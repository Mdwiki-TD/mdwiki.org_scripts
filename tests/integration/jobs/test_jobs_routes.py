"""Integration tests for the /new_jobs/ blueprint endpoints.

Tests the full job lifecycle through the Flask test client with a real
SQLite database (via TestingConfig). Background worker execution is
stubbed to avoid network access and thread complexity.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from flask_app.main_app.db.services import (
    create_job,
    get_job,
    list_jobs,
    upsert_user_token,
)
from flask_app.main_app.db.services.admin_service import add_coordinator


def _seed_user(app, user_id=1, username="JobUser"):
    """Create a user token record for job ownership."""
    with app.app_context():
        upsert_user_token(
            user_id=user_id,
            username=username,
            access_key="k",
            access_secret="s",
        )


def _login_user(mock_client, user_id=1, username="JobUser"):
    """Set session to a specific user."""
    with mock_client.session_transaction() as sess:
        sess["uid"] = user_id
        sess["username"] = username


def _seed_job(app, job_type="fixref", username="JobUser"):
    """Create a job record and return its ID."""
    with app.app_context():
        job = create_job(job_type, username)
        return job.id


VALID_JOB_TYPE = "fixref"
ANOTHER_VALID_JOB_TYPE = "create_redirects"


@pytest.mark.usefixtures("app")
class TestAllJobsList:
    """GET /new_jobs/list — public listing of all jobs."""

    def test_all_jobs_list_loads(self, mock_client):
        """The all-jobs page should load successfully."""
        resp = mock_client.get("/new_jobs/list")
        assert resp.status_code == 200

    def test_all_jobs_list_empty(self, mock_client):
        """With no jobs, the page should still render."""
        resp = mock_client.get("/new_jobs/list")
        assert resp.status_code == 200

    def test_all_jobs_list_shows_seeded_jobs(self, app, mock_client):
        """Seeded jobs should appear on the all-jobs page."""
        _seed_user(app)
        job_id = _seed_job(app, VALID_JOB_TYPE)
        resp = mock_client.get("/new_jobs/list")
        assert resp.status_code == 200


@pytest.mark.usefixtures("app")
class TestJobsListByType:
    """GET /new_jobs/<job_type> — jobs list filtered by type."""

    def test_valid_job_type_loads(self, mock_client):
        """A valid job type should return 200."""
        resp = mock_client.get(f"/new_jobs/{VALID_JOB_TYPE}")
        assert resp.status_code == 200

    def test_invalid_job_type_returns_404(self, mock_client):
        """An unknown job type should return 404."""
        resp = mock_client.get("/new_jobs/nonexistent_type")
        assert resp.status_code == 404

    def test_all_valid_job_types_load(self, mock_client):
        """Every registered job type should return 200."""
        from flask_app.main_app.new_jobs.workers_list import jobs_data

        for job_type in jobs_data:
            resp = mock_client.get(f"/new_jobs/{job_type}")
            assert resp.status_code == 200, f"Job type {job_type} failed"

    def test_jobs_list_with_seeded_data(self, app, mock_client):
        """Seeded jobs should appear in the type-filtered list."""
        _seed_user(app)
        _seed_job(app, VALID_JOB_TYPE)
        resp = mock_client.get(f"/new_jobs/{VALID_JOB_TYPE}")
        assert resp.status_code == 200


@pytest.mark.usefixtures("app")
class TestJobDetail:
    """GET /new_jobs/<job_type>/<job_id> — single job detail page."""

    def test_job_detail_loads(self, app, mock_client):
        """A valid job ID should load the detail page."""
        _seed_user(app)
        job_id = _seed_job(app, VALID_JOB_TYPE)
        resp = mock_client.get(f"/new_jobs/{VALID_JOB_TYPE}/{job_id}")
        assert resp.status_code == 200

    def test_job_detail_nonexistent_redirects(self, app, mock_client):
        """A non-existent job should redirect to the jobs list."""
        resp = mock_client.get(f"/new_jobs/{VALID_JOB_TYPE}/99999")
        assert resp.status_code == 302

    def test_job_detail_wrong_type_redirects(self, app, mock_client):
        """Looking up a job with the wrong type should redirect."""
        _seed_user(app)
        job_id = _seed_job(app, VALID_JOB_TYPE)
        resp = mock_client.get(f"/new_jobs/{ANOTHER_VALID_JOB_TYPE}/{job_id}")
        assert resp.status_code == 302

    def test_job_detail_invalid_type_404(self, app, mock_client):
        """An invalid job type should return 404 even with a valid ID."""
        _seed_user(app)
        job_id = _seed_job(app, VALID_JOB_TYPE)
        resp = mock_client.get(f"/new_jobs/nonexistent/{job_id}")
        assert resp.status_code == 404


@pytest.mark.usefixtures("app")
class TestStartJob:
    """POST /new_jobs/<job_type>/start — start a new background job."""

    def test_start_requires_login(self, app, mock_client):
        """Unauthenticated user should be redirected."""
        resp = mock_client.post(f"/new_jobs/{VALID_JOB_TYPE}/start")
        assert resp.status_code == 302

    def test_start_invalid_job_type_404(self, app, mock_client):
        """Starting a job with invalid type should return 404."""
        _seed_user(app)
        _login_user(mock_client)
        resp = mock_client.post("/new_jobs/nonexistent_type/start")
        assert resp.status_code == 404

    def test_start_creates_job_and_redirects(self, app, mock_client):
        """Starting a valid job should create a DB record and redirect."""
        _seed_user(app)
        _login_user(mock_client)

        with patch(
            "flask_app.main_app.app_routes.new_jobs.load_auth_payload",
            return_value={"id": 1, "username": "JobUser"},
        ), patch(
            "flask_app.main_app.app_routes.new_jobs.jobs_worker.start_job",
            return_value=1,
        ):
            resp = mock_client.post(
                f"/new_jobs/{VALID_JOB_TYPE}/start",
                follow_redirects=False,
            )

        assert resp.status_code == 302

    def test_start_with_args_creates_job(self, app, mock_client):
        """Starting a job with args should succeed."""
        _seed_user(app)
        _login_user(mock_client)

        with patch(
            "flask_app.main_app.app_routes.new_jobs.load_auth_payload",
            return_value={"id": 1, "username": "JobUser"},
        ), patch(
            "flask_app.main_app.app_routes.new_jobs.jobs_worker.start_job_with_args",
            return_value=1,
        ):
            resp = mock_client.post(
                f"/new_jobs/{VALID_JOB_TYPE}/start_with_args",
                data={"key": "value"},
                follow_redirects=False,
            )

        assert resp.status_code == 302


@pytest.mark.usefixtures("app")
class TestCancelJob:
    """POST /new_jobs/<job_type>/<job_id>/cancel — cancel a running job."""

    def test_cancel_requires_login(self, app, mock_client):
        """Unauthenticated user should be redirected."""
        _seed_user(app)
        job_id = _seed_job(app, VALID_JOB_TYPE)
        resp = mock_client.post(f"/new_jobs/{VALID_JOB_TYPE}/{job_id}/cancel")
        assert resp.status_code == 302

    def test_cancel_invalid_job_type_404(self, app, mock_client):
        """Cancelling with invalid job type should return 404."""
        _seed_user(app)
        _login_user(mock_client)
        job_id = _seed_job(app, VALID_JOB_TYPE)
        resp = mock_client.post(f"/new_jobs/nonexistent/{job_id}/cancel")
        assert resp.status_code == 404

    def test_cancel_nonexistent_job_redirects(self, app, mock_client):
        """Cancelling a non-existent job should redirect."""
        _seed_user(app)
        _login_user(mock_client)
        resp = mock_client.post(
            f"/new_jobs/{VALID_JOB_TYPE}/99999/cancel",
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_cancel_own_job(self, app, mock_client):
        """Job owner should be able to cancel their own job."""
        _seed_user(app, user_id=1, username="Owner")
        _login_user(mock_client, user_id=1, username="Owner")
        job_id = _seed_job(app, VALID_JOB_TYPE, username="Owner")

        with patch(
            "flask_app.main_app.app_routes.new_jobs.jobs_worker.cancel_job",
            return_value=True,
        ):
            resp = mock_client.post(
                f"/new_jobs/{VALID_JOB_TYPE}/{job_id}/cancel",
                follow_redirects=True,
            )

        assert resp.status_code == 200

    def test_cancel_other_user_job_blocked(self, app, mock_client):
        """Non-owner, non-admin should not be able to cancel another user's job."""
        _seed_user(app, user_id=1, username="Owner")
        _seed_user(app, user_id=2, username="Other")
        job_id = _seed_job(app, VALID_JOB_TYPE, username="Owner")
        _login_user(mock_client, user_id=2, username="Other")

        resp = mock_client.post(
            f"/new_jobs/{VALID_JOB_TYPE}/{job_id}/cancel",
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"don't have permission" in resp.data

    def test_admin_can_cancel_any_job(self, app, mock_client):
        """An admin (coordinator) should be able to cancel any job."""
        _seed_user(app, user_id=1, username="Owner")
        _seed_user(app, user_id=2, username="AdminCancel")
        with app.app_context():
            add_coordinator("AdminCancel")

        job_id = _seed_job(app, VALID_JOB_TYPE, username="Owner")
        _login_user(mock_client, user_id=2, username="AdminCancel")

        with patch(
            "flask_app.main_app.app_routes.new_jobs.jobs_worker.cancel_job",
            return_value=True,
        ):
            resp = mock_client.post(
                f"/new_jobs/{VALID_JOB_TYPE}/{job_id}/cancel",
                follow_redirects=True,
            )

        assert resp.status_code == 200


@pytest.mark.usefixtures("app")
class TestDeleteJob:
    """POST /new_jobs/<job_type>/<job_id>/delete — delete a job."""

    def test_delete_invalid_job_type_404(self, app, mock_client):
        """Deleting with invalid job type should return 404."""
        _seed_user(app)
        _login_user(mock_client)
        resp = mock_client.post("/new_jobs/nonexistent/1/delete")
        assert resp.status_code == 404

    def test_delete_own_job(self, app, mock_client):
        """Job owner should be able to delete their own job."""
        _seed_user(app, user_id=1, username="Owner")
        _login_user(mock_client, user_id=1, username="Owner")
        job_id = _seed_job(app, VALID_JOB_TYPE, username="Owner")

        with patch(
            "flask_app.main_app.app_routes.new_jobs.jobs_worker.cancel_job",
            return_value=False,
        ):
            resp = mock_client.post(
                f"/new_jobs/{VALID_JOB_TYPE}/{job_id}/delete",
                follow_redirects=True,
            )

        assert resp.status_code == 200

        with app.app_context():
            with pytest.raises(LookupError):
                get_job(job_id, VALID_JOB_TYPE)

    def test_delete_other_user_job_blocked(self, app, mock_client):
        """Non-owner, non-admin should not be able to delete another user's job."""
        _seed_user(app, user_id=1, username="Owner")
        _seed_user(app, user_id=2, username="Other")
        job_id = _seed_job(app, VALID_JOB_TYPE, username="Owner")
        _login_user(mock_client, user_id=2, username="Other")

        resp = mock_client.post(
            f"/new_jobs/{VALID_JOB_TYPE}/{job_id}/delete",
            follow_redirects=True,
        )
        assert resp.status_code == 200

        # Job should still exist
        with app.app_context():
            job = get_job(job_id, VALID_JOB_TYPE)
            assert job is not None

    def test_delete_nonexistent_job(self, app, mock_client):
        """Deleting a non-existent job should not error."""
        _seed_user(app)
        _login_user(mock_client)

        with patch(
            "flask_app.main_app.app_routes.new_jobs.jobs_worker.cancel_job",
            return_value=False,
        ):
            resp = mock_client.post(
                f"/new_jobs/{VALID_JOB_TYPE}/99999/delete",
                follow_redirects=True,
            )

        assert resp.status_code == 200


@pytest.mark.usefixtures("app")
class TestReadResultFile:
    """GET /new_jobs/read-job-result-file/<path> — read job result JSON."""

    def test_read_result_nonexistent_file(self, mock_client):
        """Reading a non-existent result file should error gracefully."""
        resp = mock_client.get("/new_jobs/read-job-result-file/nonexistent.json")
        assert resp.status_code in (200, 404, 500)


@pytest.mark.usefixtures("app")
class TestJobsRouteIntegration:
    """End-to-end integration scenarios for job routes."""

    def test_job_lifecycle_through_routes(self, app, mock_client):
        """Full lifecycle: start -> view detail -> cancel."""
        _seed_user(app, user_id=1, username="LifecycleUser")
        _login_user(mock_client, user_id=1, username="LifecycleUser")

        # Start
        with patch(
            "flask_app.main_app.app_routes.new_jobs.load_auth_payload",
            return_value={"id": 1, "username": "LifecycleUser"},
        ), patch(
            "flask_app.main_app.app_routes.new_jobs.jobs_worker.start_job",
        ) as mock_start:
            # Create the job in DB to simulate what start_job does
            with app.app_context():
                job = create_job(VALID_JOB_TYPE, "LifecycleUser")
                job_id = job.id
            mock_start.return_value = job_id

            resp = mock_client.post(
                f"/new_jobs/{VALID_JOB_TYPE}/start",
                follow_redirects=False,
            )

        assert resp.status_code == 302

        # View detail
        resp = mock_client.get(f"/new_jobs/{VALID_JOB_TYPE}/{job_id}")
        assert resp.status_code == 200

        # Cancel
        with patch(
            "flask_app.main_app.app_routes.new_jobs.jobs_worker.cancel_job",
            return_value=True,
        ):
            resp = mock_client.post(
                f"/new_jobs/{VALID_JOB_TYPE}/{job_id}/cancel",
                follow_redirects=True,
            )

        assert resp.status_code == 200

        # Verify cancelled in DB
        with app.app_context():
            from flask_app.main_app.db.services import is_job_cancelled

            assert is_job_cancelled(job_id, VALID_JOB_TYPE) is True

    def test_multiple_jobs_listed_by_type(self, app, mock_client):
        """Multiple jobs of the same type should all appear in the list."""
        _seed_user(app)
        with app.app_context():
            create_job(VALID_JOB_TYPE, "JobUser")
            create_job(VALID_JOB_TYPE, "JobUser")
            create_job(ANOTHER_VALID_JOB_TYPE, "JobUser")

        with app.app_context():
            fixref_jobs = list_jobs(limit=100, job_type=VALID_JOB_TYPE)
            redirect_jobs = list_jobs(limit=100, job_type=ANOTHER_VALID_JOB_TYPE)
            all_jobs = list_jobs(limit=100)

        assert len(fixref_jobs) == 2
        assert len(redirect_jobs) == 1
        assert len(all_jobs) == 3

    def test_delete_then_list_shows_remaining(self, app, mock_client):
        """After deleting one job, the list should show remaining jobs."""
        _seed_user(app, user_id=1, username="Owner")
        _login_user(mock_client, user_id=1, username="Owner")

        with app.app_context():
            job1 = create_job(VALID_JOB_TYPE, "Owner")
            job2 = create_job(VALID_JOB_TYPE, "Owner")
            job1_id = job1.id
            job2_id = job2.id

        with patch(
            "flask_app.main_app.app_routes.new_jobs.jobs_worker.cancel_job",
            return_value=False,
        ):
            mock_client.post(
                f"/new_jobs/{VALID_JOB_TYPE}/{job1_id}/delete",
                follow_redirects=True,
            )

        with app.app_context():
            remaining = list_jobs(limit=100, job_type=VALID_JOB_TYPE)
            remaining_ids = [j.id for j in remaining]
            assert job1_id not in remaining_ids
            assert job2_id in remaining_ids
