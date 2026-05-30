""" """

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def replace_redirect_link(text: str, redirect_to: str, final_target: str) -> str:
    # TODO: replace only the link not the whole text, use wikitextparser to analyze the text, then search in text for links to redirect_to then replace it to final_target
    new_text = f"#REDIRECT [[{final_target}]]"
    return new_text
