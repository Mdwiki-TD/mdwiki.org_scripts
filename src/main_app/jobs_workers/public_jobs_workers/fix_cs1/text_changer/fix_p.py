"""

<ref name=Stat2022>{{cite journal |last1=Lotterman |first1=S |last2=Sohal |first2=M |title=Ear Foreign Body Removal |date=January 2022 |pmid=29083719}}</ref>

Can you build a tool that finds all of these, checks the PMID, here

https://pubmed.ncbi.nlm.nih.gov/29083719/

Verifies that it is StatPearls and if so adds "|journal=StatPearls" to the template. Let me know if that makes sense.


"""

import logging

import wikitextparser as wtp

from .pmid import pmid_journal

in_params_en = [
    "journal",
    "magazine",
    "newspaper",
    "periodical",
    "website",
    "work",
    # "nespaper",
    # "newpaper",
    # "news",
    # "news-paper",
    # "site",
]

logger = logging.getLogger(__name__)


def get_param(temp, arg):
    va = temp.get_arg(arg) or temp.get_arg(arg.lower())
    # ---
    if va and va.value and va.value.strip():
        do = va.value.strip()
        return do
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


def fix_one_temp(temp: wtp.Template) -> wtp.Template:
    # ---
    for param in in_params_en:
        va = get_param(temp, param)
        if va:
            return temp
    # ---
    journal = get_journal_value(temp)
    # ---
    if journal:
        temp.set_arg("journal", journal)
    # ---
    return temp


def get_temps(parsed, valid_list):
    # ---
    Template_list = []
    # ---
    for tempa in parsed.templates:
        # ---
        temp_str = tempa.string
        # ---
        if not temp_str or temp_str.strip() == "":
            continue
        # ---
        name = str(tempa.normal_name()).strip()
        # ---
        if name.lower() not in valid_list:
            continue
        # ---
        Template_list.append(tempa)
    # ---
    logger.info(f"** result totall reftemps is: {len(Template_list)} ")
    # ---
    return Template_list


def fix_it(text: str) -> str:
    # ---
    ref_temps_n = ["cite journal", "cite magazine"]
    # ---
    newtext = text
    # ---
    parsed = wtp.parse(text)
    # ---
    temps = get_temps(parsed, ref_temps_n)
    # ---
    for temp in temps:
        temp = fix_one_temp(temp)
    # ---
    newtext = parsed.string
    # ---
    return newtext
