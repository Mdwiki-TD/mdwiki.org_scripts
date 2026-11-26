""" """

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Literal

from ....jobs.shared_objects import SharedMapToJson, SharedworkerObject, Summary

logger = logging.getLogger(__name__)


@dataclass
class ImportUpdaterOutcome(SharedMapToJson):
    """Result of running the updater on one page."""

    status: Literal["missing", "imported", "imported_fallback", "failed", "skipped", "completed", "pending"] = "pending"

    title: str = ""
    msg: str = ""
    newrevid: int = 0


@dataclass
class ImportHistoryWorkerObject(SharedworkerObject):
    from_lang: str = "en"

    summary: Summary = field(default_factory=Summary)

    pages_processed: list[ImportUpdaterOutcome] = field(default_factory=list)

    pages_imported: list[ImportUpdaterOutcome] = field(default_factory=list)
    pages_imported_fallback: list[ImportUpdaterOutcome] = field(default_factory=list)
    pages_failed: list[ImportUpdaterOutcome] = field(default_factory=list)
    pages_skipped: list[ImportUpdaterOutcome] = field(default_factory=list)

    pages_missing: list[ImportUpdaterOutcome] = field(default_factory=list)


__all__ = [
    "ImportHistoryWorkerObject",
    "ImportUpdaterOutcome",
]
