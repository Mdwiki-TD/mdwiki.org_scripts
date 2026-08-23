""" """

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any, Literal

logger = logging.getLogger(__name__)


@dataclass
class RedirectUpdaterOutcome:
    """Result of running the updater on one page."""

    status: Literal["pending", "missing", "changed", "error", "skipped", "completed"] = "pending"

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
