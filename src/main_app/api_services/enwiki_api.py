"""API client for English Wikipedia queries."""

from __future__ import annotations

import logging

from .clients.http_client import HttpClient

logger = logging.getLogger(__name__)


class EnwikiApi:
    def __init__(
        self,
        http_client: HttpClient | None = None,
    ) -> None:
        self.http_client = http_client or HttpClient(use_session=True)

    def get_redirects_for(self, title: str, *, timeout: int = 10) -> list[str]:
        """Fetch mainspace redirect titles pointing to *title* on enwiki.

        Args:
            title: The page title to look up redirects for.
            timeout: Request timeout in seconds.

        Returns:
            List of redirect titles (namespace 0 only).
        """
        params = {
            "action": "query",
            "format": "json",
            "prop": "redirects",
            "titles": title,
            "utf8": 1,
            "rdprop": "title",
            "rdlimit": "max",
        }
        try:
            response = self.http_client.post(
                "https://en.wikipedia.org/w/api.php",
                data=params,
                timeout=timeout,
            )
            response.raise_for_status()
            payload = response.json() or {}
        except Exception as e:
            logger.error("Error fetching redirects for %s: %s", title, e)
            return []

        pages = (payload.get("query") or {}).get("pages") or {}

        out: list[str] = []

        for page in pages.values():
            for r in page.get("redirects", []) or []:
                # if page.get("title") != title: continue
                if "ns" not in r:
                    continue

                ns = r["ns"]
                if ns != 0:
                    continue

                redirect_title = r.get("title", "")
                if redirect_title and redirect_title not in out:
                    out.append(redirect_title)
        return out


__all__ = [
    "EnwikiApi",
]
