"""
Worker module for fixref.

Migrated from src/main_app/jobs/workers/fixref.py.
Normalizes cite-template formatting on mdwiki pages.
"""

from __future__ import annotations

import logging
from datetime import datetime

from mwclient.client import Site

from ....api_services import MwClientPage, get_category_members
from ....services.fixref_shared.fixref_text_new import fix_ref_template
from ...base_worker import BaseObjectsJobWorker, JobsRunner
from ...shared_objects import SharedworkerObject, UpdaterOutcome

logger = logging.getLogger(__name__)

MAX_PAGES_FIXREF = 20000


class FixRefWorker(BaseObjectsJobWorker):
    """Normalize references on mdwiki pages."""

    def __init__(self, data: JobsRunner) -> None:
        self.args = data.args or {}
        self.site: Site | None = None

        super().__init__(data)

        self.result: SharedworkerObject = SharedworkerObject()

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "fixref"

    def process(self) -> SharedworkerObject:
        if not self._check_site():
            return self.result

        titles_raw = self.args.get("titles") or self.args.get("titlelist")
        category = self.args.get("category") or self.args.get("cat")
        number = self.args.get("number")

        self._save_progress()

        pages: list[str] = []

        if titles_raw:
            pages = self._resolve_targets(titles_raw)
        elif category:
            pages = self._resolve_targets_category(category)
        elif number:
            pages = self._resolve_targets_number(number)

        if not pages:
            self.result.status = "failed"
            self.result.error = "Provide at least one of: titles, category, number."
            self.result.failed_at = datetime.now().isoformat()
            return self.result

        total = len(pages)
        self.result.summary.total = total
        per_item = self.get_priority(total) if total else 1

        logger.info(f"Job {self.job_id}: Processing {total} pages")

        for i, title in enumerate(pages, start=1):
            logger.debug(f"i: {i}/{total}, page: {title}.")
            if self.is_cancelled():
                break

            info = UpdaterOutcome(title=title)
            self._process_one(info)

            self.update_status(info)

            # Check DB if the job cancelled every N successful edits
            if info.status == "changed" and self.check_cancel_db_periodic():
                break

            if i == 1 or i % per_item == 0:
                self._save_progress()

        if self.result.status in ("pending", "running"):
            self.result.status = "completed"

        return self.result

    def _resolve_targets_category(self, category) -> list:
        cat = category.strip()
        if not cat.lower().startswith("category:"):
            cat = f"Category:{cat}"

        members = get_category_members(
            site=self.site,
            category_title=cat,
            limit=500,
        )

        return [m for m in members if not m.startswith("Category:")][:MAX_PAGES_FIXREF]

    def _resolve_targets_number(self, number: int) -> list[str]:
        assert self.site is not None
        try:
            capped = min(int(number), MAX_PAGES_FIXREF)
        except ValueError:
            capped = MAX_PAGES_FIXREF

        titles = list(
            self.site.allpages(
                start="!",
                namespace=0,
                filterredir="nonredirects",
                dir="ascending",
                generator=True,
                limit=capped,
            )
        )
        return [p.name for p in titles]

    def _resolve_targets(
        self,
        titles: str | list[str] | None,
    ) -> list[str]:
        """Resolve which pages to process given the input options."""
        if not titles:
            return []

        if isinstance(titles, str):
            titles = [t.strip() for t in titles.splitlines() if t.strip()]

        cleaned: list[str] = []
        seen: set[str] = set()

        for t in titles:
            t = t.replace("_", " ").strip()
            if not t or t in seen:
                continue
            seen.add(t)
            cleaned.append(t)

        return cleaned[:MAX_PAGES_FIXREF]

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

        new_text, summary = self._make_new_text(text)

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

    def _make_new_text(self, text: str) -> tuple[str, str]:
        try:
            new_text, summary = fix_ref_template(text, returnsummary=True)
        except Exception as e:
            logger.error("Error while fixing references: %s", str(e))
            return text, f"Error: {e}"

        summary = summary or "Normalize references"
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
    "FixRefWorker",
]
