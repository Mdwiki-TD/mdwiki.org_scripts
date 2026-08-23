"""Domain DTOs shared across use-cases."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


@dataclass
class UpdaterTextOutcome:
    """Result of running a single-page content transform."""

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
