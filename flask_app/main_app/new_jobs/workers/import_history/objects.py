""" """

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from ....new_jobs.base_worker_object import WorkerObject

logger = logging.getLogger(__name__)



@dataclass(frozen=True)
class UpdaterOutcome:
    """Result of running the updater on one page."""

    kind: Literal["missing", "imported", "imported_fallback", "error"]
    newrevid: int = 0
    msg: str = ""

    @property
    def has_changes(self) -> bool:
        return self.kind == "changed"

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Summary:
    scanned: int = 0
    total: int = 0


@dataclass
class ImportHistoryWorkerObject(WorkerObject):
    summary: Summary = field(default_factory=Summary)

    from_lang: str = "en"

    pages_processed: list[dict[str, Any]] = field(default_factory=list)

    pages_missing: list[str] = field(default_factory=list)

    pages_imported: list[dict[str, Any]] = field(default_factory=list)
    pages_imported_fallback: list[dict[str, Any]] = field(default_factory=list)
    pages_errors: list[dict[str, Any]] = field(default_factory=list)

__all__ = [
    "ImportHistoryWorkerObject",
    "UpdaterOutcome",
]
