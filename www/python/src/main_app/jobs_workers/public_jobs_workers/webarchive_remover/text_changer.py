"""
Text transformation for the webarchive_remover job.

Removes (or merges) a ``{{Webarchive}}`` template that directly follows a
CS1/CS2 citation template in the same reference.

No network / site access, so it is easy to unit-test.

Reuses helpers from ``archive_today/shared_wtp.py`` where they overlap.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar, NamedTuple

import wikitextparser as wtp

from ..archive_today.shared_wtp import WtpUtils

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Data classes
# ----------------------------------------------------------------------


class Edit(NamedTuple):
    """A replacement of ``text[start:end]`` with ``replacement``."""

    start: int
    end: int
    replacement: str


@dataclass
class Stats:
    removed: int = 0
    merged: int = 0
    skipped: list[str] = field(default_factory=list)  # human-readable reasons

    @property
    def changed(self) -> bool:
        return bool(self.removed or self.merged)


@dataclass(frozen=True)
class ArchiveUrl:
    """A parsed Wayback Machine URL."""

    timestamp: str
    original: str  # original URL without scheme

    # https://web.archive.org/web/20220423164658/https://example.org/
    # also matches .../web/20220423164658id_/https://... and http:// variants
    _RE: ClassVar[re.Pattern[str]] = re.compile(
        r"^https?://(?:web\.)?archive\.org/web/(?P<ts>\d{4,14})(?P<mod>[a-z]{2}_)?/(?P<orig>.+)$",
        re.IGNORECASE,
    )

    @classmethod
    def parse(cls, url: str) -> ArchiveUrl | None:
        m = cls._RE.match(url.strip())
        if not m:
            return None
        return cls(timestamp=m.group("ts"), original=cls.strip_scheme(m.group("orig")))

    @staticmethod
    def strip_scheme(url: str) -> str:
        return re.sub(r"^https?:", "", url.strip(), flags=re.IGNORECASE).rstrip("/")

    @classmethod
    def same_snapshot(cls, url_a: str, url_b: str) -> bool:
        """True when both URLs point to the same snapshot of the same page."""
        a, b = cls.parse(url_a), cls.parse(url_b)
        if a and b:
            return a == b
        return cls.strip_scheme(url_a) == cls.strip_scheme(url_b)

    def formatted_date(self) -> str:
        """'20220423164658' -> '23 April 2022' (fallback when Webarchive has no date)."""
        try:
            return datetime.strptime(self.timestamp[:8], "%Y%m%d").strftime("%d %B %Y").lstrip("0")
        except ValueError:
            return ""


# ----------------------------------------------------------------------
# Main class
# ----------------------------------------------------------------------


class WebarchiveRemover:
    """
    Remove / merge redundant ``{{Webarchive}}`` templates.

    :param merge: when the citation has no archive-url, move the Webarchive data
        into it instead of skipping.
    :param default_url_status: value for ``url-status`` when merging and the
        citation has none (None = don't add it). CS1 treats a missing url-status
        as "dead" once archive-url is present, which changes how the citation
        renders, so the default is to not guess.

    Usage::

        remover = WebarchiveRemover()
        new_text, stats = remover.process(text)
    """

    # Normalized (lower-case, underscores -> spaces) Webarchive names and redirects.
    WEBARCHIVE_NAMES: ClassVar[frozenset[str]] = frozenset({"webarchive", "web archive", "wayback", "web-archive"})
    # Exact citation names besides the "cite *" family.
    CITE_EXTRA_NAMES: ClassVar[frozenset[str]] = frozenset({"citation"})

    # Parameter name aliases — reuse the same lists as archive_today/shared_wtp.py
    # via WtpUtils.get_arg_value for consistency.
    ARCHIVE_URL_PARAMS: ClassVar[list[str]] = ["archive-url", "archiveurl", "archive_url"]
    ARCHIVE_DATE_PARAMS: ClassVar[list[str]] = ["archive-date", "archivedate", "archive_date"]
    URL_PARAMS: ClassVar[list[str]] = ["url"]

    def __init__(self, merge: bool = True, default_url_status: str | None = None) -> None:
        self.merge = merge
        self.default_url_status = default_url_status

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, text: str) -> tuple[str, Stats]:
        """Return ``(new_text, stats)``."""
        stats = Stats()
        if not self._may_contain_webarchive(text):
            return text, stats

        templates = wtp.parse(text).templates
        cites_by_end = {t.span[1]: t for t in templates if self.is_cite(t)}
        webarchives = [t for t in templates if self.is_webarchive(t)]

        edits: list[Edit] = []
        for wa in webarchives:
            # Only top-level Webarchive templates (<ref> tags as ancestors are fine)
            if any(isinstance(a, wtp.Template) for a in wa.ancestors()):
                continue

            cite = self._find_preceding_cite(text, wa.span[0], cites_by_end)
            if cite is None:
                continue  # not attached to a citation: leave alone

            edit = self._handle_pair(cite, wa, stats)
            if edit:
                edits.append(edit)

        return self._apply_edits(text, edits), stats

    def remove(self, text: str) -> str:
        """Convenience: return only the new text."""
        return self.process(text)[0]

    # ------------------------------------------------------------------
    # Template detection / param helpers
    # ------------------------------------------------------------------

    @staticmethod
    def normalize_name(template: wtp.Template) -> str:
        return template.name.strip().replace("_", " ").lower()

    def is_webarchive(self, template: wtp.Template) -> bool:
        return self.normalize_name(template) in self.WEBARCHIVE_NAMES

    def is_cite(self, template: wtp.Template) -> bool:
        name = self.normalize_name(template)
        return name.startswith("cite ") or name in self.CITE_EXTRA_NAMES

    @staticmethod
    def get_param(template: wtp.Template, names: list[str]) -> str:
        """Return the stripped value of the first non-empty param among ``names``.

        Uses :meth:`WtpUtils.get_arg_value` from ``archive_today/shared_wtp.py``.
        """
        return WtpUtils.get_arg_value(template, names)

    # ------------------------------------------------------------------
    # Internal logic
    # ------------------------------------------------------------------

    @staticmethod
    def _may_contain_webarchive(text: str) -> bool:
        low = text.lower()
        return any(k in low for k in ("webarchive", "web archive", "wayback", "web-archive"))

    @staticmethod
    def _find_preceding_cite(
        text: str,
        wa_start: int,
        cites_by_end: dict[int, wtp.Template],
    ) -> wtp.Template | None:
        """Cite template ending right before ``wa_start`` (whitespace allowed between)."""
        pos = wa_start
        while pos > 0 and text[pos - 1].isspace():
            pos -= 1
        return cites_by_end.get(pos)

    def _handle_pair(self, cite: wtp.Template, wa: wtp.Template, stats: Stats) -> Edit | None:
        """Decide what to do with a (cite, Webarchive) pair; update ``stats``."""
        wa_url = self.get_param(wa, self.URL_PARAMS) or self.get_param(wa, ["1"])
        if not wa_url:
            stats.skipped.append("Webarchive without url")
            return None

        cite_archive_url = self.get_param(cite, self.ARCHIVE_URL_PARAMS)

        # Case 1: citation already has the same archive -> just drop Webarchive
        if cite_archive_url:
            if ArchiveUrl.same_snapshot(cite_archive_url, wa_url):
                stats.removed += 1
                return Edit(cite.span[1], wa.span[1], "")
            stats.skipped.append(f"different archive URLs: {cite_archive_url} vs {wa_url}")
            return None

        # Case 2: citation has no archive -> merge
        if not self.merge:
            stats.skipped.append("merge disabled")
            return None
        return self._merge_into_cite(cite, wa, wa_url, stats)

    def _merge_into_cite(self, cite: wtp.Template, wa: wtp.Template, wa_url: str, stats: Stats) -> Edit | None:
        cite_url = self.get_param(cite, self.URL_PARAMS)
        archive = ArchiveUrl.parse(wa_url)

        if not cite_url or archive is None:
            stats.skipped.append("cannot merge: missing url or not a Wayback URL")
            return None
        if ArchiveUrl.strip_scheme(cite_url) != archive.original:
            stats.skipped.append(f"Webarchive archives a different page: {wa_url}")
            return None

        new_cite = wtp.Template(str(cite))  # detached copy
        new_cite.set_arg("archive-url", wa_url)

        if not self.get_param(new_cite, self.ARCHIVE_DATE_PARAMS):
            date = self.get_param(wa, ["date"]) or archive.formatted_date()
            if date:
                new_cite.set_arg("archive-date", date)

        if self.default_url_status and not new_cite.has_arg("url-status"):
            new_cite.set_arg("url-status", self.default_url_status)

        stats.merged += 1
        return Edit(cite.span[0], wa.span[1], str(new_cite))

    @staticmethod
    def _apply_edits(text: str, edits: list[Edit]) -> str:
        """Apply edits back to front so earlier spans stay valid."""
        for start, end, replacement in sorted(edits, key=lambda e: e.start, reverse=True):
            text = text[:start] + replacement + text[end:]
        return text


def remove_webarchive(text: str) -> str:
    """Pure convenience wrapper: return only the transformed text."""
    return WebarchiveRemover().remove(text)


__all__ = [
    "ArchiveUrl",
    "Edit",
    "Stats",
    "WebarchiveRemover",
    "remove_webarchive",
]
