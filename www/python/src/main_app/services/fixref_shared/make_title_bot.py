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
_GLOBAL_BAD_TITLES = r"""
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
"""


@functools.lru_cache(maxsize=10000)
def make_title(url: str) -> str:
    url = url.strip()
    if not url:
        logger.info("url = '' return False")
        return ""

    url2 = quote(url)
    url2 = url2.replace("/", "%2F")
    url2 = url2.replace(":", "%3A")
    url2 = url2.replace("&", "%26")
    url2 = url2.replace("#", "%23")

    title = CitationApi().get_citation_title(url2)

    if not title or title.strip().lower() == "not found.":
        return ""

    titleBlackList = re.compile(_GLOBAL_BAD_TITLES, re.I | re.S | re.X)
    if titleBlackList.match(title):
        logger.error(f"{url} : Blacklisted title ({title})")

    if title:
        logger.info(f"newtitle: ({title})")

    return title


__all__ = [
    "make_title",
]
