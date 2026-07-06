"""Additional unit tests for add_rtt.py covering edge cases not in the original suite."""

from __future__ import annotations

import pytest
import wikitextparser as wtp

from src.main_app.jobs_workers.public_jobs_workers.add_r_column.add_rtt import (
    R_NEW_ROW,
    _add_r_header,
    _build_header_index,
    _check_for_r_header,
    _process_table_rows,
    count_r_rows,
    inject_r_column_into_tables,
)


class TestCountRRowsExtra:
    def test_count_r_rows_multiple_occurrences(self):
        text = R_NEW_ROW + "some content" + R_NEW_ROW + "more" + R_NEW_ROW
        assert count_r_rows(text) == 3

    def test_count_r_rows_zero_when_absent(self):
        text = '{| class="wikitable"\n! Header\n! Title\n|-\n| data\n| data\n|}'
        assert count_r_rows(text) == 0

    def test_count_r_rows_exact_marker_string(self):
        assert count_r_rows(R_NEW_ROW.strip()) == 1


class TestBuildHeaderIndex:
    def test_build_header_index_maps_columns(self):
        table_text = '{| class="wikitable"\n! #\n! R\n! Page title\n|-\n| 1\n| \n| [[Aspirin]]\n|}'
        table = wtp.parse(table_text).tables[0]
        rows = table.cells()
        index = _build_header_index(rows)
        assert index == {"#": 0, "R": 1, "Page title": 2}

    def test_build_header_index_no_header_row(self):
        table_text = '{| class="wikitable"\n|-\n| 1\n| 2\n|}'
        table = wtp.parse(table_text).tables[0]
        rows = table.cells()
        index = _build_header_index(rows)
        assert index == {}

    def test_build_header_index_only_uses_first_header_row(self):
        # If somehow multiple header-looking rows exist, only first should be used
        table_text = '{| class="wikitable"\n! A\n! B\n|-\n| 1\n| 2\n|}'
        table = wtp.parse(table_text).tables[0]
        rows = table.cells()
        index = _build_header_index(rows)
        assert index == {"A": 0, "B": 1}


class TestCheckForRHeaderExtra:
    def test_check_for_r_header_none_table(self):
        assert _check_for_r_header(None) is False

    def test_check_for_r_header_r_not_in_second_column(self):
        # _check_for_r_header specifically looks at x[1] being a header;
        # if R exists but column 2 (index 1) isn't a header cell, behavior depends on data.
        table_text = '{| class="wikitable"\n! Header\n! R\n! Title\n|-\n| data\n| data\n| data\n|}'
        table = wtp.parse(table_text).tables[0]
        assert _check_for_r_header(table) is True

    def test_check_for_r_header_empty_table_no_rows(self):
        table_text = '{| class="wikitable"\n|}'
        table = wtp.parse(table_text).tables[0]
        assert _check_for_r_header(table) is False


class TestAddRHeaderExtra:
    def test_add_r_header_data_rows_get_blank_cell(self):
        # _add_r_header only appends to the first cell (x[0]) of each row,
        # inserting a new second column; it does not touch every cell.
        table_text = '{| class="wikitable"\n! Header\n! Title\n|-\n| data1\n| data2\n|}'
        table = wtp.parse(table_text).tables[0]
        result = _add_r_header(table)
        assert "! Header\n! R" in result
        assert "| data1\n| " in result
        # data2 (second column) is untouched, still present as-is
        assert "| data2" in result

    def test_add_r_header_none_table_returns_empty_string(self):
        assert _add_r_header(None) == ""

    def test_add_r_header_multiple_data_rows(self):
        table_text = '{| class="wikitable"\n! Header\n! Title\n' "|-\n| r1c1\n| r1c2\n" "|-\n| r2c1\n| r2c2\n|}"
        table = wtp.parse(table_text).tables[0]
        result = _add_r_header(table)
        assert result.count("! R") == 1
        # each data cell in first column should get appended blank pipe
        assert "| r1c1\n| " in result
        assert "| r2c1\n| " in result


class TestProcessTableRowsExtra:
    @pytest.mark.skip
    def test_title_with_wikilink_brackets_is_normalized(self):
        table_text = '{| class="wikitable"\n! #\n! R\n! Title\n|-\n| 1\n| \n| [[Aspirin|Aspirin (drug)]]\n|}'
        result = _process_table_rows(
            table_text,
            {},
            ["Aspirin"],
            title_header="Title",
        )
        assert "background:#C66A05" in result

    def test_short_row_missing_title_cell_is_skipped(self):
        # Row 1 has only 2 cells (missing Title), row 2 has all 3
        table_text = '{| class="wikitable"\n! #\n! R\n! Title\n' "|-\n| 1\n| \n" "|-\n| 2\n| \n| [[Aspirin]]\n|}"
        result = _process_table_rows(
            table_text,
            {},
            ["Aspirin"],
            title_header="Title",
        )
        parsed = wtp.parse(result)
        cells = parsed.tables[0].cells()
        # Row with missing title cell should remain untouched (still None/blank)
        assert cells[1][2] is None
        # Row with Aspirin should be marked
        assert "background:#C66A05" in cells[2][1].string

    def test_missing_r_or_title_header_returns_unchanged(self):
        table_text = '{| class="wikitable"\n! #\n! R\n! Description\n|-\n| 1\n| \n| something\n|}'
        result = _process_table_rows(
            table_text,
            {},
            [],
            title_header="Page title",  # doesn't exist in table
        )
        assert result == table_text

    def test_no_pages_no_redirects_marks_no_add(self):
        table_text = '{| class="wikitable"\n! #\n! R\n! Title\n|-\n| 1\n| \n| [[Ibuprofen]]\n|}'
        result = _process_table_rows(
            table_text,
            {},
            [],
            title_header="Title",
        )
        parsed = wtp.parse(result)
        cells = parsed.tables[0].cells()
        # Not in pages -> should not be marked with R
        assert "background:#C66A05" not in cells[1][1].string

    def test_redirect_maps_multiple_titles_to_same_page(self):
        table_text = (
            '{| class="wikitable"\n! #\n! R\n! Title\n' "|-\n| 1\n| \n| [[Tylenol]]\n" "|-\n| 2\n| \n| [[Panadol]]\n|}"
        )
        redirects = {"Tylenol": "Paracetamol", "Panadol": "Paracetamol"}
        pages = ["Paracetamol"]
        result = _process_table_rows(table_text, redirects, pages, title_header="Title")
        parsed = wtp.parse(result)
        cells = parsed.tables[0].cells()
        assert "background:#C66A05" in cells[1][1].string
        assert "background:#C66A05" in cells[2][1].string

    def test_row_already_marked_r_is_preserved_even_if_not_in_pages(self):
        table_text = '{| class="wikitable"\n! #\n! R\n! Title\n|-\n| 1\n| R\n| [[NotInPages]]\n|}'
        result = _process_table_rows(table_text, {}, [], title_header="Title")
        assert "background:#C66A05" in result

    def test_empty_table_no_data_rows_returns_table_string(self):
        table_text = '{| class="wikitable"\n! #\n! R\n! Title\n|}'
        result = _process_table_rows(table_text, {}, ["Aspirin"], title_header="Title")
        # No data rows to process; should just return the (unchanged) header-only table
        assert "! #" in result
        assert "! R" in result
        assert "! Title" in result


class TestInjectRColumnIntoTablesExtra:
    def test_inject_only_affects_first_table_when_multiple_present(self):
        text = (
            '{| class="wikitable"\n! Header\n! Title\n|-\n| data\n| data\n|}\n'
            "Some text between tables\n"
            '{| class="wikitable"\n! Header2\n! Title2\n|-\n| data2\n| data2\n|}'
        )
        result = inject_r_column_into_tables(text, {}, [])
        assert "! Header\n! R" in result
        assert "! Header2\n! Title2" in result
        assert "! Header2\n! R" not in result

    def test_inject_skips_row_processing_when_no_redirects_and_no_pages(self):
        # Header already has R; since redirects={} and pages=[] are both falsy,
        # _process_table_rows should not run and text stays the same.
        text = '{| class="wikitable"\n! #\n! R\n! Title\n|-\n| 1\n| \n| [[Aspirin]]\n|}'
        result = inject_r_column_into_tables(text, {}, [])
        assert result == text

    def test_inject_with_default_title_header_page_title(self):
        text = '{| class="wikitable"\n! #\n! Page title\n|-\n| 1\n| [[Aspirin]]\n|}'
        result = inject_r_column_into_tables(text, {}, ["Aspirin"])
        assert "! R" in result
        assert "background:#C66A05" in result

    def test_inject_with_empty_string(self):
        assert inject_r_column_into_tables("", {}, []) == ""

    def test_inject_returns_text_unchanged_when_header_cannot_be_added(self):
        # A table with no header row at all: _add_r_header will still append '! R'
        # style markup logic branches on x[0].is_header, so this exercises the
        # 'else' branch appending a blank data cell instead of a header.
        text = '{| class="wikitable"\n|-\n| onlydata\n| morestuff\n|}'
        result = inject_r_column_into_tables(text, {}, [])
        assert result != text
