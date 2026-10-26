"""Unit tests for src/main_app/jobs_workers/public_jobs_workers/owidpopup_all/worker.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers.objects import JobsRunner
from src.main_app.jobs_workers.public_jobs_workers.owidpopup_all.worker import (
    OwidPopupAllWorker,
    replace_owid_popup,
)
from src.main_app.jobs_workers.shared_objects import SharedworkerObject, UpdaterOutcome


class TestReplaceOwidPopup:
    def test_basic_transformation(self):
        before = (
            "{{OWIDPopup\n"
            "| owid = grapher/malnutrition-death-rates\n"
            "| title = Malnutrition death rates\n"
            "}}"
        )
        expected = (
            "{{OWID\n"
            "| chart = grapher/malnutrition-death-rates\n"
            "| title = Malnutrition death rates\n"
            "}}"
        )
        assert replace_owid_popup(before) == expected

    def test_case_insensitivity_and_inline(self):
        before = "{{owidpopup | OWID = grapher/test | title = Test }}"
        expected = "{{OWID | chart = grapher/test | title = Test }}"
        assert replace_owid_popup(before) == expected

    def test_other_arguments_preserved(self):
        before = "{{OWIDPopup|owid=grapher/abc|title=Title|extra=value|foo=bar}}"
        expected = "{{OWID|chart=grapher/abc|title=Title|extra=value|foo=bar}}"
        assert replace_owid_popup(before) == expected

    def test_other_templates_untouched(self):
        before = "{{OtherTemplate | owid = 123 | title = Test}}"
        assert replace_owid_popup(before) == before

    def test_multiple_templates_and_nested(self):
        before = (
            "Leading text\n"
            "{{OWIDPopup | owid = grapher/chart-1 | title = Chart 1}}\n"
            "Middle text\n"
            "{{Wrapper | inner = {{OWIDPopup | owid = grapher/chart-2 | title = Chart 2}} }}\n"
            "Trailing text"
        )
        expected = (
            "Leading text\n"
            "{{OWID | chart = grapher/chart-1 | title = Chart 1}}\n"
            "Middle text\n"
            "{{Wrapper | inner = {{OWID | chart = grapher/chart-2 | title = Chart 2}} }}\n"
            "Trailing text"
        )
        assert replace_owid_popup(before) == expected

    def test_no_templates_returns_same_text(self):
        text = "This is plain text with no templates."
        assert replace_owid_popup(text) == text


class TestOwidPopupAllWorker:
    def test_get_job_type(self):
        worker = OwidPopupAllWorker(JobsRunner(job_id=1, args={}, user=None))
        assert worker.get_job_type() == "owidpopup_all"

    def test_result_type(self):
        worker = OwidPopupAllWorker(JobsRunner(job_id=1, args={}, user=None))
        assert isinstance(worker.result, SharedworkerObject)

    @pytest.fixture
    def mock_site(self):
        site = MagicMock()
        return site

    def test_default_category(self, mock_site):
        worker = OwidPopupAllWorker(JobsRunner(job_id=1, args={}, user=None))
        worker.site = mock_site

        with patch.object(worker, "_check_site", return_value=True), patch(
            "src.main_app.jobs_workers.public_jobs_workers.owidpopup_all.worker.get_category_members",
            return_value=[],
        ) as mock_get_cat:
            worker.process()
            mock_get_cat.assert_called_once_with(
                site=mock_site,
                category_title="Category:Gadget:OWIDPopup",
                namespace=0,
            )

    def test_custom_category(self, mock_site):
        worker = OwidPopupAllWorker(
            JobsRunner(job_id=1, args={"cat": "Gadget:OWIDPopup"}, user=None)
        )
        worker.site = mock_site

        with patch.object(worker, "_check_site", return_value=True), patch(
            "src.main_app.jobs_workers.public_jobs_workers.owidpopup_all.worker.get_category_members",
            return_value=[],
        ) as mock_get_cat:
            worker.process()
            mock_get_cat.assert_called_once_with(
                site=mock_site,
                category_title="Category:Gadget:OWIDPopup",
                namespace=0,
            )

    def test_process_page_missing(self, mock_site):
        worker = OwidPopupAllWorker(JobsRunner(job_id=1, args={}, user=None))
        worker.site = mock_site

        mock_page = MagicMock()
        mock_page.exists.return_value = False

        with patch(
            "src.main_app.jobs_workers.public_jobs_workers.owidpopup_all.worker.MwClientPage",
            return_value=mock_page,
        ):
            info = UpdaterOutcome(title="Page 1")
            worker._process_one(info)

            assert info.status == "missing"
            assert info.msg == "Page is missing"

    def test_process_page_empty(self, mock_site):
        worker = OwidPopupAllWorker(JobsRunner(job_id=1, args={}, user=None))
        worker.site = mock_site

        mock_page = MagicMock()
        mock_page.exists.return_value = True
        mock_page.get_text.return_value = "   "

        with patch(
            "src.main_app.jobs_workers.public_jobs_workers.owidpopup_all.worker.MwClientPage",
            return_value=mock_page,
        ):
            info = UpdaterOutcome(title="Page 1")
            worker._process_one(info)

            assert info.status == "skipped"
            assert info.msg == "Page is empty"

    def test_process_page_no_changes(self, mock_site):
        worker = OwidPopupAllWorker(JobsRunner(job_id=1, args={}, user=None))
        worker.site = mock_site

        mock_page = MagicMock()
        mock_page.exists.return_value = True
        mock_page.get_text.return_value = "No OWIDPopup here"

        with patch(
            "src.main_app.jobs_workers.public_jobs_workers.owidpopup_all.worker.MwClientPage",
            return_value=mock_page,
        ):
            info = UpdaterOutcome(title="Page 1")
            worker._process_one(info)

            assert info.status == "skipped"
            assert info.msg == "No changes"

    def test_process_page_success(self, mock_site):
        worker = OwidPopupAllWorker(JobsRunner(job_id=1, args={}, user=None))
        worker.site = mock_site

        mock_page = MagicMock()
        mock_page.exists.return_value = True
        mock_page.get_text.return_value = (
            "{{OWIDPopup | owid = grapher/test | title = Test}}"
        )
        mock_page.edit.return_value = {"success": True, "newrevid": 12345}

        with patch(
            "src.main_app.jobs_workers.public_jobs_workers.owidpopup_all.worker.MwClientPage",
            return_value=mock_page,
        ):
            info = UpdaterOutcome(title="Page 1")
            worker._process_one(info)

            assert info.status == "changed"
            assert info.newrevid == 12345
            mock_page.edit.assert_called_once_with(
                "{{OWID | chart = grapher/test | title = Test}}",
                "Replace OWIDPopup with OWID",
            )

    def test_process_page_edit_exception(self, mock_site):
        worker = OwidPopupAllWorker(JobsRunner(job_id=1, args={}, user=None))
        worker.site = mock_site

        mock_page = MagicMock()
        mock_page.exists.return_value = True
        mock_page.get_text.return_value = (
            "{{OWIDPopup | owid = grapher/test | title = Test}}"
        )
        mock_page.edit.side_effect = Exception("API write error")

        with patch(
            "src.main_app.jobs_workers.public_jobs_workers.owidpopup_all.worker.MwClientPage",
            return_value=mock_page,
        ):
            info = UpdaterOutcome(title="Page 1")
            worker._process_one(info)

            assert info.status == "failed"
            assert "API write error" in info.msg

    def test_process_full_job_with_cancellation(self, mock_site):
        worker = OwidPopupAllWorker(JobsRunner(job_id=1, args={}, user=None))
        worker.site = mock_site

        with patch.object(worker, "_check_site", return_value=True), patch(
            "src.main_app.jobs_workers.public_jobs_workers.owidpopup_all.worker.get_category_members",
            return_value=["Page1", "Page2"],
        ), patch.object(worker, "is_cancelled", side_effect=[False, True]), patch.object(
            worker, "_process_one"
        ) as mock_proc:
            worker.process()
            assert mock_proc.call_count == 1
            assert worker.result.status == "completed"
