"""
Worker module for fixred_all.

Migrated from src/main_app/jobs/workers/fixred_all.py.
"""

from __future__ import annotations

import logging

from mwclient.client import Site

from ....api_services import MwClientPage
from ....services.fixref_shared.fixred_worker import work_on_text
from ....services.fixref_shared.objects import RunState
from ...base_worker import BaseObjectsJobWorker, JobsRunner
from ...shared_objects import SharedworkerObject, UpdaterOutcome

logger = logging.getLogger(__name__)


class FixRedAllWorker(BaseObjectsJobWorker):
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
        return "fixred_all"

    def process(self) -> SharedworkerObject:
        if not self._check_site():
            return self.result

        state = RunState()
        titles = list(
            self.site.allpages(  # type: ignore
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
            self._process_one(info, state)

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

    def _process_one(self, info: UpdaterOutcome, state: RunState) -> UpdaterOutcome:
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

        new_text, summary = self._make_new_text(title, state, text)

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

    def _make_new_text(self, title: str, state: RunState, text: str) -> tuple[str, str]:
        new_text = work_on_text(title, text, self.site, state)
        summary = "Fix redirects"
        return new_text, summary

    def update_status(self, info: UpdaterOutcome) -> None:
        self.result.summary.processed += 1
        if info.status in ["pending", "running"]:
            info.status = "completed"

        if info.status == "changed":
            self.result.pages_changed.append(info)

        elif info.status == "missing":
            self.result.pages_missing.append(info)

        elif info.status == "skipped":
            self.result.pages_skipped.append(info)

        elif info.status == "failed":
            self.result.pages_errors.append(info)

        else:
            self.result.pages_processed.append(info)


__all__ = [
    "FixRedAllWorker",
]
