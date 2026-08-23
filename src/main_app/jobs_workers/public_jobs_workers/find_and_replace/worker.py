"""
Worker module for find_and_replace.

Migrated from src/main_app/jobs/workers/find_and_replace.py.
"""

from __future__ import annotations

import logging
from datetime import datetime

from mwclient.client import Site

from ....api_services import MwClientPage
from ...base_worker import BaseObjectsJobWorker, JobsRunner
from ...shared_objects import UpdaterOutcome
from .objects import FindAndReplaceWorkerObject

# from ....api_services.query_api import search_pages

logger = logging.getLogger(__name__)


class FindAndReplaceWorker(BaseObjectsJobWorker):
    """Find-and-replace bot for mdwiki pages."""

    def __init__(self, data: JobsRunner) -> None:
        self.args = data.args or {}
        self.site: Site | None = None

        super().__init__(data)

        self.result: FindAndReplaceWorkerObject = FindAndReplaceWorkerObject()

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "find_and_replace"

    def process(self) -> FindAndReplaceWorkerObject:
        if not self._check_site():
            return self.result

        str_find = self.args.get("str_find", "")
        str_replace = self.args.get("str_replace", "")
        listtype = self.args.get("listtype", "newlist")
        number = self.args.get("number")

        if not str_find:
            self.result.status = "failed"
            self.result.error = "`find` cannot be empty."
            self.result.failed_at = datetime.now().isoformat()
            return self.result

        self.result.text_find = str_find
        self.result.text_replace = str_replace

        try:
            cap = int(number) if number and int(number) > 0 else None
        except ValueError:
            cap = None

        self.result.cap = cap

        # save json file before start search
        self._save_progress()

        titles = self._resolve_titles(str_find, listtype)
        total = len(titles)
        self.result.summary.total = total
        per_item = self.get_priority(total) if total else 1

        logger.info(f"Job {self.job_id}: Processing {total} pages (listtype={listtype})")

        for i, title in enumerate(titles, start=1):
            logger.debug(f"i: {i}/{total}, page: {title}.")
            if self.is_cancelled():
                self.result.stopped = True
                break

            if cap is not None and self.result.summary.changed >= cap:
                logger.info(f"Job {self.job_id}: Reached cap of {cap} modifications")
                break

            info = UpdaterOutcome(title=title)

            self._process_one(info, str_find, str_replace)

            self.update_status(info)

            # Check DB if the job cancelled every N successful edits
            if info.status == "changed" and self.check_cancel_db_periodic():
                self.result.stopped = True
                break

            if i == 1 or i % per_item == 0:
                self._save_progress()

        if self.result.status in ("pending", "running"):
            self.result.status = "completed"

        return self.result

    def _resolve_titles(
        self,
        str_find: str,
        listtype: str,
    ) -> list[str]:
        """Pick the page list to walk based on *listtype*."""
        assert self.site is not None
        if listtype == "newlist":
            # return search_pages(str_find, self.site, namespace=0, limit="max")
            search_data = self.site.search(
                str_find,
                namespace="0",
                what="text",
                redirects=False,
                max_items=None,
                api_chunk_size=None,
            )
            # logger.debug(search_data)
            results = [r.get("title") for r in search_data if r.get("title")]
            logger.info(f"Found {len(results)} pages matching '{str_find}'")
            return results

        titles = list(
            self.site.allpages(
                start="!",
                namespace=0,
                filterredir="nonredirects",
                dir="ascending",
                generator=True,
            )
        )
        # oldlist: walk every mainspace page.
        return [p.name for p in titles]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_one(self, info: UpdaterOutcome, str_find: str, str_replace: str) -> UpdaterOutcome:
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

        new_text, summary = self._make_new_text(str_find, str_replace, text)

        if new_text == text:
            info.status = "skipped"
            info.msg = "No changes"
            return info

        try:
            result = page.edit(new_text, summary)
        except Exception as e:
            info.status = "error"
            info.msg = str(e)
            return info

        if result.get("success"):
            info.status = "changed"
            info.newrevid = result.get("newrevid", 0)
            return info

        info.status = "error"
        info.msg = result.get("error", "Unknown error")
        return info

    def _make_new_text(self, str_find: str, str_replace: str, text: str) -> tuple[str, str]:
        new_text = text.replace(str_find, str_replace)
        summary = "Replace via mdwiki.toolforge.org find-and-replace tool."
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

        elif info.status == "error":
            self.result.pages_errors.append(info)

        else:
            self.result.pages_processed.append(info)


__all__ = [
    "FindAndReplaceWorker",
]
