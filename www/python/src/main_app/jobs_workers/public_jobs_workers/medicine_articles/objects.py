""" """

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from ....jobs.shared_objects import STATUS_LITERAL, SharedMapToJson, SharedworkerObject, Summary

logger = logging.getLogger(__name__)


@dataclass
class LangCount(SharedMapToJson):
    lang: str
    count: int = 0
    status: STATUS_LITERAL = "pending"
    error: str | None = None


@dataclass
class MedicineArticlesSummary(Summary):
    total_articles: int = 0
    total_articles_all_langs: int = 0
    total_languages: int = 0
    page_updated: bool = False


@dataclass
class MedicineArticlesWorkerObject(SharedworkerObject):
    summary: MedicineArticlesSummary = field(default_factory=MedicineArticlesSummary)

    languages: list[LangCount] = field(default_factory=list)

    page_title: str = ""
    page_url: str = ""


__all__ = [
    "LangCount",
    "MedicineArticlesSummary",
    "MedicineArticlesWorkerObject",
]
