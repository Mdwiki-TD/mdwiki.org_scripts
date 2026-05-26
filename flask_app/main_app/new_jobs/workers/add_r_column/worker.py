"""
Worker module for Add R column.

(TODO: import logic from https://github.com/Mdwiki-TD/mdwiki-python-files/blob/main/src/md_core/add_rtt/bot.py)
"""

from __future__ import annotations

import sys
import re
import logging
import threading
from datetime import datetime
from typing import Any, Dict

from ....new_jobs.base_worker import BaseJobWorker
from .add_rtt import R_NEW_ROW, add_to_tables, fix_title

logger = logging.getLogger(__name__)


def find_redirects(pages, text):

    to_f = "== List =="

    mdwiki_pages = []

    if text.find(to_f) != -1:
        text = text.split(to_f)[1]
        # match all links like [[.*?]]
        pattern = r"\[\[(.*?)\]\]"
        links = re.findall(pattern, text)
        mdwiki_pages = links

    mdwiki_pages = list(set(mdwiki_pages))

    mdwiki_pages = [fix_title(x.strip()) for x in mdwiki_pages if x.find("|") == -1 and x not in pages]

    logger.info(f" pages: {len(mdwiki_pages)}")

    titles = api_new.get_titles_redirects(mdwiki_pages)

    # titles = api_new.get_titles_redirects(["Ehlers–Danlos syndrome"]) # {'Ehlers–Danlos syndrome': 'Ehlers–Danlos syndromes'}
    redirects = dict(titles.items())

    return redirects


class AddRColumnWorker(BaseJobWorker):
    """Add R column to tables."""

    def __init__(
        self,
        job_id: int,
        args: dict[str, Any] | None,
        user: dict[str, Any] | None,
        cancel_event: threading.Event | None = None,
    ) -> None:
        self.job_id = job_id
        self.args = args or {}
        super().__init__(job_id, user, cancel_event)

    def get_job_type(self) -> str:
        return "add_r_column"

    def get_initial_result(self) -> Dict[str, Any]:
        return {
            "status": "pending",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "cancelled_at": None,
            "summary": {
                "scanned": 0,
                "updated": 0,
                "errors": 0,
                "total": 0,
            },
            "new_text": "",
        }

    def process(self) -> Dict[str, Any]:
        """
        Placeholder process method.
        """

        logger.info(f"Job {self.job_id}: Placeholder for Add R column.")

        if self.is_cancelled():
            return self.result

        # ----
        self._start()
        # ----
        self.result["summary"]["scanned"] += 1
        self.result["summary"]["skipped"] += 1

        if self.result.get("status") in ("pending", "running"):
            self.result["status"] = "completed"

        return self.result

    def _start(self) -> None:
        """Start the job."""
        self.result["status"] = "running"

        title = "WikiProjectMed:WikiProject Medicine/Popular pages"
        page = md_MainPage(title, "www", family="mdwiki")

        if not page.exists():
            return False

        text = page.get_text()

        new_text = add_to_tables(text, redirects={}, pages=[])

        if new_text != text:
            page.save(newtext=new_text, summary="Add R column")
            text = new_text

        if "only_column" in sys.argv:
            return None

        old_counts = text.count(R_NEW_ROW.strip())

        # pages = CatDepth("Category:RTT", sitecode="www", family="mdwiki", depth=0, ns=0)
        pages = api_new.Get_template_pages("Template:RTT", namespace=0)

        redirects = find_redirects(pages, text)

        newtext = add_to_tables(text, redirects, pages)

        with open(Dir / "page_text.txt", "w", encoding="utf-8") as f:
            f.write(newtext)

        if newtext == text:
            logger.info("no changes")
            return None

        # count R_NEW_ROW in newtext
        counts = newtext.count(R_NEW_ROW.strip())

        counts = counts - old_counts

        summary = f"Added R column to {counts} titles."

        page.save(newtext=newtext, summary=summary, nocreate=1, minor="")


def add_r_column_worker_entry(
    job_id: int,
    user: Dict[str, Any] | None = None,
    *,
    cancel_event: threading.Event | None = None,
    args: Dict[str, Any] | None = None,
) -> None:
    """Background worker entry-point."""
    logger.info(f"Starting job {job_id}: add_r_column")
    worker = AddRColumnWorker(
        job_id=job_id,
        user=user,
        args=args,
        cancel_event=cancel_event,
    )
    worker.run()


__all__ = [
    "add_r_column_worker_entry",
]
