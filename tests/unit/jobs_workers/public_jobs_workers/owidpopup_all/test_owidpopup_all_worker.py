"""Unit tests for src/main_app/jobs_workers/public_jobs_workers/owidpopup_all/worker.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers.objects import JobsRunner
from src.main_app.jobs_workers.public_jobs_workers.owidpopup_all.mapping import (
    OWID_POPUP_RENAME,
    TemplateRename,
    _norm_template_name,
)
from src.main_app.jobs_workers.public_jobs_workers.owidpopup_all.worker import (
    OwidPopupAllWorker,
    replace_templates,
)
from src.main_app.jobs_workers.shared_objects import SharedworkerObject, UpdaterOutcome


class TestTemplateRenameConfig:
    def test_norm_template_name(self):
        assert _norm_template_name("  OWID_Popup  ") == "owid popup"

    def test_dataclass_fields_and_post_init(self):
        rename = TemplateRename(
            old_names=["OldName", "Old_Name"],
            new_name="NewName",
            arguments={"oldarg": "newarg"},
        )
        assert rename.old_names == ["OldName", "Old_Name"]
        assert rename.new_name == "NewName"
        assert rename.arguments == {"oldarg": "newarg"}
        assert rename._old_names_norm == frozenset({"oldname", "old name"})
        assert rename._args_map == {"oldarg": "newarg"}

    def test_owid_popup_rename_config(self):
        assert OWID_POPUP_RENAME.old_names == ["OWIDPopup", "OWID_popup"]
        assert OWID_POPUP_RENAME.new_name == "OWID"
        assert OWID_POPUP_RENAME.arguments == {"owid": "chart"}
        assert OWID_POPUP_RENAME._old_names_norm == frozenset({"owidpopup", "owid popup"})


class TestReplaceTemplates:
    def test_basic_transformation(self):
        before = (
            "{{OWIDPopup\n"
            "| owid = grapher/malnutrition-death-rates\n"
            "| title = Malnutrition death rates\n"
            "}}"
        )
        expected = (
            "{{OWID|chart= grapher/malnutrition-death-rates\n"
            "| title = Malnutrition death rates\n"
            "}}"
        )
        assert replace_templates(before, [OWID_POPUP_RENAME]) == expected

    def test_underscore_template_name(self):
        before = "{{OWID_popup | owid = grapher/test | title = Test }}"
        expected = "{{OWID|chart= grapher/test | title = Test }}"
        assert replace_templates(before, [OWID_POPUP_RENAME]) == expected

    def test_case_insensitivity_and_inline(self):
        before = "{{owidpopup | OWID = grapher/test | title = Test }}"
        expected = "{{OWID|chart= grapher/test | title = Test }}"
        assert replace_templates(before, [OWID_POPUP_RENAME]) == expected

    def test_other_arguments_preserved(self):
        before = "{{OWIDPopup|owid=grapher/abc|title=Title|extra=value|foo=bar}}"
        expected = "{{OWID|chart=grapher/abc|title=Title|extra=value|foo=bar}}"
        assert replace_templates(before, [OWID_POPUP_RENAME]) == expected

    def test_other_templates_untouched(self):
        before = "{{OtherTemplate | owid = 123 | title = Test}}"
        assert replace_templates(before, [OWID_POPUP_RENAME]) == before

    def test_multiple_templates_and_nested(self):
        before = (
            "Leading text\n"
            "{{OWIDPopup | owid = grapher/chart-1 | title = Chart 1}}\n"
            "Middle text\n"
            "{{Wrapper | inner = {{OWID_popup | owid = grapher/chart-2 | title = Chart 2}} }}\n"
            "Trailing text"
        )
        expected = (
            "Leading text\n"
            "{{OWID|chart= grapher/chart-1 | title = Chart 1}}\n"
            "Middle text\n"
            "{{Wrapper | inner = {{OWID|chart= grapher/chart-2 | title = Chart 2}} }}\n"
            "Trailing text"
        )
        assert replace_templates(before, [OWID_POPUP_RENAME]) == expected

    def test_no_templates_returns_same_text(self):
        text = "This is plain text with no templates."
        assert replace_templates(text, [OWID_POPUP_RENAME]) == text

    def test_idempotency(self):
        before = "{{OWIDPopup | owid = grapher/test | title = Test }}"
        first_pass = replace_templates(before, [OWID_POPUP_RENAME])
        second_pass = replace_templates(first_pass, [OWID_POPUP_RENAME])
        assert first_pass == second_pass

    def test_generic_multi_argument_config(self):
        custom_rename = TemplateRename(
            old_names=["OldTemplate", "Old_Template"],
            new_name="NewTemplate",
            arguments={"oldarg": "newarg", "legacy": "current"},
        )
        before = "{{Old_Template | oldarg = val1 | legacy = val2 | stay = val3}}"
        expected = "{{NewTemplate|newarg= val1 |current= val2 | stay = val3}}"
        assert replace_templates(before, [custom_rename]) == expected


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
            JobsRunner(job_id=1, args={"category": "Gadget:OWIDPopup"}, user=None)
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
                "{{OWID|chart= grapher/test | title = Test}}",
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
