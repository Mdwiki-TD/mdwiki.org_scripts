"""
Worker module for archive_today.

Removes archive.today links and templates from pages.
"""

from __future__ import annotations

import logging

from mwclient.client import Site

from ....api_services import MwClientPage
from ...base_worker import BaseObjectsJobWorker, JobsRunner
from ...shared_objects import SharedworkerObject, UpdaterOutcome
from .removers import ArchiveTodayRemover, Cs2ArchiveTodayRemover

logger = logging.getLogger(__name__)


class ArchiveTodayWorker(BaseObjectsJobWorker):
    """Remove archive.today links from all mdwiki pages."""

    def __init__(self, data: JobsRunner) -> None:
        self.args = data.args or {}
        self.site: Site | None = None

        super().__init__(data)

        self.result: SharedworkerObject = SharedworkerObject()
        self.cs2_remover = Cs2ArchiveTodayRemover()
        self.webarchive_remover = ArchiveTodayRemover()

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "archive_today"

    def process(self) -> SharedworkerObject:
        if not self._check_site():
            return self.result

        assert self.site is not None
        titles = list(
            self.site.allpages(
                start="!",
                namespace=0,
                filterredir="nonredirects",
                dir="ascending",
                generator=True,
            )
        )

        total = len(titles)
        self.result.summary.total = total
        per_item = self.get_priority(total) if total else 1

        logger.info(f"Job {self.job_id}: Processing {total} pages")

        for i, page in enumerate(titles, start=1):
            logger.debug(f"i: {i}/{total}, page: {page}.")
            if self.is_cancelled():
                break

            title = page.name if hasattr(page, "name") else str(page)

            info = UpdaterOutcome(title=title)
            self._process_one(info)

            self.update_status(info)

            if info.status == "updated" and self.check_cancel_db_periodic():
                break

            if i == 1 or i % per_item == 0:
                self.save_progress()

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
            info.status = "updated"
            info.newrevid = result.get("newrevid", 0)
            return info

        info.status = "failed"
        info.msg = result.get("error", "Unknown error")
        return info

    def _make_new_text(self, title: str, text: str) -> tuple[str, str]:
        # 1. Remove archive.today from CS1/CS2 cite templates
        text_after_cs2, _ = self.cs2_remover.remove(text)
        # 2. Remove webarchive templates pointing to archive.today
        new_text, _ = self.webarchive_remover.remove(text_after_cs2)
        summary = "Remove archive.today links"
        return new_text, summary


__all__ = [
    "ArchiveTodayWorker",
]
