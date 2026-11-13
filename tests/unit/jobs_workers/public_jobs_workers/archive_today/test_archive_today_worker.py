from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.main_app.jobs_workers.objects import JobsRunner
from src.main_app.jobs_workers.public_jobs_workers.archive_today.worker import ArchiveTodayWorker
from src.main_app.jobs_workers.shared_objects import SharedworkerObject


class TestArchiveTodayWorker:
    def test_get_job_type(self):
        worker = ArchiveTodayWorker(JobsRunner(job_id=1, args={}, user=None))
        assert worker.JOB_TYPE == "archive_today"

    def test_result_type(self):
        worker = ArchiveTodayWorker(JobsRunner(job_id=1, args={}, user=None))
        assert isinstance(worker.result, SharedworkerObject)

    def test_make_new_text(self):
        worker = ArchiveTodayWorker(JobsRunner(job_id=1, args={}, user=None))
        text = (
            "{{cite web |title=Foo |url=http://example.com |archive-url=https://archive.is/123 |archive-date=2020}} "
            "{{webarchive |url=https://archive.today/456 |date=2021}}"
        )
        new_text, summary = worker._make_new_text("Test Title", text)
        assert "archive-url" not in new_text
        assert "webarchive" not in new_text
        assert summary == "Remove archive.today links"

    def test_process_no_site(self):
        worker = ArchiveTodayWorker(JobsRunner(job_id=1, args={}, user=None))
        with patch.object(worker, "_check_site", return_value=False):
            res = worker.process()
            assert res.status in ("pending", "running")

    def test_process_pages(self):
        worker = ArchiveTodayWorker(JobsRunner(job_id=1, args={}, user=None))
        mock_site = MagicMock()
        worker.site = mock_site

        mock_page1 = MagicMock()
        mock_page1.name = "Page1"

        mock_page2 = MagicMock()
        mock_page2.name = "Page2"

        mock_site.allpages.return_value = [mock_page1, mock_page2]

        with (
            patch.object(worker, "_check_site", return_value=True),
            patch.object(worker, "_process_one") as mock_process_one,
            patch.object(worker, "save_progress") as mock_save,
        ):

            def side_effect(info):
                info.status = "updated"

            mock_process_one.side_effect = side_effect

            res = worker.process()
            assert res.status == "completed"
            assert res.summary.total == 2
            assert res.summary.processed == 2
            assert len(res.pages_updated) == 2
            assert mock_process_one.call_count == 2
