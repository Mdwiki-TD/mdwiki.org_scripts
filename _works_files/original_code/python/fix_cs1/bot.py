"""

python3 core8/pwb.py md_core/fix_cs1/bot nomwclient

tfj run fixcs --image python3.9 --command "$HOME/local/bin/python3 core8/pwb.py md_core/fix_cs1/bot"

"""

# import re
# import sys

import logging

from md_core.fix_cs1.fix_p import fix_it

# import wikitextparser as wtp
from mdwiki_api.mdwiki_page import CatDepth, md_MainPage

logger = logging.getLogger(__name__)


def one_page(title) -> None:
    # ---
    page = md_MainPage(title, "www", family="mdwiki")
    # ---
    text = page.get_text()
    # ---
    newtext = fix_it(text)
    # ---
    if text == newtext:
        return
    # ---
    page.save(newtext=newtext, summary="Fix missing periodical")


def main() -> None:
    # ---
    cat = "Category:CS1 errors: missing periodical"

    cat_members = CatDepth(cat, sitecode="www", family="mdwiki", depth=0, ns="all")

    for n, page in enumerate(cat_members):
        # ---
        logger.info(f"n: {n}/{len(cat_members)} - Page: {page}")
        one_page(page)


if __name__ == "__main__":
    main()
