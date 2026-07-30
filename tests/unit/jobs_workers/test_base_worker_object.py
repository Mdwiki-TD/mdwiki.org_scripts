"""Unit tests for BaseObjectsJobWorker and WorkerObject.

Uses real DB (TestingConfig SQLite) for JobsService calls.
Mocks only external/non-DB dependencies:
- save_job_result_by_name (filesystem)
- get_user_site (external MediaWiki API)
- is_job_cancelled_file_exist (filesystem)
"""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest
from flask import Flask

from src.main_app.db.services import JobsService
from src.main_app.jobs_workers.base_worker import (
    BaseObjectsJobWorker,
    WorkerObject,
)


class MockWorker(BaseObjectsJobWorker):
    def get_job_type(self) -> str:
        return "mock_job"

    def process(self) -> WorkerObject:
        return self.result


JOB_ID = 123
JOB_TYPE = "mock_job"


def _seed_job(app: Flask, job_id: int = JOB_ID, job_type: str = JOB_TYPE, status: str = "pending") -> None:
    """Insert a job record with a specific ID into the real DB.

    We insert directly (rather than via JobsService.create_job) so the
    auto-increment ID matches the worker's ``job_id``.
    """
    from src.main_app.db.models import JobRecord
    from src.main_app.extensions import db

    with app.app_context():
        is_running = 1 if status in ("pending", "running") else None
        record = JobRecord(
            id=job_id,
            job_type=job_type,
            username="testuser",
            status=status,
            is_running=is_running,
        )
        db.session.add(record)
        db.session.commit()


@pytest.fixture
def mock_base_is_cancelled(monkeypatch: pytest.MonkeyPatch):
    """Mock filesystem-based cancellation check."""
    mock = MagicMock(return_value=False)
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.is_job_cancelled_file_exist",
        mock,
    )
    return mock


@pytest.fixture
def worker():
    user = {"username": "testuser"}
    worker = MockWorker(job_id=JOB_ID, user=user)
    worker.result = WorkerObject()
    return worker


def test_worker_object_to_json():
    obj = WorkerObject(status="running", error="some error")
    data = obj.to_json()
    assert data["status"] == "running"
    assert data["error"] == "some error"


@pytest.mark.usefixtures("mock_app")
class TestBaseObjectsJobWorker:
    def test_before_run_success(self, mock_app, worker, mock_base_worker):
        _seed_job(mock_app)
        assert worker.before_run() is True

        # Verify real DB was updated to "running"
        with mock_app.app_context():
            job = JobsService().get_job(JOB_ID, JOB_TYPE)
            assert job.status == "running"
        assert worker.result.status == "running"

    def test_before_run_lookup_error(self, mock_app, worker, mock_base_worker):
        """No job seeded → get_job raises LookupError → before_run returns False."""
        assert worker.before_run() is False

    def test_after_run_success(self, mock_app, worker, mock_base_worker):
        _seed_job(mock_app, status="running")
        worker.result.status = "running"

        worker.after_run()

        assert worker.result.status == "completed"
        assert worker.result.completed_at is not None

        with mock_app.app_context():
            job = JobsService().get_job(JOB_ID, JOB_TYPE)
            assert job.status == "completed"

    def test_after_run_db_error(self, mock_app, worker, mock_base_worker, monkeypatch: pytest.MonkeyPatch):
        """When update_job_status_with_retry raises, after_run should not crash."""
        _seed_job(mock_app, status="running")

        def raise_error(*args, **kwargs):
            raise Exception("DB Fail")

        monkeypatch.setattr(
            "src.main_app.jobs_workers.base_worker.JobsService.update_job_status_with_retry",
            raise_error,
        )
        worker.after_run()  # Should handle exception and log it

    def test_is_cancelled_event(self, worker):
        worker.cancel_event = threading.Event()
        worker.cancel_event.set()
        assert worker.is_cancelled() is True
        assert worker.result.status == "cancelled"

    def test_is_cancelled_file(self, mock_app, worker, mock_base_worker, mock_base_is_cancelled):
        _seed_job(mock_app)
        mock_base_is_cancelled.return_value = True
        assert worker.is_cancelled() is True
        assert worker.result.status == "cancelled"

    def test_is_cancelled_db(self, mock_app, worker, mock_base_worker, mock_base_is_cancelled):
        _seed_job(mock_app, status="cancelled")
        assert worker.is_cancelled(check_db=True) is True
        assert worker.result.status == "cancelled"

    def test_check_cancel_db_periodic(self, mock_app, worker, mock_base_worker, mock_base_is_cancelled):
        _seed_job(mock_app, status="cancelled")
        # Interval is 10
        for _ in range(9):
            assert worker.check_cancel_db_periodic(interval=10) is False
        assert worker.check_cancel_db_periodic(interval=10) is True

    def test_get_priority(self, worker):
        assert worker.get_priority(5) == 1
        assert worker.get_priority(100) == 10

    def test_handle_error(self, worker):
        worker.handle_error(ValueError("Test error"), context="Some context")
        assert worker.result.status == "failed"
        assert worker.result.failed_at is not None
        assert worker.result.errors[0]["error"] == "Test error"
        assert worker.result.errors[0]["error_type"] == "ValueError"

    def test_log_no_site_error(self, worker):
        worker.log_no_site_error()
        assert worker.result.status == "failed"
        assert "No authenticated user site available" in worker.result.errors[0]["error"]

    def test_run_success(self, mock_app, worker, mock_base_worker):
        _seed_job(mock_app)
        result = worker.run()
        assert result["status"] == "completed"

        with mock_app.app_context():
            job = JobsService().get_job(JOB_ID, JOB_TYPE)
            assert job.status == "completed"

    def test_run_before_fail(self, mock_app, worker, mock_base_worker):
        """No job seeded → before_run fails → status stays pending."""
        result = worker.run()
        assert result["status"] == "pending"

    def test_run_exception(self, mock_app, worker, mock_base_worker, monkeypatch: pytest.MonkeyPatch):
        _seed_job(mock_app)

        def raise_error(*args, **kwargs):
            raise Exception("Process failed")

        monkeypatch.setattr(MockWorker, "process", raise_error)
        result = worker.run()
        assert result["status"] == "failed"
        assert result["errors"][0]["error"] == "Process failed"
