""" """

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from ...shared_objects import Summary, UpdaterOutcome, WorkerMapping

logger = logging.getLogger(__name__)


@dataclass
class FindAndReplaceWorkerObject(WorkerMapping):
    text_find: str = ""
    text_replace: str = ""
    stopped: bool = False
    cap: int | None = None

    summary: Summary = field(default_factory=Summary)

    pages_processed: list[UpdaterOutcome] = field(default_factory=list)

    pages_changed: list[UpdaterOutcome] = field(default_factory=list)
    pages_errors: list[UpdaterOutcome] = field(default_factory=list)
    pages_skipped: list[UpdaterOutcome] = field(default_factory=list)

    pages_missing: list[UpdaterOutcome] = field(default_factory=list)


__all__ = [
    "FindAndReplaceWorkerObject",
]
