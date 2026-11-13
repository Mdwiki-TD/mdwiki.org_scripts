"""
Worker module for webarchive_remover.

Removes redundant {{Webarchive}} templates from pages where a CS1/CS2
citation template already carries the same archive-url / archive-date.
"""

from __future__ import annotations

import logging

from mwclient.client import Site

from ....api_services import MwClientPage, get_template_pages
from ...base_worker import BaseObjectsJobWorker, JobsRunner
from ...shared_objects import SharedworkerObject, UpdaterOutcome
from .text_changer import WebarchiveRemover

logger = logging.getLogger(__name__)


class WebarchiveRemoverWorker(BaseObjectsJobWorker):
    """Remove duplicate {{Webarchive}} templates from mdwiki pages."""

    def __init__(self, data: JobsRunner) -> None:
        self.args = data.args or {}
        self.site: Site | None = None

        super().__init__(data)

        self.result: SharedworkerObject = SharedworkerObject()
        self.remover = WebarchiveRemover(merge=True)

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "webarchive_remover"

    def process(self) -> SharedworkerObject:
        if not self._check_site():
            return self.result

        assert self.site is not None

        mode = self.args.get("mode", "template")
        limit = int(self.args.get("limit") or 0) or None

        if mode == "all":
            titles = self._get_all_pages()
        else:
            titles = self._get_template_pages()

        if limit:
            titles = self._apply_limits(titles, limit)

        total = len(titles)
        self.result.summary.total = total
        per_item = self.get_priority(total) if total else 1

        logger.info(f"Job {self.job_id}: Processing {total} pages (mode={mode})")

        for i, title in enumerate(titles, start=1):
            logger.debug(f"i: {i}/{total}, page: {title}.")
            if self.is_cancelled():
                break

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
    # Page selection
    # ------------------------------------------------------------------

    def _get_template_pages(self) -> list[str]:
        """Get all pages that transclude Template:Webarchive (namespace 0)."""
        return get_template_pages(
            title="Template:Webarchive",
            site=self.site,
            namespace=0,
        )

    def _get_all_pages(self) -> list[str]:
        """Get all pages in the main namespace via allpages (lazy pagination)."""
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
        return [page.name if hasattr(page, "name") else str(page) for page in titles]

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
        new_text, stats = self.remover.process(text)

        if new_text == text:
            return new_text, ""

        if stats.removed and stats.merged:
            summary = "Remove duplicate {{Webarchive}} (archive already in citation template)"
        elif stats.removed:
            summary = "Remove duplicate {{Webarchive}} (archive already in citation template)"
        elif stats.merged:
            summary = "Merge {{Webarchive}} into citation template"
        else:
            summary = "Clean up {{Webarchive}} templates"

        logger.info(
            "Job %s: %r: removed=%d, merged=%d, skipped=%d",
            self.job_id,
            title,
            stats.removed,
            stats.merged,
            len(stats.skipped),
        )
        return new_text, summary


__all__ = [
    "WebarchiveRemoverWorker",
]
