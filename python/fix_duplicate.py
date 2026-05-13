#!/usr/bin/python3
"""

"""
import logging
import sys
from .mdapi import GetPageText, page_put, post_s

logger = logging.getLogger(__name__)

# ---
offset = {1: 0}
# ---
for arg in sys.argv:
    arg, _, value = arg.partition(":")
    # ---
    if arg.lower() in ["offset", "-offset"] and value.isdigit():
        offset[1] = int(value)
# ---
from_to = {}


def fix_dup(From, To):
    """Treat one double redirect."""
    # ---
    if To in from_to:
        To = from_to[To]
    # ---
    newtext = f"#REDIRECT [[{To}]]"
    # ---
    oldtext = GetPageText(From)
    # ---
    sus = f"fix duplicate redirect to [[{To}]]"
    # ---
    if oldtext == newtext:
        logger.info("no changes.")
        return
    # ---
    page_put(oldtext=oldtext, newtext=newtext, summary=sus, title=From, returntrue=False, diff=True)


def main():
    logger.info("*<<red>> > :")
    # ---
    # python3 dup.py -page:Allopurinol
    # python3 dup.py -page:Activated_charcoal_\(medication\)
    # python3 dup.py -newpages:10
    # python dup.py -newpages:1000
    # python dup.py -newpages:20000
    # ---
    fop = {
        "action": "query",
        "format": "json",
        "prop": "info",
        "generator": "querypage",
        "redirects": 1,
        "utf8": 1,
        "gqppage": "DoubleRedirects",
        "gqplimit": "max",
    }
    # ---
    lista = post_s(fop)
    # ---
    redirects = lista.get("query", {}).get("redirects", [])
    # ---
    for gg in redirects:
        From = gg["from"]
        To = gg["to"]
        from_to[From] = To
    # ---
    for nu, title in enumerate(redirects, start=1):
        From = title["from"]
        logger.info(f'-------\n*<<yellow>> >{nu}/{len(redirects)} From:"{From}".')
        To = title["to"]
        if To in from_to:
            fix_dup(From, To)


if __name__ == "__main__":
    main()
