"""
<ref name=Stat2022>{{cite journal |last1=Lotterman |first1=S |last2=Sohal |first2=M |title=Ear Foreign Body Removal |date=January 2022 |pmid=29083719}}</ref>

Can you build a tool that finds all of these, checks the PMID, here

https://pubmed.ncbi.nlm.nih.gov/29083719/

Verifies that it is StatPearls and if so adds "|journal=StatPearls" to the template. Let me know if that makes sense.

"""

# import re
# import sys
# import wikitextparser as wtp
import logging

from md_core.fix_cs1.bots.pmid import pmid_journal

logger = logging.getLogger(__name__)


def get_param(temp, arg):
    va = temp.get_arg(arg) or temp.get_arg(arg.lower())
    # ---
    if va and va.value and va.value.strip():
        do = va.value.strip()
        return do
    # else:
    # logger.info(f"Parameter {arg} not found in template.")
    # ---
    return ""


def get_journal_value(temp):
    # ---
    journal = ""
    # ---
    to_do_params = [
        "pmid",
        "doi",
        "jfm",
        "jstor",
        "lccn",
        "دوي",
    ]
    # ---
    for param in to_do_params:
        va = get_param(temp, param)
        if not va:
            continue
        # ---
        # logger.info(f"** temp has |{param} = {va}")
        journal = pmid_journal(va, param)
        # ---
        if journal:
            break
    # ---
    return journal
