""" """

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from ....jobs.shared_objects import STATUS_LITERAL, SharedMapToJson, SharedworkerObject

logger = logging.getLogger(__name__)


@dataclass
class TitleCounts:
    target_missing: int = 0
    created: int = 0
    already_exists: int = 0
    skipped: int = 0
    errors: int = 0


@dataclass
class OneTitleInfo(SharedMapToJson):
    title: str
    status: STATUS_LITERAL = "pending"
    error: str | None = None
    msg: str | None = None
    counts: TitleCounts = field(default_factory=TitleCounts)


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
class CreateRedirectsWorkerObject(SharedworkerObject):
    summary: RedirectsSummary = field(default_factory=RedirectsSummary)

    pages_processed: list[OneTitleInfo] = field(default_factory=list)

    pages_created: list[OneTitleInfo] = field(default_factory=list)
    pages_failed: list[OneTitleInfo] = field(default_factory=list)
    pages_skipped: list[OneTitleInfo] = field(default_factory=list)


__all__ = [
    "RedirectsSummary",
    "CreateRedirectsWorkerObject",
]
