"""Application service: fix redirects on a single page.

Orchestrates infrastructure (MediaWiki client) + pure domain transform.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, Protocol

from ...domain.shared_classes import UpdaterTextOutcome

logger = logging.getLogger(__name__)


class WikiPagePort(Protocol):
    """Port for loading / editing a wiki page (implemented by MwClientPage)."""

    def get_text(self) -> str: ...
    def edit(self, text: str, summary: str) -> dict[str, Any]: ...


class SiteFactory(Protocol):
    def __call__(self, user_payload: dict[str, Any] | None) -> Any: ...


class FixRedirectsService:
    """Use-case: load page → run redirect fixer → optionally save."""

    def __init__(
        self,
        *,
        site_factory: SiteFactory,
        page_factory: Callable[[str, Any], WikiPagePort],
        work_on_text: Callable[..., str],
        run_state_factory: Callable[[], Any],
    ) -> None:
        self._site_factory = site_factory
        self._page_factory = page_factory
        self._work_on_text = work_on_text
        self._run_state_factory = run_state_factory

    def run(
        self,
        title: str,
        *,
        save: bool = False,
        summary: str = "Fix redirects.",
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

        state = self._run_state_factory()
        try:
            new_text = self._work_on_text(title, old_text, site, state)
        except Exception:
            logger.exception("work_on_text failed for %s", title)
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
    "FixRedirectsService",
    "WikiPagePort",
    "SiteFactory",
]
