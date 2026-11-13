""" """

from __future__ import annotations

from dataclasses import dataclass

from ...shared_objects import UpdaterOutcome


@dataclass
class RedirectUpdaterOutcome(UpdaterOutcome):
    """Result of running the updater on one page."""

    redirect_to: str | None = None
    final_target: str | None = None


__all__ = [
    "RedirectUpdaterOutcome",
]
