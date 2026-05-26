"""Low-level Wikimedia Commons download utilities.

This module provides the core HTTP download functionality for fetching
files from Wikimedia Commons. It serves as the foundation for higher-level
download functions used across the application.
"""

from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)


def create_commons_session(user_agent: str | None = None) -> requests.Session:
    """Create a pre-configured requests Session for Commons API calls.

    Args:
        user_agent: Optional custom User-Agent string. If not provided,
            defaults to a generic bot identifier.

    Returns:
        Configured requests Session ready for use.
    """
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": user_agent or "SVGTranslateBot/1.0",
        }
    )
    return session


__all__ = [
    "create_commons_session",
]
