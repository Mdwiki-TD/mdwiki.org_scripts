"""Application service: medical-content updater for a single page."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, Protocol

from ...domain.shared_classes import UpdaterTextOutcome

logger = logging.getLogger(__name__)


class WikiPagePort(Protocol):
    def get_text(self) -> str: ...
    def edit(self, text: str, summary: str) -> dict[str, Any]: ...


class SiteFactory(Protocol):
    def __call__(self, user_payload: dict[str, Any] | None) -> Any: ...


class MedicalUpdaterService:
    """Use-case: load page → run medical updater pipeline → optionally save."""

    def __init__(
        self,
        *,
        site_factory: SiteFactory,
        page_factory: Callable[[str, Any], WikiPagePort],
        med_updater_one: Callable[[str, str], str],
        add_param_named: Callable[[str], str],
    ) -> None:
        self._site_factory = site_factory
        self._page_factory = page_factory
        self._med_updater_one = med_updater_one
        self._add_param_named = add_param_named

    def run(
        self,
        title: str,
        *,
        save: bool = False,
        summary: str = "Med updater.",
        user_payload: dict[str, Any] | None = None,
    ) -> UpdaterTextOutcome:
        title = (title or "").strip()
        if not title:
            return UpdaterTextOutcome(kind="skipped", msg="Invalid title")
        if user_payload is None:
            return UpdaterTextOutcome(kind="skipped", msg="No user")

        site = self._site_factory(user_payload)
        if site is None:
            return UpdaterTextOutcome(kind="skipped", msg="Failed to get site")

        page = self._page_factory(title, site)
        old_text = page.get_text()

        if not old_text or not old_text.strip():
            return UpdaterTextOutcome(kind="notext", old_text=old_text or "")

        try:
            new_text = self._med_updater_one(title, old_text)
            new_text = self._add_param_named(new_text)
        except Exception:
            logger.exception("medical updater failed for %s", title)
            raise

        if not new_text or not new_text.strip():
            return UpdaterTextOutcome(kind="notext", old_text=old_text)

        if new_text == old_text:
            return UpdaterTextOutcome(kind="skipped", msg="No changes")

        if save:
            result = page.edit(new_text, summary)
            if result.get("success"):
                return UpdaterTextOutcome(
                    kind="saved",
                    newrevid=int(result.get("newrevid") or 0),
                )

        return UpdaterTextOutcome(
            kind="changes",
            old_text=old_text,
            new_text=new_text,
        )


__all__ = [
    "MedicalUpdaterService",
]
