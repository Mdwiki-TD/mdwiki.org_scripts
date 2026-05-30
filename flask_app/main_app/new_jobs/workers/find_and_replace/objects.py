""" """

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from ....new_jobs.base_worker_object import WorkerObject

logger = logging.getLogger(__name__)


@dataclass
class Summary:
    scanned: int = 0
    total: int = 0

    changed: int = 0
    errors: int = 0
    skipped: Optional[int] = 0

    no_changes: int = 0
    missing: int = 0


@dataclass
class FindAndReplaceWorkerObject(WorkerObject):
    text_find: str = ""
    text_replace: str = ""
    stopped: bool = False
    cap: Optional[int] = None

    summary: Summary = field(default_factory=Summary)

    pages_processed: list[dict[str, Any]] = field(default_factory=list)

    pages_changed: list[dict[str, Any]] = field(default_factory=list)
    pages_errors: list[dict[str, Any]] = field(default_factory=list)
    pages_skipped: list[dict[str, Any]] = field(default_factory=list)

    pages_no_changes: list[str] = field(default_factory=list)
    pages_missing: list[str] = field(default_factory=list)


__all__ = [
    "FindAndReplaceWorkerObject",
]
