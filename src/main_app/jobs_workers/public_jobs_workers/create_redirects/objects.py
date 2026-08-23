""" """

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any

from ...shared_objects import STATUS_LIST, WorkerMapping

logger = logging.getLogger(__name__)

@dataclass
class TitleCounts:
    target_missing: int = 0
    created: int = 0
    already_exists: int = 0
    skipped: int = 0
    errors: int = 0

@dataclass
class OneTitleInfo:
    title: str
    status: STATUS_LIST = "pending"
    error: str | None = None
    msg: str | None = None
    counts: TitleCounts = field(default_factory=TitleCounts)

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RedirectsSummary:
    processed: int = 0
    total: int = 0

    created: int = 0
    errors: int = 0
    skipped: int = 0

    already_exists: int = 0
    target_missing: int = 0

    def update_from_counts(self, data: TitleCounts) -> None:
        self.target_missing += data.target_missing
        self.created += data.created
        self.already_exists += data.already_exists
        self.skipped += data.skipped
        self.errors += data.errors


@dataclass
class CreateRedirectsWorkerObject(WorkerMapping):
    summary: RedirectsSummary = field(default_factory=RedirectsSummary)

    pages_processed: list[OneTitleInfo] = field(default_factory=list)

    pages_created: list[OneTitleInfo] = field(default_factory=list)
    pages_errors: list[OneTitleInfo] = field(default_factory=list)
    pages_skipped: list[OneTitleInfo] = field(default_factory=list)


__all__ = [
    "RedirectsSummary",
    "CreateRedirectsWorkerObject",
]
