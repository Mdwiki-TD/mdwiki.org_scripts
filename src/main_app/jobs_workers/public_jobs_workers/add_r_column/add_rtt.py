#!/usr/bin/python3
""" """

import logging
from typing import Any

import wikitextparser as wtp
from wikitextparser._cell import Cell

from .utils import fix_title

logger = logging.getLogger(__name__)

R_NEW_ROW = '\n| style="text-align:center; white-space:nowrap; font-weight:bold; background:#C66A05" | R'


def count_r_rows(text: str) -> int:
    """Count the number of rows with R in the first column"""
    return text.count(R_NEW_ROW.strip())


def _build_header_index(all_cells: list[list[Cell]]) -> dict[str, int]:
    """
    Build a mapping of header text -> column index.
    """
    header_index: dict[str, int] = {}
    for row in all_cells:
        if not row or row[0] is None or not row[0].is_header:
            continue
        for idx, cell in enumerate(row):
            if cell is None:
                continue
            header_index[cell.value.strip()] = idx
        break
    return header_index


class AddRColumn:
    """Encapsulates logic for injecting/updating an 'R' column in wikitext tables."""

    def __init__(
        self,
        text: str,
        redirects: dict | None = None,
        pages: list | None = None,
    ) -> None:
        self.text = text
        self.redirects = redirects or {}
        self.pages = pages or {}
        self.tables = 0

    def _load_table_cells(self, table: wtp.Table) -> Any:
        try:
            return table.cells()
        except Exception as exc:
            logger.error(f"error getting cells: {exc}")
            return False

    def _count_r_cells(self, table: wtp.Table) -> int:
        if not table:
            logger.info("no table found")
            return 0

        all_cells = self._load_table_cells(table)

        if not all_cells:
            return 0

        numbs = 0
        for x in all_cells:
            # we don't need to count headers here
            if x[1].is_header:
                continue

            for v in x:
                if v.value.strip() == "R":
                    numbs += 1
        return numbs

    def _check_for_r_header(self, table: wtp.Table) -> bool:
        if not table:
            logger.info("no table found")
            return False

        all_cells = self._load_table_cells(table)

        if not all_cells:
            return False

        for x in all_cells:
            # we need to check only headers
            if not x[1].is_header:
                continue

            for numb, v in enumerate(x, start=1):
                if v.value.strip() == "R":
                    logger.info(f"header has R: in column {numb}")
                    return True
        return False

    def _add_r_header_table(self, table: wtp.Table) -> bool:
        if not table:
            return False

        all_cells = self._load_table_cells(table)
        if not all_cells:
            return False

        count = 0
        # add R to header in 2nd column
        for x in all_cells:
            count += 1

            # in header add the column R, in other rows add empty cell
            cell_str = "\n! R" if x[0].is_header else "\n| "

            # add cell_str after first cell
            x[0].value = x[0].value + cell_str

        logger.info(f"Added R column to table header in {count} cells")

        # NOTE: Adding new cell delimiters (\n! or \n|) directly into the cell value
        # alters the table structure dynamically. We must re-assign 'table.string'
        # to force wikitextparser to re-parse the text and register the new cells.
        # Otherwise, the internal span tracking breaks, causing the following error
        # in wikitextparser/_table.py:261 (in cells insort_right):
        # TypeError: '<' not supported between instances of 'bytearray' and 'NoneType'

        table_str = table.string
        table.string = table_str
        return True

    def _ensure_table_has_r_column(self, table) -> bool:
        if self._check_for_r_header(table):
            return False

        added = self._add_r_header_table(table)
        return added


    def load_ids(self, r_header, title_header, all_cells):
        header_index = _build_header_index(all_cells)
        r_idx = header_index.get(r_header)
        title_idx = header_index.get(title_header)

        if r_idx is None or title_idx is None:
            logger.warning(
                f"couldn't find expected headers: "
                f"r_header={r_header!r} -> {r_idx}, title_header={title_header!r} -> {title_idx}"
            )
        return r_idx,title_idx

    # ================================
    # Main function
    # ================================

    def _process_table(
        self,
        table: wtp.Table,
        r_header: str = "R",
        title_header: str = "Page title",
    ) -> bool:

        all_cells = self._load_table_cells(table)
        if not all_cells:
            return False

        # 1. Map header text to its column index
        r_idx, title_idx = self.load_ids(r_header, title_header, all_cells)

        if r_idx is None or title_idx is None:
            return False

        already_in = 0
        no_add = 0
        add_from_redirect = 0
        add_done = 0
        cell_errors = 0

        for n, row_cells in enumerate(all_cells):
            # Skip empty rows and rows that don't have enough columns
            if not row_cells or row_cells[0] is None:
                continue

            # Skip columns headers
            if row_cells[0].is_header:
                continue

            # Skip rows that are too short to contain both required columns
            if max(r_idx, title_idx) >= len(row_cells) or row_cells[r_idx] is None or row_cells[title_idx] is None:
                continue

            try:
                title = row_cells[title_idx].value.strip()
                header_label = row_cells[r_idx].value.strip()
            except Exception:
                logger.warning(f"cell error: {n}")
                cell_errors += 1
                continue

            if header_label == "R":
                row_cells[r_idx].string = R_NEW_ROW
                already_in += 1
                continue

            title = fix_title(title)
            title2 = self.redirects.get(title, title)
            if title in self.pages:
                row_cells[r_idx].string = R_NEW_ROW
                add_done += 1

            elif title2 in self.pages:
                row_cells[r_idx].string = R_NEW_ROW
                add_from_redirect += 1
            else:
                no_add += 1

        if cell_errors:
            logger.error(f"cell_errors: {cell_errors}:")

        logger.info(f"no_add: {no_add}, already_in: {already_in}")
        logger.info(f"add_done: {add_done}, add_from_redirect: {add_from_redirect}")

        return True
    # ================================
    # Public API
    # ================================

    def count_r_rows(self) -> int:
        return count_r_rows(self.text)

    def run(self) -> str:
        parsed = wtp.parse(self.text)

        if not parsed.tables:
            self.tables = 0
            return self.text

        self.tables = len(parsed.tables)
        table = parsed.tables[0]

        # check if R column exists or add it
        added = self._ensure_table_has_r_column(table)

        # update self.text after adding R column
        if added:
            self.text = parsed.string

        # Return False if no redirects or pages
        if not self.redirects and not self.pages:
            logger.info("No redirects or pages to add!")
            return self.text

        # Return False if R column not exists and not added
        if not self._check_for_r_header(table):
            logger.info("Can't add R column to table!")
            return self.text

        changed = self._process_table(
            table,
            r_header="R",
            title_header="Page title",
        )

        if changed:
            # update self.text after adding R column
            self.text = parsed.string

        return self.text


def inject_r_column_into_tables(
    text: str,
    redirects: dict | None = None,
    pages: list | None = None,
) -> str:
    model = AddRColumn(
        text,
        redirects,
        pages,
    )
    return model.run()


__all__ = [
    "AddRColumn",
    "count_r_rows",
    "inject_r_column_into_tables",
]
