"""Service: fix redirects in a single page on mdwiki.

Provides :class:`FixRedOneService` for fetching a page, fixing redirect
links, and optionally saving the result, plus a backward-compatible
legacy function.
"""

from __future__ import annotations

import logging

from ...api_services import MwClientPage
from ...api_services.clients.wikisite_client import WikiSiteClient
from ...config import get_settings
from ...services.auth.current_user import CurrentUser
from ...services.fixref_shared.fixred_worker import FixRedirectWorker
from ...services.fixref_shared.objects import RunState
from ...services.shared_classes import UpdaterTextOutcome

logger = logging.getLogger(__name__)


class FixRedOneService:
    """Fix redirect links in a single wiki page.

    Orchestrates site creation, page fetching, redirect resolution,
    and optional saving.
    """

    def __init__(
        self,
        fix_redirect_worker_cls: type[FixRedirectWorker] | None = None,
        wiki_site_client_cls: type[WikiSiteClient] | None = None,
        mw_client_page_cls: type[MwClientPage] | None = None,
    ) -> None:
        self.fix_redirect_worker_cls = fix_redirect_worker_cls or FixRedirectWorker
        self.wiki_site_client_cls = wiki_site_client_cls or WikiSiteClient
        self.mw_client_page_cls = mw_client_page_cls or MwClientPage

    def work_on_title(
        self,
        title: str,
        save: bool = False,
        summary: str = "Fix redirects.",
        user: CurrentUser | None = None,
    ) -> UpdaterTextOutcome:
        """Fetch the page, fix redirect links, and report the diff."""
        title = (title or "").strip()
        if not title:
            return UpdaterTextOutcome(status="skipped", msg="Invalid title")

        if user is None:
            return UpdaterTextOutcome(status="skipped", msg="No user")

        app_settings = get_settings()
        site = self.wiki_site_client_cls.get_user_site(
            app_settings.other.wiki_domain,
            user.to_auth_payload(),
        )

        page = self.mw_client_page_cls(title, site)
        old_text = page.get_text()

        if not old_text or not old_text.strip():
            return UpdaterTextOutcome(status="notext", old_text=old_text)

        state = RunState()
        worker = self.fix_redirect_worker_cls(site=site)
        try:
            new_text = worker.work_on_text(title, old_text, state)
        except Exception:
            logger.exception("work_on_text failed for %s", title)
            raise

        if not new_text or not new_text.strip():
            return UpdaterTextOutcome(status="notext", old_text=old_text)

        if new_text == old_text:
            return UpdaterTextOutcome(status="skipped", msg="No changes")

        if save:
            result = page.edit(new_text, summary)
            if result.get("success"):
                return UpdaterTextOutcome(status="saved", newrevid=result.get("newrevid", 0))

        return UpdaterTextOutcome(status="changes", old_text=old_text, new_text=new_text)


# ---------------------------------------------------------------------------
# Legacy compatibility layer — no business logic, delegates to FixRedOneService
# ---------------------------------------------------------------------------

_default_service: FixRedOneService | None = None


def _get_default_service() -> FixRedOneService:
    global _default_service
    if _default_service is None:
        _default_service = FixRedOneService()
    return _default_service


def work_on_title(
    title: str,
    save: bool = False,
    summary: str = "Fix redirects.",
    user: CurrentUser | None = None,
) -> UpdaterTextOutcome:
    """Legacy entry point. Use :meth:`FixRedOneService.work_on_title` instead."""
    return _get_default_service().work_on_title(title, save, summary, user)


__all__ = [
    "FixRedOneService",
    "work_on_title",
]
