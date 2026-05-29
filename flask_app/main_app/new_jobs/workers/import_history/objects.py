""" """

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ....new_jobs.base_worker_object import WorkerObject

logger = logging.getLogger(__name__)


@dataclass
class Summary:
    scanned: int = 0
    total: int = 0


@dataclass
class ImportHistoryWorkerObject(WorkerObject):
    summary: Summary = field(default_factory=Summary)

    from_lang: str = "en"

    pages_processed: list[dict[str, Any]] = field(default_factory=list)
    pages_missing: list[dict[str, Any]] = field(default_factory=list)
    pages_no_revisions: list[dict[str, Any]] = field(default_factory=list)
    pages_imported: list[dict[str, Any]] = field(default_factory=list)
    pages_imported_fallback: list[dict[str, Any]] = field(default_factory=list)
    pages_error: list[dict[str, Any]] = field(default_factory=list)

__all__ = [
    "ImportHistoryWorkerObject",
]
