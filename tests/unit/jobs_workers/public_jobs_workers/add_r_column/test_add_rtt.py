"""Unit tests for src/main_app/jobs/workers/add_r_column/add_rtt.py."""

from __future__ import annotations

import wikitextparser as wtp

from src.main_app.jobs_workers.public_jobs_workers.add_r_column.add_rtt import (
    R_NEW_ROW,
    AddRColumn,
    count_r_rows,
    inject_r_column_into_tables,
    _build_header_index,
)

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
        table_text = '{| class="wikitable"\n! A\n! B\n|-\n| 1\n| 2\n|}'
        table = wtp.parse(table_text).tables[0]
        rows = table.cells()
        index = _build_header_index(rows)
        assert index == {"A": 0, "B": 1}


class TestCountRRows:
    def test_count_r_rows_multiple_occurrences(self):
        text = R_NEW_ROW + "some content" + R_NEW_ROW + "more" + R_NEW_ROW
        assert count_r_rows(text) == 3

    def test_count_r_rows_zero_when_absent(self):
        text = '{| class="wikitable"\n! Header\n! Title\n|-\n| data\n| data\n|}'
        assert count_r_rows(text) == 0

    def test_count_r_rows_exact_marker_string(self):
        assert count_r_rows(R_NEW_ROW.strip()) == 1

    def test_count_r_rows_uses_instance_text(self):
        model = AddRColumn(R_NEW_ROW * 4)
        assert model.count_r_rows() == 4

    def test_count_r_rows_no_tables(self):
        text = "Plain text"
        assert count_r_rows(text) == 0


class TestInjectRColumnIntoTables:
    def test_inject_r_column_into_tables_no_tables(self):
        text = "Plain text"
        assert inject_r_column_into_tables(text) == text

    def test_inject_r_column_into_tables_with_table(self):
        text = '{| class="wikitable"\n! Header\n! Title\n|-\n| data\n| data\n|}'
        # inject_r_column_into_tables should add R column because it's missing
        result = inject_r_column_into_tables(text)
        assert "! Header\n! R" in result

    def test_inject_only_affects_first_table_when_multiple_present(self):
        text = (
            '{| class="wikitable"\n! Header\n! Title\n|-\n| data\n| data\n|}\n'
            "Some text between tables\n"
            '{| class="wikitable"\n! Header2\n! Title2\n|-\n| data2\n| data2\n|}'
        )
        result = inject_r_column_into_tables(text)
        assert "! Header\n! R" in result
        assert "! Header2\n! Title2" in result
        assert "! Header2\n! R" not in result

    def test_inject_skips_row_processing_when_no_redirects_and_no_pages(self):
        text = '{| class="wikitable"\n! #\n! R\n! Title\n|-\n| 1\n| \n| [[Aspirin]]\n|}'
        result = inject_r_column_into_tables(text)
        assert result == text

    def test_inject_with_default_title_header_page_title(self):
        text = '{| class="wikitable"\n! #\n! Page title\n|-\n| 1\n| [[Aspirin]]\n|}'
        result = inject_r_column_into_tables(text, {}, ["Aspirin"])

        # check _add_r_header_table result:
        assert "! R" in result

        # check _process_the_table result
        assert "background:#C66A05" in result

    def test_inject_with_empty_string(self):
        assert inject_r_column_into_tables("") == ""

    def test_inject_returns_text_unchanged_when_header_cannot_be_added(self):
        text = '{| class="wikitable"\n|-\n| onlydata\n| morestuff\n|}'
        result = inject_r_column_into_tables(text)
        assert result != text


class TestCheckForRHeader:
    def test_check_for_r_header_none_table(self):
        model = AddRColumn("")
        assert model._check_for_r_header(None) is False

    def test_check_for_r_header_r_present(self):
        table_text = '{| class="wikitable"\n! Header\n! R\n! Title\n|-\n| data\n| data\n| data\n|}'
        table = wtp.parse(table_text).tables[0]
        model = AddRColumn("")
        assert model._check_for_r_header(table) is True

    def test_check_for_r_header_empty_table_no_rows(self):
        table_text = '{| class="wikitable"\n|}'
        table = wtp.parse(table_text).tables[0]
        model = AddRColumn("")
        assert model._check_for_r_header(table) is False

    def test_header_has_r_true(self):
        table_text = '{| class="wikitable"\n! Header\n! R\n! Title\n|-\n| data\n| data\n| data\n|}'
        parsed = wtp.parse(table_text)
        table = parsed.tables[0]
        model = AddRColumn("")
        assert model._check_for_r_header(table) is True

    def test_header_has_r_false(self):
        table_text = '{| class="wikitable"\n! Header\n! Other\n! Title\n|-\n| data\n| data\n| data\n|}'
        parsed = wtp.parse(table_text)
        table = parsed.tables[0]
        model = AddRColumn("")
        assert model._check_for_r_header(table) is False

    def test_header_has_r_with_table_object(self):
        table_text = '{| class="wikitable"\n! Header\n! R\n! Title\n|-\n| data\n| data\n| data\n|}'
        table = wtp.parse(table_text).tables[0]
        model = AddRColumn("")
        assert model._check_for_r_header(table=table) is True


class TestAddRHeader:

    def test_add_r_header_data_rows_get_blank_cell(self):
        # _add_r_header only appends to the first cell (x[0]) of each row,
        # inserting a new second column; it does not touch every cell.
        table_text = '{| class="wikitable"\n! Header\n! Title\n|-\n| data1\n| data2\n|}'
        table = wtp.parse(table_text).tables[0]
        model = AddRColumn("")
        _ = model._add_r_header(table)
        result = table.string

        assert "! Header\n! R" in result
        assert "| data1\n| " in result
        assert "| data2" in result

    def test_add_r_header_multiple_data_rows(self):
        table_text = "{| class='wikitable'\n! Header\n! Title\n|-\n| r1c1\n| r1c2\n|-\n| r2c1\n| r2c2\n|}"
        table = wtp.parse(table_text).tables[0]
        model = AddRColumn("")
        _ = model._add_r_header(table)
        result = table.string

        assert result.count("! R") == 1
        assert "| r1c1\n| " in result
        assert "| r2c1\n| " in result

    def test_add_header_r_new(self):
        table_text = '{| class="wikitable"\n! Header\n! Title\n|-\n| data\n| data\n|}'
        parsed = wtp.parse(table_text)
        table = parsed.tables[0]
        model = AddRColumn("")
        _ = model._add_r_header(table)
        result = table.string
        assert "! Header\n! R" in result
        assert "| data\n| " in result

    def test_add_header_r_already_exists(self):
        table_text = '{| class="wikitable"\n! Header\n! R\n! Title\n|-\n| data\n| data\n| data\n|}'
        parsed = wtp.parse(table_text)
        table = parsed.tables[0]
        model = AddRColumn("")
        _ = model._add_r_header(table)
        result = table.string
        assert result == table_text


class TestAddRColumnClass:
    """Sanity checks that the instance-based API works and matches __all__."""

    def test_class_is_exported(self):
        from src.main_app.jobs_workers.public_jobs_workers.add_r_column import add_rtt

        assert "AddRColumn" in add_rtt.__all__
        assert "count_r_rows" in add_rtt.__all__
        assert "inject_r_column_into_tables" in add_rtt.__all__

    def test_instance_stores_constructor_args(self):
        model = AddRColumn("some text", {"a": "b"}, ["Page1"])
        assert model.text == "some text"
        assert model.redirects == {"a": "b"}
        assert model.pages == ["Page1"]

    def test_module_level_count_r_rows_delegates_to_instance(self):
        text = R_NEW_ROW * 2
        assert count_r_rows(text) == AddRColumn(text).count_r_rows() == 2

    def test_module_level_inject_delegates_to_instance_run(self):
        text = '{| class="wikitable"\n! Header\n! Title\n|-\n| data\n| data\n|}'
        assert inject_r_column_into_tables(text) == AddRColumn(text).run()


class TestAddRColumnRunMethod:
    def test_run_uses_instance_state_directly(self):
        text = '{| class="wikitable"\n! #\n! Page title\n|-\n| 1\n| [[Aspirin]]\n|}'
        model = AddRColumn(text, {}, ["Aspirin"])
        result = model.run()
        assert "! R" in result
        assert "background:#C66A05" in result

    def test_run_no_tables_returns_original_text(self):
        model = AddRColumn("Plain text")
        assert model.run() == "Plain text"

    def test_two_instances_are_independent(self):
        text1 = '{| class="wikitable"\n! #\n! Page title\n|-\n| 1\n| [[Aspirin]]\n|}'
        text2 = '{| class="wikitable"\n! #\n! Page title\n|-\n| 1\n| [[Ibuprofen]]\n|}'
        model1 = AddRColumn(text1, {}, ["Aspirin"])
        model2 = AddRColumn(text2, {}, ["Ibuprofen"])
        result1 = model1.run()
        result2 = model2.run()
        assert "background:#C66A05" in result1
        assert "background:#C66A05" in result2
        assert model1.text != model2.text
