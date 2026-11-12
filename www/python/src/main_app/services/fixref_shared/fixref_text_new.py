"""Reference template normalization for wikitext.

Provides :class:`FixRefTextService` for normalizing ``<ref>`` templates
(lay-source extraction, title auto-fill), plus backward-compatible
legacy functions.
"""

from __future__ import annotations

import re
import sys
from typing import Any

import wikitextparser as wtp

from .make_title_bot import TitleMaker


def change_lay_source(temp: wtp.Template) -> tuple[str, Any]:
    """Extract lay-source parameters from *temp* into a ``{{lay source}}`` string."""
    temp_name = str(temp.normal_name()).strip()

    tab = {
        "url": ["layurl", "lay-url"],
        "title": ["laytitle", "lay-title"],
        "date": ["laydate", "lay-date"],
        "source": ["laysource", "lay-source"],
    }
    new_tab = {"url": "", "title": "", "date": "", "source": ""}

    for x, ys in tab.items():
        for param in ys:
            has_param = temp.get_arg(param)
            if has_param:
                val = has_param.value
                if val.strip() != "":
                    new_tab[x] = val.strip()
                temp.del_arg(param)

    title = new_tab["title"]
    url = new_tab["url"]
    date = new_tab["date"]
    source = new_tab["source"]

    if title == "" and url != "":
        title = TitleMaker().make_title(url)
        title = title.replace("|", "{{!}}")

    lay_temp = ""
    if url != "" or source != "":
        lay_temp = f"""|template = {temp_name}|url = {url}|title = {title}|date = {date}|website = {source}"""
        lay_temp = "* {{lay source" + lay_temp + "}}"

    return lay_temp, temp


def add_title(temp: wtp.Template) -> wtp.Template:
    """Auto-fill a missing ``title`` parameter from the ``url`` parameter."""
    title = ""
    url = ""

    title_arg = temp.get_arg("title")
    if title_arg:
        title = str(title_arg.value).strip()

    _url_param = temp.get_arg("url")
    if temp.has_arg("url") and _url_param:
        url = _url_param.value

    if title != "" or url == "":
        return temp

    title = TitleMaker().make_title(url)
    if not title:
        return temp

    title = title.replace("|", "{{!}}")

    if title_arg:
        title_arg.value = title
    else:
        temp.set_arg("title", title)

    return temp


def fix_ref_template(text: str, returnsummary: bool = False) -> str | tuple[str, str]:
    """Normalize ``<ref>`` templates in *text*.

    For each ``<ref>`` tag containing templates:
    - Extracts lay-source parameters into ``{{lay source}}``.
    - Auto-fills missing ``title`` from the URL.
    - Strips newlines from template text (unless ``newline`` is in sys.argv).

    Args:
        text: Wikitext to process.
        returnsummary: If True, return ``(newtext, summary)`` tuple.

    Returns:
        Processed wikitext, or ``(wikitext, summary)`` if *returnsummary*.
    """
    summary = "Normalize references"

    newtext = text

    parsed = wtp.parse(text)

    for tag in parsed.get_tags(name="ref"):
        content = tag.contents or ""

        if not content.strip():
            continue

        templates = tag.templates

        for temp in templates:
            temp_str = temp.string

            laysource, temp = change_lay_source(temp)
            temp = add_title(temp)

            temp_new = temp.string

            if "newline" not in sys.argv:
                temp_new = re.sub(r"\n", "", temp_new, flags=re.DOTALL)

            if laysource != "":
                temp_new = f"{temp_new}\n{laysource}"
                summary = "Normalize references, move lay source params"

            newtext = newtext.replace(temp_str, temp_new)

    return (newtext, summary) if returnsummary else newtext


__all__ = [
    "change_lay_source",
    "add_title",
    "fix_ref_template",
]
