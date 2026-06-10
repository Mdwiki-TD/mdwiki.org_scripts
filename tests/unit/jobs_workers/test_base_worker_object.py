"""Unit tests for src/main_app/jobs_workers/base_worker_object.py."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest
from src.main_app.jobs_workers.base_worker_object import (
    BaseObjectsJobWorker,
    WorkerObject,
)


class MockWorker(BaseObjectsJobWorker):
    def get_job_type(self) -> str:
        return "mock_job"

    def process(self) -> WorkerObject:
        return self.result


class TestBaseObjectsJobWorker:
    @pytest.fixture
    def worker(self):
        worker = MockWorker(job_id=1, user={"username": "test"}, cancel_event=threading.Event())
        worker.result = WorkerObject()
        return worker

    @patch("src.main_app.jobs_workers.base_worker_object.update_job_status")
    @patch("src.main_app.jobs_workers.base_worker_object.save_job_result_by_name")
    def test_before_run(self, mock_save, mock_update, worker):
        assert worker.before_run() is True
        mock_update.assert_called_once_with(1, "running", worker.result_file, job_type="mock_job")
        assert worker.result.status == "running"
        mock_save.assert_called_once()

    @patch("src.main_app.jobs_workers.base_worker_object.update_job_status")
    @patch("src.main_app.jobs_workers.base_worker_object.save_job_result_by_name")
    def test_after_run(self, mock_save, mock_update, worker):
        worker.result.status = "running"
        worker.after_run()
        assert worker.result.status == "completed"
        assert worker.result.completed_at is not None
        mock_update.assert_called_once_with(1, "completed", worker.result_file, job_type="mock_job")

    @patch("src.main_app.jobs_workers.base_worker_object.is_job_cancelled_file_exist")
    def test_is_cancelled_local(self, mock_file_exists, worker):
        mock_file_exists.return_value = False
        assert worker.is_cancelled() is False

        worker.cancel_event.set()
        assert worker.is_cancelled() is True
        assert worker.result.status == "cancelled"

    @patch("src.main_app.jobs_workers.base_worker_object.is_job_cancelled")
    @patch("src.main_app.jobs_workers.base_worker_object.is_job_cancelled_file_exist")
    def test_is_cancelled_db(self, mock_file_exists, mock_db_cancelled, worker):
        mock_file_exists.return_value = False
        mock_db_cancelled.return_value = True
        assert worker.is_cancelled(check_db=True) is True
        assert worker.result.status == "cancelled"

    def test_handle_error(self, worker):
        error = ValueError("test error")
        worker.handle_error(error, context="doing something")
        assert worker.result.status == "failed"
        assert worker.result.failed_at is not None
        assert len(worker.result.errors) == 1
        assert worker.result.errors[0]["error"] == "test error"

    @patch("src.main_app.jobs_workers.base_worker_object.update_job_status")
    @patch("src.main_app.jobs_workers.base_worker_object.save_job_result_by_name")
    def test_run_success(self, mock_save, mock_update, worker):
        worker.process = MagicMock(return_value=worker.result)
        result = worker.run()
        assert result["status"] == "completed"
        worker.process.assert_called_once()

    def test_get_priority(self, worker):
        assert worker.get_priority(5) == 1
        assert worker.get_priority(100) == 10
