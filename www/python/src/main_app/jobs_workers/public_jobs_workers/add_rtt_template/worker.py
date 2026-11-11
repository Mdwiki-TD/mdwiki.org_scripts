"""
Worker module for add_rtt_template.

Adds {{RTT}} template to all pages in Category:RTT that don't already have it.
"""

from __future__ import annotations

import logging

import wikitextparser as wtp
from mwclient.client import Site

from ....api_services import MwClientPage, get_template_pages
from ....api_services.category import get_category_members
from ...base_worker import BaseObjectsJobWorker, JobsRunner
from ...shared_objects import SharedworkerObject, UpdaterOutcome

logger = logging.getLogger(__name__)


def add_rtt_to_text(text: str, title: str) -> str:
    new_line = "{{RTT}}"

    if text.find(new_line) != -1:
        logger.info(f"page already tagged.{new_line}")
        return text

    target_templates = ["rtt"]

    parsed = wtp.parse(text)

    for temp in parsed.templates:
        name = str(temp.normal_name()).strip().lower().replace("_", " ")
        if name in target_templates:
            logger.info(f"page already tagged.{title=}")
            return text

    newtext = text

    last_section = None

    for section in parsed.sections:
        last_section = section

    category_found = False
    if last_section:
        for line in last_section.contents.split("\n"):
            if line.strip().lower().startswith("[[category:"):
                newtext = newtext.replace(line, f"{new_line}\n{line}", 1)
                category_found = True
                break
    if not category_found:
        newtext = f"{newtext.rstrip()}\n{new_line}"

    return newtext


class AddRttTemplateWorker(BaseObjectsJobWorker):
    """Add {{RTT}} template to pages in Category:RTT."""

    def __init__(self, data: JobsRunner) -> None:
        self.args = data.args or {}
        self.site: Site | None = None

        super().__init__(data)

        self.result: SharedworkerObject = SharedworkerObject()

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "add_rtt_template"

    def process(self) -> SharedworkerObject:
        if not self._check_site():
            return self.result

        mdwiki_pages = get_category_members(
            site=self.site,
            category_title="Category:RTT",
            namespace=0,
        )

        if not mdwiki_pages:
            self.result.note = "No pages in Category:RTT"
            self.result.status = "skipped"
            self.result.summary.total = 0
            self.result.summary.processed = 0
            return self.result

        logger.info(f"Job {self.job_id}: len of mdwiki_pages: {len(mdwiki_pages)}")
        template_pages = get_template_pages(
            title="Template:RTT",
            site=self.site,
            namespace=0,
        )

        logger.info(f"Job {self.job_id}: len of template_pages: {len(template_pages)}")

        pages_to_add = [x for x in mdwiki_pages if x not in template_pages]
        logger.info(f"Job {self.job_id}: len of pages_to_add: {len(pages_to_add)}")

        total = len(pages_to_add)
        if not pages_to_add:
            self.result.note = "No pages to add"
            self.result.status = "completed"
            self.result.summary.total = 0
            self.result.summary.processed = 0
            return self.result

        self.result.summary.total = total
        self._save_progress()

        per_item = self.get_priority(total) if total else 1

        for i, title in enumerate(pages_to_add, start=1):
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

        ns = page.namespace
        if ns != 0:
            info.status = "skipped"
            info.msg = "Not in main namespace"
            return info

        text = page.get_text()
        if not text or not text.strip():
            info.status = "skipped"
            info.msg = "Page is empty"
            return info

        parsed = wtp.parse(text)
        if any(str(t.normal_name()).strip().lower().replace("_", " ") == "rtt" for t in parsed.templates):
            info.status = "skipped"
            info.msg = "Already has RTT template"
            return info

        try:
            new_text = add_rtt_to_text(text, title)
        except Exception as e:
            logger.exception(f"Job {self.job_id}: {title!r}: error")
            info.status = "failed"
            info.msg = str(e)
            return info

        if new_text == text:
            info.status = "skipped"
            info.msg = "No changes"
            return info

        try:
            result = page.edit(
                text=new_text,
                summary="Added {{RTT}}",
                nocreate=True,
            )
        except Exception as e:
            logger.exception(f"Job {self.job_id}: {title!r}: error")
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
    "AddRttTemplateWorker",
]
