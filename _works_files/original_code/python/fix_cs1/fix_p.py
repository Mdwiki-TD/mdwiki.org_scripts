"""
python3 core8/pwb.py md_core/fix_cs1/bot

"""

import logging

import wikitextparser as wtp

from md_core.fix_cs1.bots.find_journal import get_journal_value, get_param
from md_core.fix_cs1.bots.temps_list import in_params_ar, in_params_en

logger = logging.getLogger(__name__)


def fix_one_temp(temp, find_params):
    # ---
    for param in find_params:
        va = get_param(temp, param)
        if va:
            # logger.info(f"** temp has |{param} = {va}")
            return temp
    # ---
    journal = get_journal_value(temp)
    # ---
    if journal:
        temp.set_arg("journal", journal)
    # else:
    # logger.info("Journal value not found for template.")
    # logger.info(temp)
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


def fix_it(text: str, site: str = ""):
    # ---
    ref_temps_n = ["cite journal", "cite magazine", "استشهاد بمجلة", "استشهاد بدورية محكمة"]
    # ---
    find_params = in_params_ar if site == "ar" else in_params_en
    # ---
    newtext = text
    # ---
    parsed = wtp.parse(text)
    # ---
    temps = get_temps(parsed, ref_temps_n)
    # ---
    for temp in temps:
        temp = fix_one_temp(temp, find_params)
    # ---
    newtext = parsed.string
    # ---
    return newtext
