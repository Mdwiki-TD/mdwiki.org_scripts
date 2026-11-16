"""
Worker module for medicine_articles.

Generates a statistical report of medical articles by language for WikiProject Medicine
and publishes it to mdwiki.org.

Migrated from medicine_articles/legacy.py.
"""

from __future__ import annotations

import datetime
import logging

from ....api_services.mwclient_page import MwClientPage
from ....api_services.wikidb.analytics import WikiReplicaDB
from ...base_worker import BaseObjectsJobWorker, JobsRunner
from .objects import LangCount, MedicineArticlesWorkerObject
from ...shared_objects import UpdaterOutcome

logger = logging.getLogger(__name__)

_SQL_LANG_COUNTS = """
select ll_lang, count(page_title) as counts
    from page , langlinks , page_assessments , page_assessments_projects
    where pap_project_title = "Medicine"
    and pa_project_id = pap_project_id
    and pa_page_id = page_id
    and page_id = ll_from
    and page_is_redirect = 0
    and page_namespace = 0
    group by ll_lang
"""

_SQL_TOTAL_ARTICLES = """
select count(pa_page_id) as articles
    from page, page_assessments , page_assessments_projects
    where pap_project_title = "Medicine"
    and pa_project_id = pap_project_id
    and pa_page_id = page_id
    and page_is_redirect = 0
    and page_namespace = 0
"""


class MedicineArticlesWorker(BaseObjectsJobWorker):
    """Generate WikiProject Medicine article stats by language and publish to mdwiki."""

    JOB_TYPE = "medicine_articles"

    def __init__(
        self,
        data: JobsRunner,
        lang_db: WikiReplicaDB | None = None,
    ) -> None:
        super().__init__(data)
        self.result: MedicineArticlesWorkerObject = MedicineArticlesWorkerObject()
        self.lang_db = lang_db or WikiReplicaDB("enwiki")

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def _process_one(self, info: UpdaterOutcome) -> UpdaterOutcome:
        try:
            languages = self._fetch_lang_counts()
        except Exception as e:
            self.handle_error(e, "fetching language counts")
            info.status = "failed"
            return info

        try:
            total_articles = self._fetch_total_articles()
        except Exception as e:
            self.handle_error(e, "fetching total articles")
            info.status = "failed"
            return info

        if "en" not in languages:
            languages["en"] = total_articles

        # Build LangCount entries
        sorted_langs = dict(sorted(languages.items(), key=lambda item: item[1], reverse=True))

        for lang, count in sorted_langs.items():
            self.result.languages.append(LangCount(lang=lang, count=count, status="completed"))

        self.result.summary.total_languages = len(sorted_langs)
        self.result.summary.total_articles = total_articles
        self.result.summary.total_articles_all_langs = sum(sorted_langs.values())

        # Build wikitext
        text = self._build_wikitext(sorted_langs)

        page = MwClientPage(info.title, self.site)

        page_text = page.get_text()
        if page_text == text:
            info.status = "skipped"
            self.result.status = "skipped"
            logger.info(f"Job {self.job_id}: Page {info.title!r} is already up to date")
            return info

        # Save to wiki
        try:
            result = page.edit(text, "update")
            info.status = "updated"
            info.newrevid = result.get("newrevid", 0)

        except Exception as e:
            self.handle_error(e, "saving page to wiki")
            info.status = "failed"
            return info

        self.result.summary.page_updated = True
        self.result.status = "completed"
        logger.info(f"Job {self.job_id}: Updated page {info.title!r}")

        return info

    def process(self) -> MedicineArticlesWorkerObject:
        if not self._check_site():
            return self.result

        # Determine page title
        year = datetime.datetime.now().year
        title = f"WikiProjectMed:WikiProject Medicine/Stats/Number of articles by language {year}"
        self.result.page_title = title

        info = UpdaterOutcome(title=title)

        ok = self._process_one(info)
        if not ok:
            return self.result

        self.update_status(info)

        if self.result.status in ("pending", "running"):
            self.result.status = "completed"

        return self.result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_lang_counts(self) -> dict[str, int]:
        """Query wiki replica for article counts grouped by language."""
        rows = self.lang_db.select_safe(_SQL_LANG_COUNTS)
        return {row["ll_lang"]: row["counts"] for row in rows}

    def _fetch_total_articles(self) -> int:
        """Query wiki replica for total medicine article count."""
        rows = self.lang_db.select_safe(_SQL_TOTAL_ARTICLES)
        if rows:
            return rows[0]["articles"]
        return 0

    def _build_wikitext(self, languages: dict[str, int]) -> str:
        """Build the wikitext for the stats page."""
        year = datetime.datetime.now().year
        month = datetime.datetime.now().month
        articles_all = self.result.summary.total_articles_all_langs

        text = "{{:WPM:WikiProject Medicine/Total medical articles}}\n"
        text += f"Numbers are as {month} {year}. There are {articles_all:,} medical articles across {len(languages)} languages.\n"
        text += '{| class="sortable wikitable"\n!Lang\n!#\n|-'

        for lang, count in languages.items():
            text += f"\n!{lang}\n|{count:,}\n|-"

        text += "\n|}"
        return text


__all__ = [
    "MedicineArticlesWorker",
]
