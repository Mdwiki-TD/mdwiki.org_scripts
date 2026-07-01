#!/usr/bin/python3
""" """

import logging
from typing import Any

import wikitextparser as wtp
from wikitextparser._cell import Cell

logger = logging.getLogger(__name__)

R_NEW_ROW = '\n| style="text-align:center; white-space:nowrap; font-weight:bold; background:#C66A05" | R'


def fix_title(title):
    title = title.replace("[[", "").replace("]]", "")
    title = title.replace("&#039;", "'")

    return title


def header_has_r(text: str, table: wtp.Table | bool = False) -> bool:
    if not table:
        parsed = wtp.parse(text)
        table = parsed.tables[0]

    # for table in parsed.tables:

    for x in table.cells():  # type: ignore
        if x[1].is_header:
            for numb, v in enumerate(x, 1):
                if v.value.strip() == "R":
                    logger.info(f"header has R: in column {numb}")
                    return True

    return False


def _build_header_index(all_rows: list[list[Cell]]) -> dict[str, int]:
    """
    Build a mapping of header text -> column index.
    """
    header_index: dict[str, int] = {}
    for row in all_rows:
        if not row or row[0] is None or not row[0].is_header:
            continue
        for idx, cell in enumerate(row):
            if cell is None:
                continue
            header_index[cell.value.strip()] = idx
        break
    return header_index


def add_header_r(text: str, table: wtp.Table | bool = False) -> str:
    if not table:
        parsed = wtp.parse(text)
        table = parsed.tables[0]

    if not table:
        return ""

    # for table in parsed.tables:

    # Check if R column already exists
    if header_has_r(text, table):
        logger.info("R column already exists in table header")
        return table.string  # type: ignore

    count = 0

    # add R to header in 2nd column
    for x in table.cells():  # type: ignore
        if x[0].is_header:
            x[0].value = x[0].value + "\n! R"
        else:
            x[0].value = x[0].value + "\n| "

        count += 1

    logger.info(f"Added R column to table header in {count} cells")

    return table.string  # type: ignore

def work_one_table(
    table_text: str,
    redirects: dict,
    pages: set,
) -> str:
    parsed = wtp.parse(table_text)
    table = parsed.tables[0]

    if not header_has_r(table_text, table):
        logger.info("<<red>> no R in table header!")
        return table_text

    already_in: list[Any] = []
    no_add: list[Any] = []

    add_from_redirect: list[Any] = []
    add_done: list[Any] = []

    cell_errors: list[Any] = []

    all_rows = table.cells()
    if not all_rows:
        return table.string

    # 1. Map header text to its column index
    header_index = _build_header_index(all_rows)

    data = table.data()

    for n, x in enumerate(all_rows):
        if x[1].is_header or len(x) < 3:
            continue

        try:
            title = x[2].value.strip()
            r_s = x[1].value.strip()
        except Exception:
            logger.warning(f"cell error: {n}")
            numb = data[n][2]
            cell_errors.append(numb)
            continue

        title = fix_title(title)
        title2 = redirects.get(title, title)

        if r_s == "R":
            x[1].string = R_NEW_ROW

            already_in.append(title)
            continue

        if title in pages:
            x[1].string = R_NEW_ROW

            add_done.append(title)
        elif title2 in pages:
            x[1].string = R_NEW_ROW
            add_from_redirect.append(title)
        else:
            no_add.append(title)

    logger.info(f"<<yellow>> no_add: {len(no_add)}, already_in: {len(already_in)}")

    logger.error(f"<<red>> cell_errors: {len(cell_errors)}:")
    logger.info(cell_errors)

    logger.info(f"<<yellow>> add_done: {len(add_done)}, add_from_redirect: {len(add_from_redirect)}")

    return table.string


__all__ = [
    "R_NEW_ROW",
    "add_header_r",
    "fix_title",
    "header_has_r",
    "work_one_table",
]
