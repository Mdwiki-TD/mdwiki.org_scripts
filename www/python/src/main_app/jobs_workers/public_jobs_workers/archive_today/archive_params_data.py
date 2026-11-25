from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class ArchiveParamsUrlsData:
    """Archive parameters and URL data for archive link handling."""

    ARCHIVEIS_SITES = [
        "archive.fo",
        "archive.is",
        "archive.li",
        "archive.md",
        "archive.ph",
        "archive.today",
        "archive.vn",
    ]

    TITLES_PARAMS = [
        "script-title",
        "ScriptTitle",
        "title",
        # "العنوان",
        # "عنوان أجنبي",
        # "عنوان",
    ]

    TITLE_PARAMS = [
        "title",
        # "العنوان",
        # "عنوان",
    ]

    URL_PARAMS = [
        "url",
        # "المسار",
        # "مسار",
        # "وصلة",
    ]

    ARCHIVE_PARAMS = [
        "archive-url",
        "archive_url",
        "archiveurl",
        # "مسار أرشيف",
        # "مسار الأرشيف",
        # "مسار-أرشيف",
        # "مسار-الأرشيف",
    ]

    URL_STATUS_PARAMS = [
        "url status",
        "url-status",
        "urlstatus",
        # "حالة المسار",
        # "حالة مسار",
    ]
    ACCESSDATE_PARAMS = [
        "accessDate",
        # "تاريخ الوصول",
        "accessdate",
        "access-date",
        # "تاريخ وصول",
    ]
    ARCHIVEDATE_PARAMS = [
        "archive-date",
        "archive_date",
        "archivedate",
        # "تاريخ أرشيف",
        # "تاريخ الأرشيف",
        # "تاريخ-أرشيف",
        # "تاريخ-الأرشيف",
    ]

    DEAD_URL_PARAMS = [
        # "وصلة مكسورة",
        "dead-url",
        "deadurl",
        # "رابط معطوب",
        # "وصلة ميتة",
    ]

    DEAD_URL_DATE_PARAMS = [
        # "تاريخ وصلة مكسورة",
        "dead-date",
        "deaddate",
    ]

    DEFAULT_TEMPLATE_NAMES = ("webarchive", "web-archive")

    def _build_start_patterns(self, domains: list[str] | None = None) -> tuple[str, ...]:
        """Build e.g. ``https://archive.today`` and ``http://archive.today``."""
        domains = domains or self.ARCHIVEIS_SITES

        patterns: list[str] = []
        for domain in domains:
            patterns.append(f"https://{domain}")
            patterns.append(f"http://{domain}")
        return tuple(patterns)

    def _is_archiveis_url(self, url: str) -> bool:
        return any(url.startswith((f"https://{site}", f"http://{site}")) for site in self.ARCHIVEIS_SITES)


__all__ = [
    "ArchiveParamsUrlsData",
]
