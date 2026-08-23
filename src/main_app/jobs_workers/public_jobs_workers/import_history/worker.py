"""
Worker module for import_history.

Migrated from src/main_app/jobs/workers/import_history.py.
Imports revision history from English Wikipedia to mdwiki.
"""

from __future__ import annotations

import logging

from mwclient.client import Site

from ....api_services import MwClientPage
from ....api_services.query_api import import_page_from_wiki
from ...base_worker import BaseObjectsJobWorker, JobsRunner
from .objects import ImportHistoryWorkerObject, ImportUpdaterOutcome

logger = logging.getLogger(__name__)


class ImportHistoryWorker(BaseObjectsJobWorker):
    """Import revision history from enwiki to mdwiki."""

    def __init__(self, data: JobsRunner) -> None:
        self.args = data.args or {}
        self.site: Site | None = None

        super().__init__(data)

        self.result: ImportHistoryWorkerObject = ImportHistoryWorkerObject()

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "import_history"

    def process(self) -> ImportHistoryWorkerObject:
        if not self._check_site():
            return self.result

        titles_raw = self.args.get("titles", [])
        from_lang = self.args.get("from_lang", "en")
        self.result.from_lang = from_lang

        if isinstance(titles_raw, str):
            titles = [t.strip() for t in titles_raw.splitlines() if t.strip()]
        else:
            titles = [t.replace("_", " ").strip() for t in titles_raw if t and t.strip()]

        total = len(titles)
        self.result.summary.total = total
        per_item = self.get_priority(total) if total else 1

        logger.info(f"Job {self.job_id}: Importing history for {total} titles")

        for i, title in enumerate(titles, start=1):
            if self.is_cancelled():
                break

            info = ImportUpdaterOutcome(title=title)
            self._process_one(info)

            self.update_status(info)

            # Check DB if the job cancelled every N successful edits
            if info.status in ("imported", "imported_fallback") and self.check_cancel_db_periodic():
                break

            if i == 1 or i % per_item == 0:
                self._save_progress()

        if self.result.status in ("pending", "running"):
            self.result.status = "completed"

        return self.result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_one(self, info: ImportUpdaterOutcome) -> ImportUpdaterOutcome:
        title = info.title

        page = MwClientPage(title, self.site)
        if not page.exists():
            logger.info(f"Job {self.job_id}: {title!r}: missing!")
            info.status = "missing"
            return info

        text = page.get_text()
        if not text or not text.strip():
            info.status = "skipped"
            info.msg = "Page is empty"
            return info

        result = import_page_from_wiki(self.site, title, family="wikipedia")
        if result.get("error"):
            logger.warning(f"Job {self.job_id}: import_page failed for {title}: {result['error']}")
            info.status = "error"
            info.msg = result["error"]
            return info

        revisions = (result.get("import") or [{}])[0].get("revisions", 0)

        if not revisions:
            logger.info(f"Job {self.job_id}: {title!r}: import returned 0 revisions")
            info.status = "error"
            info.msg = "Import returned 0 revisions"
            return info

        logger.info(f"Job {self.job_id}: {title!r}: imported {revisions} revision(s)")

        # Re-save the original body so the page content matches what the operator
        # saw before the import.
        try:
            saved = page.edit(text, "")
        except Exception as e:
            logger.warning(f"Job {self.job_id}: {title!r}: failed to save original body: {e}")
            info.status = "error"
            info.msg = f"Failed to save original body: {e}"
            return info

        if saved.get("success"):
            info.status = "imported"
            info.newrevid = saved.get("newrevid", 0)
            return info

        # assert self.site is not None

        username = "Mr._Ibrahem"
        if self.site and self.site.username:
            username = self.site.username

        fallback_title = f"User:{username}/{title}"
        logger.info(f"Job {self.job_id}: {title!r}: top-level save failed; writing to {fallback_title!r}")

        fallback_page = MwClientPage(fallback_title, self.site)

        fallback_result = fallback_page.edit(
            text=text,
            summary="Returns the article text after importing the history",
        )

        if fallback_result.get("success"):
            info.status = "imported_fallback"
            info.newrevid = fallback_result.get("newrevid", 0)
            return info

        logger.warning(f"Job {self.job_id}: fallback save failed too for {fallback_title}")

        info.status = "error"
        info.msg = fallback_result.get("error", "Unknown error")
        return info

    def update_status(self, info: ImportUpdaterOutcome) -> None:
        self.result.summary.processed += 1
        if info.status in ["pending", "running"]:
            info.status = "completed"

        if info.status == "imported":
            self.result.pages_imported.append(info)

        elif info.status == "imported_fallback":
            self.result.pages_imported_fallback.append(info)

        elif info.status == "missing":
            self.result.pages_missing.append(info)

        elif info.status == "error":
            self.result.pages_errors.append(info)
        else:
            self.result.pages_processed.append(info)


__all__ = [
    "ImportHistoryWorker",
]
