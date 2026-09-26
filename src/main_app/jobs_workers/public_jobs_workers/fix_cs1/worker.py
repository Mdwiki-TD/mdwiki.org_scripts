"""
Worker module for fix_cs1.

Migrated from

https://github.com/Mdwiki-TD/mdwiki-python-files/tree/main/src/md_core/fix_cs1

TODO: import logic from _works_files/original_code/python/fix_cs1

"""

from __future__ import annotations

import logging

from mwclient.client import Site

from ....api_services import MwClientPage, get_category_members
from ...base_worker import BaseObjectsJobWorker, JobsRunner
from ...shared_objects import SharedworkerObject, UpdaterOutcome

logger = logging.getLogger(__name__)


class FixCs1Worker(BaseObjectsJobWorker):
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
        return "fix_cs1"

    def process(self) -> SharedworkerObject:
        if not self._check_site():
            return self.result

        titles: list[str] = get_category_members(
            site=self.site,
            category_title="Category:CS1 errors: missing periodical",
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
        # TODO: import logic from _works_files/original_code/python/fix_cs1_params
        new_text = text
        summary = ".."
        return new_text, summary


__all__ = [
    "FixCs1Worker",
]
