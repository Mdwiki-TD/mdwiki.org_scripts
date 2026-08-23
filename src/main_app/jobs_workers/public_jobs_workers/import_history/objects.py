""" """

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from ...shared_objects import Summary, WorkerMapping

logger = logging.getLogger(__name__)


@dataclass
class ImportUpdaterOutcome:
    """Result of running the updater on one page."""

    status: Literal["missing", "imported", "imported_fallback", "error", "skipped", "completed", "pending"] = "pending"

    title: str = ""
    msg: str = ""
    newrevid: int = 0

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ImportHistoryWorkerObject(WorkerMapping):
    from_lang: str = "en"

    summary: Summary = field(default_factory=Summary)

    pages_processed: list[ImportUpdaterOutcome] = field(default_factory=list)

    pages_imported: list[ImportUpdaterOutcome] = field(default_factory=list)
    pages_imported_fallback: list[ImportUpdaterOutcome] = field(default_factory=list)
    pages_errors: list[ImportUpdaterOutcome] = field(default_factory=list)
    pages_skipped: list[ImportUpdaterOutcome] = field(default_factory=list)

    pages_missing: list[ImportUpdaterOutcome] = field(default_factory=list)


__all__ = [
    "ImportHistoryWorkerObject",
    "ImportUpdaterOutcome",
]
