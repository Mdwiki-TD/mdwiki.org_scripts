"""Unit tests for src/main_app/jobs/workers/add_r_column/add_rtt.py."""

from __future__ import annotations

import wikitextparser as wtp

from src.main_app.jobs_workers.public_jobs_workers.add_r_column.wtp_table_manager import WikiTableColumnManager


class TestCheckForRHeader:
    def test_check_for_r_header_none_table(self):
        model = WikiTableColumnManager()
        assert model.has_column(None, "R") is False

    def test_check_for_r_header_r_present(self):
        table_text = '{| class="wikitable"\n! Header\n! R\n! Title\n|-\n| data\n| data\n| data\n|}'
        table = wtp.parse(table_text).tables[0]
        model = WikiTableColumnManager()
        assert model.has_column(table, "R") is True

    def test_check_for_r_header_empty_table_no_rows(self):
        table_text = '{| class="wikitable"\n|}'
        table = wtp.parse(table_text).tables[0]
        model = WikiTableColumnManager()
        assert model.has_column(table, "R") is False

    def test_header_has_r_true(self):
        table_text = '{| class="wikitable"\n! Header\n! R\n! Title\n|-\n| data\n| data\n| data\n|}'
        parsed = wtp.parse(table_text)
        table = parsed.tables[0]
        model = WikiTableColumnManager()
        assert model.has_column(table, "R") is True

    def test_header_has_r_false(self):
        table_text = '{| class="wikitable"\n! Header\n! Other\n! Title\n|-\n| data\n| data\n| data\n|}'
        parsed = wtp.parse(table_text)
        table = parsed.tables[0]
        model = WikiTableColumnManager()
        assert model.has_column(table, "R") is False

    def test_header_has_r_with_table_object(self):
        table_text = '{| class="wikitable"\n! Header\n! R\n! Title\n|-\n| data\n| data\n| data\n|}'
        table = wtp.parse(table_text).tables[0]
        model = WikiTableColumnManager()
        assert model.has_column(table, "R") is True


class TestAddRHeader:

    def test_add_r_header_data_rows_get_blank_cell(self):
        # add_column only appends to the first cell (x[0]) of each row,
        # inserting a new second column; it does not touch every cell.
        table_text = '{| class="wikitable"\n! Header\n! Title\n|-\n| data1\n| data2\n|}'
        table = wtp.parse(table_text).tables[0]
        model = WikiTableColumnManager()
        _ = model.add_column(table, "R")
        result = table.string

        assert "! Header\n! R" in result
        assert "| data1\n| " in result
        assert "| data2" in result

    def test_add_r_header_multiple_data_rows(self):
        table_text = "{| class='wikitable'\n! Header\n! Title\n|-\n| r1c1\n| r1c2\n|-\n| r2c1\n| r2c2\n|}"
        table = wtp.parse(table_text).tables[0]
        model = WikiTableColumnManager()
        _ = model.add_column(table, "R")
        result = table.string

        assert result.count("! R") == 1
        assert "| r1c1\n| " in result
        assert "| r2c1\n| " in result

    def test_add_header_r_new(self):
        table_text = '{| class="wikitable"\n! Header\n! Title\n|-\n| data\n| data\n|}'
        parsed = wtp.parse(table_text)
        table = parsed.tables[0]
        model = WikiTableColumnManager()
        _ = model.add_column(table, "R")
        result = table.string
        assert "! Header\n! R" in result
        assert "| data\n| " in result

    def test_add_header_r_already_exists(self):
        table_text = '{| class="wikitable"\n! Header\n! R\n! Title\n|-\n|data1\n|data2\n|data3\n|}'
        parsed = wtp.parse(table_text)
        table = parsed.tables[0]
        model = WikiTableColumnManager()
        _ = model.add_column(table, "R")
        result = table.string
        assert result == '{| class="wikitable"\n! Header\n! R\n! R\n! Title\n|-\n|data1\n| \n|data2\n|data3\n|}'
