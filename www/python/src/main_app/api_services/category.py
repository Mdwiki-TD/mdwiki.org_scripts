"""Category member queries via MediaWiki API.

Legacy compatibility module — delegates to :class:`MediaWikiQueryService`.
"""

from __future__ import annotations

import logging

import mwclient
import mwclient.errors
from mwclient.client import Site

from .query_api import MediaWikiQueryService

logger = logging.getLogger(__name__)


def get_category_members(
    site: Site,
    category_title: str,
    namespace: int = 0,
    limit: int | str | None = None,
) -> list[str]:
    """Legacy entry point. Use :meth:`MediaWikiQueryService.get_category_members` instead."""
    return MediaWikiQueryService(site=site).get_category_members(category_title, namespace, limit)


__all__ = [
    "get_category_members",
]
