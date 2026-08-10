#!/usr/bin/python3
"""
Module for injecting and updating table columns in Wikitext documents.
Separated into structural table management and data population logic.
"""

import logging

import wikitextparser as wtp
from wikitextparser._cell import Cell

from .utils import fix_title
from .wtp_table_manager import WikiTableColumnManager

logger = logging.getLogger(__name__)

R_NEW_ROW = '\n| style="text-align:center; white-space:nowrap; font-weight:bold; background:#C66A05" | R'


def count_r_rows(text: str) -> int:
    """Count the number of rows with R in the first column."""
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

# ==============================================================================
# PART 2: Data Population Manager (Fills Row Values Based on Business Logic)
# ==============================================================================

class AddRColumn:
    """Encapsulates logic for populating data in the 'R' column of wikitext tables."""

    def __init__(
        self,
        text: str,
        redirects: dict | None = None,
        pages: list | None = None,
    ) -> None:
        self.text = text
        self.redirects = redirects or {}
        self.pages = set(pages) if pages else set()
        self.tables = 0
        self.column_manager = WikiTableColumnManager()

    def load_ids(self, r_header: str, title_header: str, all_cells: list[list[Cell]]):
        """Map header names to their respective column indices."""
        header_index = _build_header_index(all_cells)
        r_header_id = header_index.get(r_header)
        title_header_id = header_index.get(title_header)

        if r_header_id is None or title_header_id is None:
            logger.warning(
                f"Couldn't find expected headers: "
                f"r_header={r_header!r} -> {r_header_id}, title_header={title_header!r} -> {title_header_id}"
            )
        return r_header_id, title_header_id

    # ================================
    # Main function
    # ================================

    def _populate_table_rows(
        self,
        table: wtp.Table,
        r_header: str = "R",
        title_header: str = "Page title",
    ) -> bool:
        """Populate the 'R' column cell values based on matching pages and redirects."""
        all_cells: list[list[Cell]] | None = self.column_manager.load_table_cells(table)
        if not all_cells:
            return False

        # 1. Map header text to its column index
        r_header_id, title_header_id = self.load_ids(r_header, title_header, all_cells)

        if r_header_id is None or title_header_id is None:
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
            if max(r_header_id, title_header_id) >= len(row_cells):
                continue

            r_idx_cell: Cell = row_cells[r_header_id]
            title_idx_cell: Cell = row_cells[title_header_id]

            if r_idx_cell is None or title_idx_cell is None:
                continue

            try:
                r_column_value = r_idx_cell.value.strip()
            except Exception:
                logger.warning(f"Cell error at row {n}")
                cell_errors += 1
                continue

            if r_column_value == r_header:
                r_idx_cell.string = R_NEW_ROW
                already_in += 1
                continue

            try:
                cell_value = title_idx_cell.value.strip()
            except Exception:
                logger.warning(f"Cell error at row {n}")
                cell_errors += 1
                continue

            title = fix_title(cell_value)
            title2 = self.redirects.get(title, title)

            if title in self.pages:
                r_idx_cell.string = R_NEW_ROW
                add_done += 1

            elif title2 in self.pages:
                r_idx_cell.string = R_NEW_ROW
                add_from_redirect += 1
            else:
                no_add += 1

        if cell_errors:
            logger.error(f"Cell errors encountered: {cell_errors}")

        logger.info(f"no_add: {no_add}, already_in: {already_in}")
        logger.info(f"add_done: {add_done}, add_from_redirect: {add_from_redirect}")

        return True

    # ================================
    # Public API
    # ================================

    def count_r_rows(self) -> int:
        """Count existing 'R' formatted rows in the document text."""
        return self.text.count(R_NEW_ROW.strip())

    def run(self) -> str:
        """Execute column structure injection and data population sequentially."""
        parsed = wtp.parse(self.text)

        if not parsed.tables:
            self.tables = 0
            return self.text

        self.tables = len(parsed.tables)
        table = parsed.tables[0]

        # STEP 1: Ensure structural column exists (Part 1)
        added = self.column_manager.ensure_column_exists(
            table,
            col_name="R",
            position="after_first",
            default_value="",
        )

        # update self.text after adding R column
        if added:
            self.text = parsed.string

        # Validate prerequisites: Return False if no redirects or pages
        if not self.redirects and not self.pages:
            logger.info("No redirects or pages to add!")
            return self.text

        # Return False if R column not exists and not added
        if not self.column_manager.has_column(table, "R"):
            logger.info("Can't add or find R column in table!")
            return self.text

        # STEP 2: Populate cell values (Part 2)
        changed = self._populate_table_rows(
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
    """Convenience function to process wikitext and populate the 'R' column."""
    model = AddRColumn(
        text,
        redirects,
        pages,
    )
    return model.run()


__all__ = [
    "WikiTableColumnManager",
    "AddRColumn",
    "count_r_rows",
    "inject_r_column_into_tables",
]
