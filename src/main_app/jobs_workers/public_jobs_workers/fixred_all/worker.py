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
            self.result.summary.processed += 1

            try:
                outcome = self._process_one(title, state)
            except Exception as exc:
                logger.exception("job failed for %s", title)
                self.result.pages_errors.append({"title": title, "msg": str(exc)})
                continue

            self.record_page_outcome(outcome, title)

            if outcome.kind == "changed" and self.check_cancel_db_periodic():
                break

            if i == 1 or i % per_item == 0:
                self._save_progress()

        if self.result.status in ("pending", "running"):
            self.result.status = "completed"

        return self.result

    def record_page_outcome(self, outcome: UpdaterOutcome, title: str) -> None:
        page_record = {
            "title": title,
            "msg": outcome.msg,
        }
        if outcome.kind == "changed":
            page_record["newrevid"] = str(outcome.newrevid)
            self.result.pages_changed.append(page_record)

        elif outcome.kind == "missing":
            self.result.pages_missing.append(title)

        elif outcome.kind == "skipped":
            self.result.pages_skipped.append(page_record)

        elif outcome.kind == "error":
            self.result.pages_errors.append(page_record)

        else:
            page_record["status"] = outcome.kind
            self.result.pages_processed.append(page_record)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_one(self, title: str, state: RunState) -> UpdaterOutcome:
        page = MwClientPage(title, self.site)
        if not page.exists():
            logger.info(f"Job {self.job_id}: {title!r}: missing!")
            return UpdaterOutcome(kind="missing")

        text = page.get_text()
        if not text or not text.strip():
            return UpdaterOutcome(kind="skipped", msg="Page is empty")

        new_text, summary = self.make_new_text(title, state, text)

        if new_text == text:
            return UpdaterOutcome(kind="skipped", msg="No changes")

        result = page.edit(new_text, summary)

        if result.get("success"):
            return UpdaterOutcome(kind="changed", newrevid=result.get("newrevid", 0))

        return UpdaterOutcome(kind="error", msg=result.get("error", "Unknown error"))

    def make_new_text(self, title: str, state: RunState, text: str) -> tuple[str, str]:
        new_text = work_on_text(title, text, self.site, state)
        summary = "Fix redirects"
        return new_text, summary

__all__ = [
    "FixRedAllWorker",
]
