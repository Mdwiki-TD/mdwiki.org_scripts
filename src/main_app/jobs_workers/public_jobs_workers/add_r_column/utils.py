#!/usr/bin/python3
""" """

import logging

logger = logging.getLogger(__name__)


def fix_title(title: str) -> str:
    title = title.replace("[[", "").replace("]]", "")
    title = title.replace("&#039;", "'")
    title = title.split("|")[0]
    title = title.split("#")[0]
    return title.strip()


__all__ = [
    "fix_title",
]
