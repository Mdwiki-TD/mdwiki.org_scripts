"""Service: medical-content updater (synchronous).

In-process replacement for ``python/newupdater.py``. Unlike the other tools
this one is fast — a single page transform — so we run it inline on the
request thread instead of through the job runner.

The actual content-rewriting algorithm lives in ``new_updater``
(``med_updater_one``). We import it as-is because that module encodes years
of medical-content domain rules; reimplementing it is out of scope.
"""

from __future__ import annotations

import logging

from ..api_services import MwClientPage
from ..api_services.clients.wikisite_client import WikiSiteClient
from ..config import get_settings
from .auth.current_user import CurrentUser
from .named_param import NamedParamEditor
from .new_updater import med_updater_one
from .shared_classes import UpdaterTextOutcome

logger = logging.getLogger(__name__)


class NewUpdaterService:
    """Fetch a wiki page, run the medical content updater, and optionally save.

    Collaborators are injected via ``__init__`` for testability.
    """

    def __init__(
        self,
        named_param_editor: NamedParamEditor | None = None,
        wiki_site_client_cls: type[WikiSiteClient] | None = None,
        mw_client_page_cls: type[MwClientPage] | None = None,
    ) -> None:
        self.named_param_editor = named_param_editor or NamedParamEditor()
        self.wiki_site_client_cls = wiki_site_client_cls or WikiSiteClient
        self.mw_client_page_cls = mw_client_page_cls or MwClientPage

    def update_one(
        self,
        title: str,
        save: bool = False,
        summary: str = "Med updater.",
        user: CurrentUser | None = None,
    ) -> UpdaterTextOutcome:
        """Fetch the page, run the updater, and report what the diff would be."""
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
        if site is None:
            return UpdaterTextOutcome(status="skipped", msg="Failed to get site")

        page = self.mw_client_page_cls(title, site)
        old_text = page.get_text()

        if not old_text or not old_text.strip():
            return UpdaterTextOutcome(status="notext", old_text=old_text)

        try:
            new_text = med_updater_one(title, old_text)
            new_text = self.named_param_editor.add_param_named(new_text)
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

        return UpdaterTextOutcome(
            status="changes",
            old_text=old_text,
            new_text=new_text,
        )

__all__ = [
    "NewUpdaterService",
]
