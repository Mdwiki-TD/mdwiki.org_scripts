"""Domain DTOs shared across use-cases."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class UpdaterTextOutcome:
    """Result of running a single-page content transform."""

    kind: Literal["notext", "skipped", "changes", "saved"]
    old_text: str = ""
    new_text: str = ""
    newrevid: int = 0
    msg: str = ""

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


__all__ = [
    "UpdaterTextOutcome",
]
