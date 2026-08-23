""" """

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from ...shared_objects import OUTCOME_STATUS


@dataclass
class RedirectUpdaterOutcome:
    """Result of running the updater on one page."""

    status: OUTCOME_STATUS = "pending"
    title: str = ""
    msg: str = ""
    newrevid: int = 0

    redirect_to: str | None = None
    final_target: str | None = None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


__all__ = [
    "RedirectUpdaterOutcome",
]
