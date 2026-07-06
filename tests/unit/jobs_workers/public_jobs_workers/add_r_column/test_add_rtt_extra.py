"""Additional unit tests for add_rtt.py covering edge cases not in the original suite."""

from __future__ import annotations

import pytest
import wikitextparser as wtp

from src.main_app.jobs_workers.public_jobs_workers.add_r_column.add_rtt import (
    AddRColumn,
)


def make_model(text: str = "", redirects: dict | None = None, pages: list | None = None) -> AddRColumn:
    return AddRColumn(text, redirects, pages)


def _process_table_rows(
    model: AddRColumn,
    table_text: str,
    r_header: str = "R",
    title_header: str = "Page title",
) -> str:
    parsed = wtp.parse(table_text)
    table = parsed.tables[0]
    _ = model._process_table(table, r_header, title_header)
    return table.string


class TestProcessTableRowsExtra:
    def test_short_row_missing_title_cell_is_skipped(self):
        table_text = "{| class=wikitable\n! #\n! R\n! Title\n|-\n| 1\n| \n|-\n| 2\n| \n| [[Aspirin]]\n|}"
        model = make_model(table_text, {}, ["Aspirin"])
        result = _process_table_rows(model, table_text, title_header="Title")
        parsed = wtp.parse(result)
        cells = parsed.tables[0].cells()
        assert cells[1][2] is None
        assert "background:#C66A05" in cells[2][1].string

    def test_missing_r_or_title_header_returns_unchanged(self):
        table_text = '{| class="wikitable"\n! #\n! R\n! Description\n|-\n| 1\n| \n| something\n|}'
        model = make_model(table_text)
        result = _process_table_rows(model, table_text, title_header="Page title")
        assert result == table_text

    def test_no_pages_no_redirects_marks_no_add(self):
        table_text = '{| class="wikitable"\n! #\n! R\n! Title\n|-\n| 1\n| \n| [[Ibuprofen]]\n|}'
        model = make_model(table_text)
        result = _process_table_rows(model, table_text, title_header="Title")
        parsed = wtp.parse(result)
        cells = parsed.tables[0].cells()
        assert "background:#C66A05" not in cells[1][1].string

    def test_redirect_maps_multiple_titles_to_same_page(self):
        table_text = (
            "{| class='wikitable'\n! #\n! R\n! Title\n|-\n| 1\n| \n| [[Tylenol]]\n|-\n| 2\n| \n| [[Panadol]]\n|}"
        )
        redirects = {"Tylenol": "Paracetamol", "Panadol": "Paracetamol"}
        pages = ["Paracetamol"]
        model = make_model(table_text, redirects, pages)
        result = _process_table_rows(model, table_text, title_header="Title")
        parsed = wtp.parse(result)
        cells = parsed.tables[0].cells()
        assert "background:#C66A05" in cells[1][1].string
        assert "background:#C66A05" in cells[2][1].string

    def test_row_already_marked_r_is_preserved_even_if_not_in_pages(self):
        table_text = '{| class="wikitable"\n! #\n! R\n! Title\n|-\n| 1\n| R\n| [[NotInPages]]\n|}'
        model = make_model(table_text)
        result = _process_table_rows(model, table_text, title_header="Title")
        assert "background:#C66A05" in result

    def test_empty_table_no_data_rows_returns_table_string(self):
        table_text = '{| class="wikitable"\n! #\n! R\n! Title\n|}'
        model = make_model(table_text, {}, ["Aspirin"])
        result = _process_table_rows(model, table_text, title_header="Title")
        assert "! #" in result
        assert "! R" in result
        assert "! Title" in result

    @pytest.mark.skip
    def test_title_with_wikilink_brackets_is_normalized(self):
        table_text = '{| class="wikitable"\n! #\n! R\n! Title\n|-\n| 1\n| \n| [[Aspirin|Aspirin (drug)]]\n|}'
        model = make_model(table_text, {}, ["Aspirin"])
        result = _process_table_rows(model, table_text, title_header="Title")
        assert "background:#C66A05" in result


class TestProcessTableRows:
    def test_work_one_table_no_r_header(self):
        table_text = '{| class="wikitable"\n! Header\n! Title\n|-\n| data\n| data\n|}'
        model = make_model(table_text)
        result = _process_table_rows(
            model,
            table_text,
            title_header="Title",
        )
        assert result == table_text

    def test_work_one_table_updates_cells(self):
        table_text = (
            '{| class="wikitable"\n! #\n! R\n! Title\n|-\n| 1\n| \n| [[Aspirin]]\n|-\n| 2\n| \n| [[Paracetamol]]\n|}'
        )
        redirects = {"Aspirin": "Aspirin"}
        pages = ["Aspirin"]
        model = make_model(table_text, redirects, pages)
        result = _process_table_rows(
            model,
            table_text,
            title_header="Title",
        )

        assert 'background:#C66A05" | R' in result
        assert "[[Aspirin]]" in result
        assert "[[Paracetamol]]" in result

        parsed = wtp.parse(result)
        cells = parsed.tables[0].cells()
        # Row 1 (data): cells[1] is list of Cells for the first data row
        # cells[1][1] is the 'R' cell
        assert 'background:#C66A05" | R' in cells[1][1].string  # type: ignore
        # cells[2][1] should NOT be updated (it's for Paracetamol)
        assert 'background:#C66A05" | R' not in cells[2][1].string  # type: ignore

    def test_work_one_table_with_redirects(self):
        table_text = '{| class="wikitable"\n! #\n! R\n! Title\n|-\n| 1\n| \n| [[Acetaminophen]]\n|}'
        redirects = {"Acetaminophen": "Paracetamol"}
        pages = ["Paracetamol"]
        model = make_model(table_text, redirects, pages)
        result = _process_table_rows(
            model,
            table_text,
            title_header="Title",
        )
        assert 'background:#C66A05" | R' in result

    def test_work_one_table_already_r(self):
        table_text = '{| class="wikitable"\n! #\n! R\n! Title\n|-\n| 1\n| R\n| [[Aspirin]]\n|}'
        model = make_model(table_text)
        result = _process_table_rows(
            model,
            table_text,
            title_header="Title",
        )
        assert 'background:#C66A05" | R' in result
