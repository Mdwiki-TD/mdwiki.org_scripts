"""
from cite.archive_bots.archive_date_maker import make_archive_date_and_url, make_archive_date
# found_it, archivedate, url, archiveurl = make_archive_date_and_url(archiveurl)
# archive_date = make_archive_date(archiveurl)
"""

import logging
import re

logger = logging.getLogger(__name__)


# Wayback Machine format
##r"^https?://web\.archive\.org/web/(\d{4})(\d{2})(\d{2})\d*/(https?://.+)$",
# archive.today/ph format with optional separators
##r"^https?://archive\.\w+/(\d{4})[-.]?(\d{2})[-.]?(\d{2})(?:[-\d.]+)?/(https?://.+)$",

matches = [
    r"^https*\:\/\/web\.archive\.org\/web\/(\d\d\d\d)(\d\d)(\d\d)\d*\/(http.*?)$",
    r"^https*\:\/\/archive\.\w+\/(\d\d\d\d)\.*(\d\d)\.*(\d\d)-*\d+\/(.*?)$",
    r"^https*\:\/\/archive\.\w+\/(\d\d\d\d)[-\.](\d\d)[-\.](\d\d)\/(.*?)?$",
    r"^https*\:\/\/archive\.\w+\/(\d\d\d\d)[-\.]*(\d\d)[-\.]*(\d\d)\/(.*?)?$",
    r"^https*\:\/\/archive\.\w+\/(\d\d\d\d)[-\.]*(\d\d)[-\.]*(\d\d)[-\d\.]+\/(.*?)?$",
]


def make_archive_date(archiveurl):
    # ---
    archivedate = ""
    # ---
    # logger.info(f"make_archive_date: {archiveurl=}")
    # ---
    # http://archive.today/2024.05.23-204959/
    # ---
    if not archiveurl:
        return archivedate
    # ---
    for x in matches:
        matche = re.match(x, archiveurl.strip(), flags=re.IGNORECASE)
        # ---
        if matche:
            archivedate = matche.group(1) + "-" + matche.group(2) + "-" + matche.group(3)
            break
    # ---
    return archivedate


def make_archive_date_and_url(archiveurl):
    # ---
    archivedate = ""
    url = ""
    # ---
    # ---
    # logger.info(f"make_archive_date: {archiveurl=}")
    # ---
    # http://archive.today/2024.05.23-204959/
    # ---
    found_it = False
    # ---
    if not archiveurl:
        return found_it, archivedate, url, archiveurl
    # ---
    for x in matches:
        matche = re.match(x, archiveurl.strip(), flags=re.IGNORECASE)
        # ---
        if matche:
            found_it = True
            # logger.info("found_it = True")
            archivedate = matche.group(1) + "-" + matche.group(2) + "-" + matche.group(3)
            url = matche.group(4)
            break
    # ---
    return found_it, archivedate, url, archiveurl
