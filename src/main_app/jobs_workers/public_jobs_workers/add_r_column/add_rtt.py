#!/usr/bin/python3
""" """

import logging
from typing import Any

import wikitextparser as wtp
from wikitextparser._cell import Cell

from .utils import fix_title

logger = logging.getLogger(__name__)

R_NEW_ROW = '\n| style="text-align:center; white-space:nowrap; font-weight:bold; background:#C66A05" | R'


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


def _check_for_r_header(table: wtp.Table) -> bool:
    if not table:
        return False

    for x in table.cells():  # type: ignore
        if x[1].is_header:
            for numb, v in enumerate(x, 1):
                if v.value.strip() == "R":
                    logger.info(f"header has R: in column {numb}")
                    return True
    return False


def count_r_rows(text: str) -> int:
    """Count the number of rows with R in the first column"""
    return text.count(R_NEW_ROW.strip())


def _add_r_header(table: wtp.Table) -> str:

    if not table:
        return ""

    # Check if R column already exists
    if _check_for_r_header(table):
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


def _process_table_rows(
    table_text: str,
    redirects: dict,
    pages: set,
    r_header: str = "R",
    title_header: str = "Page title",
) -> str:
    parsed = wtp.parse(table_text)
    table = parsed.tables[0]

    if not _check_for_r_header(table):
        logger.info("no R in table header!")
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

    r_idx = header_index.get(r_header)
    title_idx = header_index.get(title_header)

    if r_idx is None or title_idx is None:
        logger.warning(
            f"couldn't find expected headers: "
            f"r_header={r_header!r} -> {r_idx}, title_header={title_header!r} -> {title_idx}"
        )
        return table.string

    data = table.data()

    for n, row_cells in enumerate(all_rows):
        if not row_cells or row_cells[0] is None or row_cells[0].is_header:
            continue

        # Skip rows that are too short to contain both required columns
        if max(r_idx, title_idx) >= len(row_cells) or row_cells[r_idx] is None or row_cells[title_idx] is None:
            continue

        try:
            title = row_cells[title_idx].value.strip()
            r_s = row_cells[r_idx].value.strip()
        except Exception:
            logger.warning(f"cell error: {n}")
            numb = data[n][title_idx]
            cell_errors.append(numb)
            continue

        title = fix_title(title)
        title2 = redirects.get(title, title)

        if r_s == "R":
            row_cells[r_idx].string = R_NEW_ROW

            already_in.append(title)
            continue

        if title in pages:
            row_cells[r_idx].string = R_NEW_ROW

            add_done.append(title)
        elif title2 in pages:
            row_cells[r_idx].string = R_NEW_ROW
            add_from_redirect.append(title)
        else:
            no_add.append(title)

    logger.info(f"no_add: {len(no_add)}, already_in: {len(already_in)}")

    logger.error(f"cell_errors: {len(cell_errors)}:")
    logger.info(cell_errors)

    logger.info(f"add_done: {len(add_done)}, add_from_redirect: {len(add_from_redirect)}")

    return table.string


class AddRColumn:
    def __init__(
        self,
        text: str,
        redirects: dict,
        pages: list,
    ) -> None:
        self.text = text
        self.redirects = redirects
        self.pages = pages

    def inject_r_column(self) -> str:
        parsed = wtp.parse(self.text)

        if not parsed.tables:
            return self.text

        table = parsed.tables[0]

        new_text = self.text

        if not _check_for_r_header(table):
            new_text = _add_r_header(table)

            if new_text == self.text:
                logger.info("Can't add R column to table!")
                return self.text

        if self.redirects or self.pages:
            new_text = _process_table_rows(
                new_text,
                self.redirects,
                self.pages,
                r_header="R",
                title_header="Page title",
            )

        table.string = new_text

        _text = parsed.string

        return _text


def inject_r_column_into_tables(
    text: str,
    redirects: dict,
    pages: list,
) -> str:
    model = AddRColumn(
        text,
        redirects,
        pages,
    )
    return model.inject_r_column()


__all__ = [
    "AddRColumn",
    "count_r_rows",
    "inject_r_column_into_tables",
]
