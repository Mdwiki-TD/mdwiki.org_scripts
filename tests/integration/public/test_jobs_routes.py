"""Integration tests for the /jobs/ blueprint endpoints.

Tests the full job lifecycle through the Flask test client with a real
SQLite database (via TestingConfig). Background worker execution is
stubbed to avoid network access and thread complexity.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from flask.app import Flask

from src.main_app.db.services import (
    create_job,
    get_job,
    list_jobs,
    upsert_user_token,
)
from src.main_app.db.services.admin_service import add_coordinator
from src.main_app.db.services.users_service import create_user


@pytest.fixture
def _unwrap_delete_job(mock_app: Flask):
    """Bypass @admin_required on delete_job by unwrapping the view function.

    The ``@admin_required`` decorator is applied at module-import time
    (when the blueprint is created), so it cannot be mocked per-test
    through the normal patch / monkeypatch machinery.  This fixture
    walks the ``__wrapped__`` chain of the already-wrapped view function
    stored in the app's view-functions registry and replaces it with the
    original (unwrapped) handler, then restores it after the test.
    """
    endpoint = "public_jobs.delete_job"
    original = mock_app.view_functions.get(endpoint)
    if original is not None:
        unwrapped = original
        while hasattr(unwrapped, "__wrapped__"):
            unwrapped = unwrapped.__wrapped__
        mock_app.view_functions[endpoint] = unwrapped
    yield
    if original is not None:
        mock_app.view_functions[endpoint] = original


VALID_JOB_TYPE = "fixref"
ANOTHER_VALID_JOB_TYPE = "create_redirects"


@pytest.fixture(autouse=True)
def _clean_db(mock_app: Flask):
    """Clean all tables after each test to prevent state leaking."""
    yield
    with mock_app.app_context():
        from src.main_app.extensions import db

        meta = db.metadata
        with db.engine.begin() as conn:
            for table in reversed(meta.sorted_tables):
                conn.execute(table.delete())


def _seed_user(mock_app, username="JobUser", *, can_run_bg_jobs=False) -> int:
    """Create a user token record for job ownership. Returns the auto-generated user_id."""
    with mock_app.app_context():
        user = create_user(username)
        if can_run_bg_jobs:
            from src.main_app.db.services.users_service import toggle_can_run_bg_jobs

            toggle_can_run_bg_jobs(user.user_id, True)
        upsert_user_token(
            user_id=user.user_id,
            access_key="k",
            access_secret="s",
        )
        return user.user_id


def _login_user(mock_client, user_id, username="JobUser"):
    """Set session to a specific user."""
    with mock_client.session_transaction() as sess:
        sess["uid"] = user_id
        sess["username"] = username


def _seed_job(mock_app, job_type=VALID_JOB_TYPE, username="JobUser"):
    """Create a job record and return its ID."""
    with mock_app.app_context():
        job = create_job(job_type, username)
        return job.id


@pytest.mark.usefixtures("mock_app")
class TestAllJobsList:
    """GET /jobs/list — public listing of all jobs."""

    def test_all_jobs_list_loads(self, mock_client):
        """The all-jobs page should load successfully."""
        resp = mock_client.get("/jobs/list")
        assert resp.status_code == 200

    def test_all_jobs_list_empty(self, mock_client):
        """With no jobs, the page should still render."""
        resp = mock_client.get("/jobs/list")
        assert resp.status_code == 200


@pytest.mark.usefixtures("mock_app")
class TestJobsListByType:
    """GET /jobs/<job_type> — jobs list filtered by type."""

    def test_valid_job_type_loads(self, mock_client):
        """A valid job type should return 200."""
        resp = mock_client.get(f"/jobs/{VALID_JOB_TYPE}")
        assert resp.status_code == 200

    def test_invalid_job_type_returns_404(self, mock_client):
        """An unknown job type should return 404."""
        resp = mock_client.get("/jobs/nonexistent_type")
        assert resp.status_code == 404

    def test_all_valid_job_types_load(self, mock_client):
        """Every registered job type should return 200."""
        from src.main_app.jobs_workers.public_jobs_workers.workers_list_public import jobs_data_public

        for job_type in jobs_data_public:
            resp = mock_client.get(f"/jobs/{job_type}")
            assert resp.status_code == 200, f"Job type {job_type} failed"


@pytest.mark.usefixtures("mock_app")
class TestJobDetail:
    """GET /jobs/<job_type>/<job_id> — single job detail page."""

    def test_job_detail_loads(self, mock_app, mock_client):
        """A valid job ID should load the detail page."""
        _seed_user(mock_app)
        job_id = _seed_job(mock_app, VALID_JOB_TYPE)
        resp = mock_client.get(f"/jobs/{VALID_JOB_TYPE}/{job_id}")
        assert resp.status_code == 200

    def test_job_detail_nonexistent_redirects(self, mock_app, mock_client):
        """A non-existent job should redirect to the jobs list."""
        resp = mock_client.get(f"/jobs/{VALID_JOB_TYPE}/99999")
        assert resp.status_code == 302

    def test_job_detail_wrong_type_redirects(self, mock_app, mock_client):
        """Looking up a job with the wrong type should redirect."""
        _seed_user(mock_app)
        job_id = _seed_job(mock_app, VALID_JOB_TYPE)
        resp = mock_client.get(f"/jobs/{ANOTHER_VALID_JOB_TYPE}/{job_id}")
        assert resp.status_code == 302

    def test_job_detail_invalid_type_returns_404_or_redirect(self, mock_app, mock_client):
        """An invalid job type should return 404 or redirect."""
        _seed_user(mock_app)
        job_id = _seed_job(mock_app, VALID_JOB_TYPE)
        resp = mock_client.get(f"/jobs/nonexistent/{job_id}")
        # The route may 404 or redirect depending on abort handler
        assert resp.status_code in (302, 404)


@pytest.mark.usefixtures("mock_app")
class TestStartJob:
    """POST /jobs/<job_type>/start — start a new background job."""

    def test_start_requires_login(self, mock_app, mock_client):
        """Unauthenticated user should be redirected."""
        resp = mock_client.post(f"/jobs/{VALID_JOB_TYPE}/start")
        assert resp.status_code == 302

    def test_start_invalid_job_type_404(self, mock_app, mock_client):
        """Starting a job with invalid type should return 404."""
        uid = _seed_user(mock_app)
        _login_user(mock_client, uid)
        resp = mock_client.post("/jobs/nonexistent_type/start")
        assert resp.status_code == 404

    def test_start_creates_job_and_redirects(self, mock_app, mock_client):
        """Starting a valid job should create a DB record and redirect."""
        uid = _seed_user(mock_app, can_run_bg_jobs=True)
        _login_user(mock_client, uid)

        with (
            patch(
                "src.main_app.public.jobs_routes_utils.load_auth_payload",
                return_value={"id": uid, "username": "JobUser"},
            ),
            patch(
                "src.main_app.public.jobs_routes_utils.start_job",
                return_value=1,
            ),
        ):
            resp = mock_client.post(
                f"/jobs/{VALID_JOB_TYPE}/start",
                follow_redirects=False,
            )

        assert resp.status_code == 302

    def test_start_creates_job(self, mock_app, mock_client):
        """Starting a job with args should succeed."""
        uid = _seed_user(mock_app, can_run_bg_jobs=True)
        _login_user(mock_client, uid)

        with (
            patch(
                "src.main_app.public.jobs_routes_utils.load_auth_payload",
                return_value={"id": uid, "username": "JobUser"},
            ),
            patch(
                "src.main_app.public.jobs_routes_utils.start_job",
                return_value=1,
            ),
        ):
            resp = mock_client.post(
                f"/jobs/{VALID_JOB_TYPE}/start",
                data={"key": "value"},
                follow_redirects=False,
            )

        assert resp.status_code == 302

    def test_start_duplicate_job_flashes_warning(self, mock_app, mock_client):
        """Starting a duplicate job should flash a warning and redirect."""
        from src.main_app.db.exceptions import DuplicateJobError

        uid = _seed_user(mock_app, can_run_bg_jobs=True)
        _login_user(mock_client, uid)

        with (
            patch(
                "src.main_app.public.jobs_routes_utils.load_auth_payload",
                return_value={"id": uid, "username": "JobUser"},
            ),
            patch(
                "src.main_app.public.jobs_routes_utils.start_job",
                side_effect=DuplicateJobError("A job of type 'fixref' is already active"),
            ),
        ):
            resp = mock_client.post(
                f"/jobs/{VALID_JOB_TYPE}/start",
                follow_redirects=True,
            )

        assert b"A job of this type is already running" in resp.data


@pytest.mark.usefixtures("mock_app")
class TestCancelJob:
    """POST /jobs/<job_type>/<job_id>/cancel — cancel a running job."""

    def test_cancel_requires_login(self, mock_app, mock_client):
        """Unauthenticated user should be redirected."""
        _seed_user(mock_app)
        job_id = _seed_job(mock_app, VALID_JOB_TYPE)
        resp = mock_client.post(f"/jobs/{VALID_JOB_TYPE}/{job_id}/cancel")
        assert resp.status_code == 302

    def test_cancel_invalid_job_type_404(self, mock_app, mock_client):
        """Cancelling with invalid job type should return 404."""
        uid = _seed_user(mock_app)
        _login_user(mock_client, uid)
        job_id = _seed_job(mock_app, VALID_JOB_TYPE)
        resp = mock_client.post(f"/jobs/nonexistent/{job_id}/cancel")
        assert resp.status_code == 404

    def test_cancel_nonexistent_job_redirects(self, mock_app, mock_client):
        """Cancelling a non-existent job should redirect."""
        uid = _seed_user(mock_app)
        _login_user(mock_client, uid)
        resp = mock_client.post(
            f"/jobs/{VALID_JOB_TYPE}/99999/cancel",
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_cancel_own_job(self, mock_app, mock_client):
        """Job owner should be able to cancel their own job."""
        owner_uid = _seed_user(mock_app, username="Owner")
        _login_user(mock_client, owner_uid, username="Owner")
        job_id = _seed_job(mock_app, VALID_JOB_TYPE, username="Owner")

        with patch(
            "src.main_app.public.jobs_routes_utils.cancel_job_worker",
            return_value=True,
        ):
            resp = mock_client.post(
                f"/jobs/{VALID_JOB_TYPE}/{job_id}/cancel",
                follow_redirects=True,
            )

        assert resp.status_code == 200

    def test_cancel_other_user_job_blocked(self, mock_app, mock_client, monkeypatch):
        """Non-owner, non-admin should not be able to cancel another user's job."""
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", mock_flash)

        _seed_user(mock_app, username="Owner")
        other_uid = _seed_user(mock_app, username="Other")
        job_id = _seed_job(mock_app, VALID_JOB_TYPE, username="Owner")
        _login_user(mock_client, other_uid, username="Other")

        resp = mock_client.post(
            f"/jobs/{VALID_JOB_TYPE}/{job_id}/cancel",
            follow_redirects=True,
        )
        assert resp.status_code == 200
        mock_flash.assert_called_once_with("You don't have permission to cancel this job.", "danger")

    def test_admin_can_cancel_any_job(self, mock_app, mock_client):
        """An admin (coordinator) should be able to cancel any job."""
        _seed_user(mock_app, username="Owner")
        admin_uid = _seed_user(mock_app, username="AdminCancel")
        with mock_app.app_context():
            add_coordinator("AdminCancel")

        job_id = _seed_job(mock_app, VALID_JOB_TYPE, username="Owner")
        _login_user(mock_client, admin_uid, username="AdminCancel")

        with patch(
            "src.main_app.public.jobs_routes_utils.cancel_job_worker",
            return_value=True,
        ):
            resp = mock_client.post(
                f"/jobs/{VALID_JOB_TYPE}/{job_id}/cancel",
                follow_redirects=True,
            )

        assert resp.status_code == 200


@pytest.mark.usefixtures("mock_app", "_unwrap_delete_job")
class TestDeleteJob:
    """POST /jobs/<job_type>/<job_id>/delete — delete a job."""

    def test_delete_invalid_job_type_404(self, mock_app, mock_client):
        """Deleting with invalid job type should return 404."""
        uid = _seed_user(mock_app)
        _login_user(mock_client, uid)
        resp = mock_client.post("/jobs/nonexistent/1/delete")
        assert resp.status_code == 404

    def test_delete_own_job(self, mock_app, mock_client):
        """Job owner should be able to delete their own job."""
        owner_uid = _seed_user(mock_app, username="Owner")
        _login_user(mock_client, owner_uid, username="Owner")
        job_id = _seed_job(mock_app, VALID_JOB_TYPE, username="Owner")

        with patch(
            "src.main_app.public.jobs_routes_utils.cancel_job_worker",
            return_value=False,
        ):
            resp = mock_client.post(
                f"/jobs/{VALID_JOB_TYPE}/{job_id}/delete",
                follow_redirects=True,
            )

        assert resp.status_code == 200

        with mock_app.app_context():
            with pytest.raises(LookupError):
                get_job(job_id, VALID_JOB_TYPE)

    def test_delete_nonexistent_job(self, mock_app, mock_client):
        """Deleting a non-existent job should not error."""
        uid = _seed_user(mock_app)
        _login_user(mock_client, uid)

        with patch(
            "src.main_app.public.jobs_routes_utils.cancel_job_worker",
            return_value=False,
        ):
            resp = mock_client.post(
                f"/jobs/{VALID_JOB_TYPE}/99999/delete",
                follow_redirects=True,
            )

        assert resp.status_code == 200


@pytest.mark.usefixtures("mock_app")
class TestJobsRouteIntegration:
    """End-to-end integration scenarios for job routes."""

    def test_job_lifecycle_through_routes(self, mock_app, mock_client):
        """Full lifecycle: create -> view detail -> cancel."""
        uid = _seed_user(mock_app, username="LifecycleUser")
        _login_user(mock_client, uid, username="LifecycleUser")

        # Create job in DB
        with mock_app.app_context():
            job = create_job(VALID_JOB_TYPE, "LifecycleUser")
            job_id = job.id

        # View detail
        resp = mock_client.get(f"/jobs/{VALID_JOB_TYPE}/{job_id}")
        assert resp.status_code == 200

        # Cancel (no mock — let the real cancel_job_db update the DB)
        resp = mock_client.post(
            f"/jobs/{VALID_JOB_TYPE}/{job_id}/cancel",
            follow_redirects=True,
        )

        assert resp.status_code == 200

        # Verify cancelled in DB
        with mock_app.app_context():
            from src.main_app.db.services import is_job_cancelled

            assert is_job_cancelled(job_id, VALID_JOB_TYPE) is True

    def test_multiple_jobs_listed_by_type(self, mock_app, mock_client):
        """Multiple jobs of the same type should all appear in the list."""
        from src.main_app.db.services import update_job_status

        _seed_user(mock_app)
        with mock_app.app_context():
            job1 = create_job(VALID_JOB_TYPE, "JobUser")
            update_job_status(job1.id, "running", job_type=VALID_JOB_TYPE)
            update_job_status(job1.id, "completed", job_type=VALID_JOB_TYPE)
            create_job(VALID_JOB_TYPE, "JobUser")
            create_job(ANOTHER_VALID_JOB_TYPE, "JobUser")

        with mock_app.app_context():
            fixref_jobs = list_jobs(limit=100, job_type=VALID_JOB_TYPE)
            redirect_jobs = list_jobs(limit=100, job_type=ANOTHER_VALID_JOB_TYPE)
            all_jobs = list_jobs(limit=100)

        assert len(fixref_jobs) == 2
        assert len(redirect_jobs) == 1
        assert len(all_jobs) == 3

    @pytest.mark.usefixtures("_unwrap_delete_job")
    def test_delete_then_list_shows_remaining(self, mock_app, mock_client):
        """After deleting one job, the list should show remaining jobs."""
        from src.main_app.db.services import update_job_status

        owner_uid = _seed_user(mock_app, username="Owner")
        _login_user(mock_client, owner_uid, username="Owner")

        with mock_app.app_context():
            job1 = create_job(VALID_JOB_TYPE, "Owner")
            update_job_status(job1.id, "running", job_type=VALID_JOB_TYPE)
            update_job_status(job1.id, "completed", job_type=VALID_JOB_TYPE)
            job2 = create_job(VALID_JOB_TYPE, "Owner")
            job1_id = job1.id
            job2_id = job2.id

        with patch(
            "src.main_app.public.jobs_routes_utils.cancel_job_worker",
            return_value=False,
        ):
            mock_client.post(
                f"/jobs/{VALID_JOB_TYPE}/{job1_id}/delete",
                follow_redirects=True,
            )

        with mock_app.app_context():
            remaining = list_jobs(limit=100, job_type=VALID_JOB_TYPE)
            remaining_ids = [j.id for j in remaining]
            assert job1_id not in remaining_ids
            assert job2_id in remaining_ids
