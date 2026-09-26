"""
Worker module for fix_cs1_params.

Migrated from
https://github.com/Mdwiki-TD/mdwiki-python-files/tree/main/src/md_core/fix_cs1/fix_cs_params

"""

from __future__ import annotations

import logging

from mwclient.client import Site

from ....api_services import MwClientPage, get_category_members
from ...base_worker import BaseObjectsJobWorker, JobsRunner
from ...shared_objects import SharedworkerObject, UpdaterOutcome
from .bot import OnePageArchive
from .bot import OnePage

logger = logging.getLogger(__name__)


class FixCs1ParamsWorker(BaseObjectsJobWorker):
    """Fix redirect links in all mdwiki pages."""

    def __init__(self, data: JobsRunner) -> None:
        self.args = data.args or {}
        self.site: Site | None = None

        super().__init__(data)

        self.result: SharedworkerObject = SharedworkerObject()

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "fix_cs1_params"

    def process(self) -> SharedworkerObject:
        if not self._check_site():
            return self.result

        titles: list[str] = get_category_members(
            site=self.site,
            category_title="Category:CS1 errors: redundant parameter",
            namespace=0,
        )

        total = len(titles)
        self.result.summary.total = total
        per_item = self.get_priority(total) if total else 1

        logger.info(f"Job {self.job_id}: Processing {total} pages")

        for i, title in enumerate(titles, start=1):
            logger.debug(f"i: {i}/{total}, page: {title}.")
            if self.is_cancelled():
                break

            info = UpdaterOutcome(title=title)
            self._process_one(info)

            self.update_status(info)

            if info.status == "changed" and self.check_cancel_db_periodic():
                break

            if i == 1 or i % per_item == 0:
                self._save_progress()

        if self.result.status in ("pending", "running"):
            self.result.status = "completed"

        return self.result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_one(self, info: UpdaterOutcome) -> UpdaterOutcome:
        title = info.title

        page = MwClientPage(title, self.site)
        if not page.exists():
            logger.info(f"Job {self.job_id}: {title!r}: missing!")
            info.status = "missing"
            info.msg = "Page is missing"
            return info

        text = page.get_text()
        if not text or not text.strip():
            info.status = "skipped"
            info.msg = "Page is empty"
            return info

        new_text, summary = self._make_new_text(title, text)

        if new_text == text:
            info.status = "skipped"
            info.msg = "No changes"
            return info

        try:
            result = page.edit(new_text, summary)
        except Exception as e:
            info.status = "failed"
            info.msg = str(e)
            return info

        if result.get("success"):
            info.status = "changed"
            info.newrevid = result.get("newrevid", 0)
            return info

        info.status = "failed"
        info.msg = result.get("error", "Unknown error")
        return info

    def _make_new_text(self, title: str, text: str) -> tuple[str, str]:
        """
        Processes text and its associated archive to generate a modified version and a summary.

        Args:
            title (str): The title of the page.
            text (str): The original text content of the page.

        Returns:
            tuple[str, str]: A tuple containing the new processed text and the corresponding summary.
        """
        # Create a new OnePage instance with the given title and text
        fixer = OnePage(title, text)
        new_text = fixer.run()
        is_diff = new_text != text

        # Create a new OnePageArchive instance with the title and processed text
        archive_fixer = OnePageArchive(title, new_text)

        # Process the text again using the OnePageArchive instance
        new_text = archive_fixer.run()

        # Use archive_fixer summary if OnePage made no changes
        summary = fixer.summary if is_diff else archive_fixer.summary

        return new_text, summary


__all__ = [
    "FixCs1ParamsWorker",
]
