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

    def _check_for_r_header(self, table: wtp.Table) -> bool:
        if not table or not isinstance(table, wtp.Table):
            logger.info("no table found")
            return False

        try:
            all_cells = table.cells()
        except Exception as exc:
            logger.error(f"error getting cells: {exc}")
            return False

        if not all_cells:
            return False

        for x in all_cells:
            if x[1].is_header:
                for numb, v in enumerate(x, 1):
                    if v.value.strip() == "R":
                        logger.info(f"header has R: in column {numb}")
                        return True
        return False

    def _add_r_header_table(self, table: wtp.Table) -> bool:
        if not table or not isinstance(table, wtp.Table):
            return False
        count = 0

        try:
            all_cells = table.cells()
        except Exception as exc:
            logger.error(f"error getting cells: {exc}")
            return False

        if not all_cells:
            return False

        # add R to header in 2nd column
        for x in all_cells:
            if x[0].is_header:
                x[0].value = x[0].value + "\n! R"
            else:
                x[0].value = x[0].value + "\n| "

            count += 1

        logger.info(f"Added R column to table header in {count} cells")

        return True

    def _add_r_header(self, table: wtp.Table):
        # Check if R column already exists
        if self._check_for_r_header(table):
            logger.info("R column already exists in table header")
            return

        self._add_r_header_table(table)

    def _process_table(
        self,
        table: wtp.Table,
        r_header: str = "R",
        title_header: str = "Page title",
    ) -> bool:
        already_in: list[Any] = []
        no_add: list[Any] = []

        add_from_redirect: list[Any] = []
        add_done: list[Any] = []

        cell_errors: list[Any] = []

        try:
            all_cells = table.cells()
        except Exception as exc:
            logger.error(f"error getting cells: {exc}")
            return False

        if not all_cells:
            return False

        # 1. Map header text to its column index
        header_index = _build_header_index(all_cells)

        r_idx = header_index.get(r_header)
        title_idx = header_index.get(title_header)

        if r_idx is None or title_idx is None:
            logger.warning(
                f"couldn't find expected headers: "
                f"r_header={r_header!r} -> {r_idx}, title_header={title_header!r} -> {title_idx}"
            )
            return False

        data = table.data()

        for n, row_cells in enumerate(all_cells):
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
            title2 = self.redirects.get(title, title)

            if r_s == "R":
                row_cells[r_idx].string = R_NEW_ROW

                already_in.append(title)
                continue

            if title in self.pages:
                row_cells[r_idx].string = R_NEW_ROW

                add_done.append(title)
            elif title2 in self.pages:
                row_cells[r_idx].string = R_NEW_ROW
                add_from_redirect.append(title)
            else:
                no_add.append(title)

        logger.info(f"no_add: {len(no_add)}, already_in: {len(already_in)}")

        logger.error(f"cell_errors: {len(cell_errors)}:")
        logger.info(cell_errors)

        logger.info(f"add_done: {len(add_done)}, add_from_redirect: {len(add_from_redirect)}")

        return True

    def count_r_rows(self) -> int:
        return count_r_rows(self.text)

    def _process_the_table(self, table: wtp.Table) -> bool:
        if not self._check_for_r_header(table):
            logger.info("Can't add R column to table!")
            return False

        if not self.redirects and not self.pages:
            return False

        changed = self._process_table(
            table,
            r_header="R",
            title_header="Page title",
        )
        if changed:
            logger.info("Table changed!")

        return True

    def run(self) -> str:
        parsed = wtp.parse(self.text)

        if not parsed.tables:
            return self.text

        table = parsed.tables[0]

        if not self._check_for_r_header(table):
            added = self._add_r_header_table(table)

            # NOTE: next step to solve this issue by reloading the table object
            # wikitextparser/_table.py:261: in cells insort_right(spans, cell_span)
            # TypeError: '<' not supported between instances of 'bytearray' and 'NoneType'

            table_str = table.string
            if added:
                table.string = table_str

        self._process_the_table(table)

        return parsed.string


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
