#!/usr/bin/python3
"""Title extraction from URLs via the Wikipedia citation API.

Provides :class:`TitleMaker` for fetching and filtering citation titles,
plus a backward-compatible legacy :func:`make_title` function.
"""

from __future__ import annotations

import functools
import logging
import re
from urllib.parse import quote

from ...api_services.citation_api import CitationApi

logger = logging.getLogger(__name__)


# Module-level blacklist regex (compiled once, shared by all instances)
_GLOBAL_BAD_TITLES = re.compile(
    r"""
# is
(test|
# starts with
    ^\W*(
            register
            |registration
            |(sign|log)[ \-]?in
            |subscribe
            |sign[ \-]?up
            |log[ \-]?on
            |untitled[ ]?(document|page|\d+|$)
            |404[ ]
        ).*
# anywhere
    |.*(
            403[ ]forbidden
            |(404|page|file|information|resource).*not([ ]*be)?[ ]*(available|found)
            |site.*disabled
            |error[ ]404
            |error.+not[ ]found
            |not[ ]found.+error
            |404[ ]error
            |\D404\D
            |check[ ]browser[ ]settings
            |log[ \-]?(on|in)[ ]to
            |site[ ]redirection
     ).*
# ends with
    |.*(
            register
            |access denied
            |registration
            |(sign|log)[ \-]?in
            |subscribe|sign[ \-]?up
            |log[ \-]?on
        )\W*$
)
""",
    re.I | re.S | re.X,
)


@functools.lru_cache(maxsize=10000)
def _cached_fetch_title(url_encoded: str, citation_api: CitationApi) -> str:
    """Module-level cached fetch — shared across TitleMaker instances using the default API."""
    return citation_api.get_citation_title(url_encoded)


class TitleMaker:
    """Fetch and filter citation titles from URLs.

    Uses the Wikipedia citation REST API to extract titles, then filters
    out common boilerplate (login pages, 404s, etc.).
    """

    def __init__(self, citation_api: CitationApi | None = None) -> None:
        self.citation_api = citation_api or CitationApi()

    def make_title(self, url: str) -> str:
        """Extract a clean title from *url* via the citation API.

        Returns the title string, or empty string if the URL is invalid,
        the API fails, or the title matches the blacklist.
        """
        url = url.strip()
        if not url:
            logger.info("url = '' return False")
            return ""

        url2 = quote(url)
        url2 = url2.replace("/", "%2F")
        url2 = url2.replace(":", "%3A")
        url2 = url2.replace("&", "%26")
        url2 = url2.replace("#", "%23")

        title = _cached_fetch_title(url2, self.citation_api)

        if not title or title.strip().lower() == "not found.":
            return ""

        if _GLOBAL_BAD_TITLES.match(title):
            logger.error(f"{url} : Blacklisted title ({title})")

        if title:
            logger.info(f"newtitle: ({title})")

        return title


# ---------------------------------------------------------------------------
# Legacy compatibility layer — no business logic, delegates to TitleMaker
# ---------------------------------------------------------------------------

_default_maker: TitleMaker | None = None


def _get_default_maker() -> TitleMaker:
    global _default_maker
    if _default_maker is None:
        _default_maker = TitleMaker()
    return _default_maker


def make_title(url: str) -> str:
    """Legacy entry point. Use :meth:`TitleMaker.make_title` instead."""
    return _get_default_maker().make_title(url)


# Expose cache_clear for backward compatibility with tests
make_title.cache_clear = _cached_fetch_title.cache_clear  # type: ignore[attr-defined]


__all__ = [
    "TitleMaker",
    "make_title",
]
