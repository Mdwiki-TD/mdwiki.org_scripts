"""Wikilink redirect replacement utilities.

Provides :class:`WikilinkReplacer` for updating wikilinks in wikitext
to follow redirects, plus backward-compatible legacy functions.
"""

from __future__ import annotations

import logging

import wikitextparser as wtp

logger = logging.getLogger(__name__)


class WikilinkReplacer:
    """Replaces wikilink destinations in wikitext to follow redirects.

    All methods are static — this is a namespace class for pure text
    transformations with no external dependencies.
    """

    @staticmethod
    def _normalize_mediawiki_title(title: str) -> str:
        """Normalize a MediaWiki page title for accurate comparison.
        Handles spaces, underscores, and first-letter capitalization.
        """
        if not title:
            return title

        # Strip whitespaces and treat underscores as spaces
        title = title.strip().replace("_", " ")

        # Capitalize only the first character (MediaWiki standard)
        if title:
            title = title[0].upper() + title[1:]

        return title

    @classmethod
    def _replace_wikilinks(
        cls,
        text: str,
        redirect_to: str,
        final_target: str,
        set_text: bool = False,
    ) -> str:
        """Parse wikitext and update links pointing to *redirect_to* → *final_target*.

        Default (set_text=False):
            - ``[[old]]`` becomes ``[[new]]``.
            - ``[[old|...]]`` becomes ``[[new|...]]``.

        With set_text=True:
            - ``[[old]]`` becomes ``[[new|old]]`` (preserve original display text).
        """
        parsed_text = wtp.parse(text)

        # Normalize the target we are searching for
        normalized_redirect = cls._normalize_mediawiki_title(redirect_to)

        for link in parsed_text.wikilinks:
            # Use native 'title' property instead of manually splitting the target
            if link.title is None:
                continue

            normalized_title = cls._normalize_mediawiki_title(link.title)

            # Compare the normalized titles
            if normalized_title == normalized_redirect:
                # Updating link.title automatically preserves link.fragment and link.text
                old_target = link.target
                old_title = link.title
                link.title = final_target

                if set_text and not link.text:
                    # preserve the original display text
                    link.text = old_target

                logger.debug(f"Replaced link title '{old_title}' with '{final_target}'")
        # Return the updated wikitext as a string
        return parsed_text.string

    @classmethod
    def replace_wikilink_destinations(
        cls,
        text: str,
        redirect_to: str,
        final_target: str,
    ) -> str:
        """Replace wikilinks pointing to *redirect_to* so they point to *final_target*.

        Preserves fragments and display text. ``[[old]]`` → ``[[new]]``,
        ``[[old|...]]`` → ``[[new|...]]``.
        """
        return cls._replace_wikilinks(
            text,
            redirect_to,
            final_target,
        )

    @classmethod
    def replace_wikilink_redirects(
        cls,
        text: str,
        redirect_to: str,
        final_target: str,
    ) -> str:
        """Replace wikilinks following redirects, preserving original display text.

        ``[[old]]`` → ``[[new|old]]``, ``[[old|...]]`` → ``[[new|...]]``.
        """
        return cls._replace_wikilinks(
            text,
            redirect_to,
            final_target,
            set_text=True,
        )


__all__ = [
    "WikilinkReplacer",
]
