"""Fix redirect links in wikitext.

Provides :class:`FixRedirectWorker` for resolving and replacing redirect
wikilinks in page text, plus backward-compatible legacy functions.
"""

from __future__ import annotations

import logging

import wikitextparser as wtp

from ...api_services.query_api import MediaWikiQueryService
from ..replace_wikilink import WikilinkReplacer
from .objects import RunState

logger = logging.getLogger(__name__)


class FixRedirectWorker:
    """Fix redirect links in wikitext by resolving them to their final targets.

    Uses :class:`MediaWikiQueryService` for API queries and
    :class:`WikilinkReplacer` for text replacement.
    """

    def __init__(
        self,
        query_service: MediaWikiQueryService,
    ) -> None:
        self.query_service = query_service

    @staticmethod
    def _replace_links(text: str, oldlink: str, newlink: str) -> str:
        """Replace wikilinks: ``[[old]]`` → ``[[new|old]]``, ``[[old|...]]`` → ``[[new|...]]``."""
        parsed = wtp.parse(text)
        for wl in parsed.wikilinks:
            if wl.title == oldlink:
                if wl.text is None:
                    wl.text = wl.target
                wl.title = newlink
        return str(parsed)

    @staticmethod
    def replace_in_text(text: str, new_targets: dict[str, str]) -> str:
        """Replace all redirect links in *text* using *new_targets* mapping."""
        newtext = text
        for oldlink, target in new_targets.items():
            newtext = WikilinkReplacer.replace_wikilink_redirects(newtext, oldlink, target)
        return newtext

    def work_on_text(self, title: str, text: str, state: RunState) -> str:
        """Fix redirect links in *text* for the given *title*.

        Queries the API for page links and their redirect resolutions,
        then replaces outdated links with their final targets.
        """
        links = self.query_service.get_page_links(title)

        for nor in links.get("normalized", []) or []:
            state.normalized[nor["to"]] = nor["from"]

        link_titles = list(links["links"].keys())
        if not link_titles:
            return text

        data = self.query_service.resolve_redirects(titles=link_titles)

        new_targets: dict[str, str] = {}

        for _, info in links["links"].items():
            oldlink = info["title"]
            oldlink2 = data.get("normalized", {}).get(oldlink) or oldlink
            target = data.get("from_to", {}).get(oldlink) or data.get("from_to", {}).get(oldlink2)
            if target:
                new_targets[oldlink2] = target
                new_targets[oldlink] = target

        newtext = self.replace_in_text(text, new_targets)
        return newtext


__all__ = [
    "FixRedirectWorker",
    "RunState",
]
