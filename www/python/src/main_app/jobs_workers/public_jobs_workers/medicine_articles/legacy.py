#!/usr/bin/python3
"""
Create medicine_articles worker.py and objects.py
same style as in public_jobs_workers/create_redirects

read logic from medicine_articles/legacy.py
add it to the new worker.py

registre the new job in workers_list_public.py

"""

import datetime
from typing import Any

from ....api_services.mwclient_page import MwClientPage
from ....api_services import WikiSiteClient
from ....api_services.wikidb.analytics import WikiReplicaDB


def sql_result() -> dict[str, Any]:
    """
    Executes an SQL query to retrieve the count of page titles for each language in the 'Medicine' project. The function connects to the 'enwiki' database and returns a dictionary with language codes as keys and the corresponding counts as values.
    """
    query = """
    select ll_lang, count(page_title) as counts
        from page , langlinks , page_assessments , page_assessments_projects
        where pap_project_title = "Medicine"
        and pa_project_id = pap_project_id
        and pa_page_id = page_id
        and page_id = ll_from
        and page_is_redirect = 0
        and page_namespace = 0
        #and ll_lang = 'ar'
        group by ll_lang
        #limit 10
    """
    # ---
    lang_db = WikiReplicaDB("enwiki")
    result = lang_db.select_safe(query)
    # ---
    languages = {x["ll_lang"]: x["counts"] for x in result}
    # ---
    return languages


def get_articles():
    """
    Retrieves the number of articles related to the "Medicine" project from the database.

    Returns:
        int: The number of articles.
    """
    # ---
    query = """
    select count(pa_page_id) as articles
        from page, page_assessments , page_assessments_projects
        where pap_project_title = "Medicine"
        and pa_project_id = pap_project_id
        and pa_page_id = page_id
        and page_is_redirect = 0
        and page_namespace = 0
    """
    # ---
    lang_db = WikiReplicaDB("enwiki")
    result = lang_db.select_safe(query)
    # ---
    articles = [x["articles"] for x in result]
    # ---
    if articles:
        return articles[0]
    # ---
    return 0


def start() -> None:
    """
    This function generates a statistical report of the number of articles by language for the WikiProject Medicine. It retrieves the current year using the `datetime` module and constructs a title for the report. It then fetches the result of an SQL query using the `sql_result` function and obtains a list of articles using the `get_articles` function. If the language 'en' is not present in the `languages` dictionary, it adds the 'en' key with the corresponding number of articles.

    The function then constructs a text string with the title, current month and year, and the total number of articles across all languages. It appends a table header to the text string.

    Next, the `languages` dictionary is sorted in descending order based on the count of articles. The function iterates over the sorted dictionary and appends each language and its corresponding count to the text string.

    Finally, the function appends a table closing tag to the text string and uses the `md_MainPage` class to save the generated text as a new version of a wiki page. The page is saved with the specified title, update summary, and other optional parameters.

    This function does not take any parameters and does not return any values.
    """
    # year
    year = datetime.datetime.now().year
    # ---
    month = datetime.datetime.now().month
    # ---
    title = f"WikiProjectMed:WikiProject Medicine/Stats/Number of articles by language {year}"
    # ---
    languages = sql_result()
    # ---
    articles = get_articles()
    # ---
    if "en" not in languages:
        languages["en"] = articles
    # ---
    # count all languages values
    articles_all = sum(languages.values())
    # ---
    text = "{{:WPM:WikiProject Medicine/Total medical articles}}\n"
    # ---
    text += f"Numbers are as {month} {year}. There are {articles_all:,} medical articles across {len(languages)} languages.\n"
    text += """{| class="sortable wikitable"\n!Lang\n!#\n|-"""
    # ---
    # sort languages by count
    languages = dict(sorted(languages.items(), key=lambda item: item[1], reverse=True))
    # ---
    for lang, count in languages.items():
        text += f"\n!{lang}\n|{count:,}\n|-"
    # ---
    text += "\n|}"
    # ---
    site = WikiSiteClient().get_user_site("mdwiki.org", None)
    page = MwClientPage(title, site)

    page.edit(text, "update")


if __name__ == "__main__":
    start()
