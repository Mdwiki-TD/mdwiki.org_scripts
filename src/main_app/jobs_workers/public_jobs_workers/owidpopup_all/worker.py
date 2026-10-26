"""
Worker module for owidpopup_all.

Replaces OWIDPopup templates with OWID templates on MediaWiki pages belonging to a category.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging

from mwclient.client import Site
import wikitextparser as wtp

from ....api_services import MwClientPage, get_category_members
from ...base_worker import BaseObjectsJobWorker, JobsRunner
from ...shared_objects import SharedworkerObject, UpdaterOutcome

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TemplateRename:
    old_names: list[str]
    new_name: str
    arguments: dict[str, str]


OWID_POPUP_RENAME = TemplateRename(
    old_names=["OWIDPopup", "OWID_popup"],
    new_name="OWID",
    arguments={
        "owid": "chart",
    },
)


def replace_templates(
    text: str,
    renames: list[TemplateRename],
) -> str:
    """
    Replace wikitext templates and arguments based on configuration rules.
    """
    rename_map: dict[str, tuple[str, dict[str, str]]] = {}
    for r in renames:
        args_map = {k.strip().lower(): v for k, v in r.arguments.items()}
        for old_name in r.old_names:
            norm_name = old_name.strip().lower().replace("_", " ")
            rename_map[norm_name] = (r.new_name, args_map)

    parsed = wtp.parse(text)
    for template in parsed.templates:
        norm_t_name = template.name.strip().lower().replace("_", " ")
        if norm_t_name in rename_map:
            new_t_name, args_map = rename_map[norm_t_name]
            template.name = new_t_name

            for arg in template.arguments:
                norm_arg_name = arg.name.strip().lower()
                if norm_arg_name in args_map:
                    arg.name = args_map[norm_arg_name]

    return parsed.string


class OwidPopupAllWorker(BaseObjectsJobWorker):
    """Replace OWIDPopup templates with OWID templates in category pages."""

    def __init__(self, data: JobsRunner) -> None:
        self.args = data.args or {}
        self.site: Site | None = None

        super().__init__(data)

        self.result: SharedworkerObject = SharedworkerObject()

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "owidpopup_all"

    def process(self) -> SharedworkerObject:
        if not self._check_site():
            return self.result

        category = self.args.get("category")
        if not category or not str(category).strip():
            category = "Category:Gadget:OWIDPopup"
        else:
            category = str(category).strip()
            if not category.lower().startswith("category:"):
                category = f"Category:{category}"

        titles: list[str] = get_category_members(
            site=self.site,
            category_title=category,
            namespace=0,
        )

        total = len(titles)
        self.result.summary.total = total
        per_item = self.get_priority(total) if total else 1

        logger.info(
            f"Job {self.job_id}: Processing {total} pages from category {category!r}"
        )

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
        new_text = replace_templates(text, [OWID_POPUP_RENAME])
        if new_text == text:
            return new_text, ""

        summary = "Replace OWIDPopup with OWID"
        logger.info("Job %s: %r: %s", self.job_id, title, summary)
        return new_text, summary


__all__ = [
    "OwidPopupAllWorker",
    "TemplateRename",
    "OWID_POPUP_RENAME",
    "replace_templates",
]
