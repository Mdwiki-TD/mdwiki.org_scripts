""" """

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any, Literal

logger = logging.getLogger(__name__)


@dataclass
class UpdaterTextOutcome:
    """Result of running the updater on one page."""

    status: Literal["notext", "skipped", "changes", "saved"]
    old_text: str = ""
    new_text: str = ""

    title: str = ""
    msg: str = ""
    newrevid: int = 0

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


__all__ = [
    "UpdaterTextOutcome",
]
