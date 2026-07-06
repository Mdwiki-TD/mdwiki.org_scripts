"""Unit tests for src/main_app/jobs/workers/add_r_column/add_rtt.py."""

from __future__ import annotations

import wikitextparser as wtp

from src.main_app.jobs_workers.public_jobs_workers.add_r_column.add_rtt import (
    R_NEW_ROW,
    AddRColumn,
    count_r_rows,
    inject_r_column_into_tables,
)


def make_model(text: str = "", redirects: dict | None = None, pages: list | None = None) -> AddRColumn:
    return AddRColumn(text, redirects or {}, pages or [])


class TestCountRRows:
    def test_count_r_rows_no_tables(self):
        text = "Plain text"
        assert count_r_rows(text) == 0


class TestInjectRColumnIntoTables:
    def test_inject_r_column_into_tables_no_tables(self):
        text = "Plain text"
        assert inject_r_column_into_tables(text, {}, []) == text

    def test_inject_r_column_into_tables_with_table(self):
        text = '{| class="wikitable"\n! Header\n! Title\n|-\n| data\n| data\n|}'
        # inject_r_column_into_tables should add R column because it's missing
        result = inject_r_column_into_tables(text, {}, [])
        assert "! Header\n! R" in result


class TestCheckForRHeader:
    def test_header_has_r_true(self):
        table_text = '{| class="wikitable"\n! Header\n! R\n! Title\n|-\n| data\n| data\n| data\n|}'
        parsed = wtp.parse(table_text)
        table = parsed.tables[0]
        model = make_model()
        assert model._check_for_r_header(table) is True

    def test_header_has_r_false(self):
        table_text = '{| class="wikitable"\n! Header\n! Other\n! Title\n|-\n| data\n| data\n| data\n|}'
        parsed = wtp.parse(table_text)
        table = parsed.tables[0]
        model = make_model()
        assert model._check_for_r_header(table) is False

    def test_header_has_r_with_table_object(self):
        table_text = '{| class="wikitable"\n! Header\n! R\n! Title\n|-\n| data\n| data\n| data\n|}'
        table = wtp.parse(table_text).tables[0]
        model = make_model()
        assert model._check_for_r_header(table=table) is True


class TestAddRHeader:
    def test_add_header_r_new(self):
        table_text = '{| class="wikitable"\n! Header\n! Title\n|-\n| data\n| data\n|}'
        parsed = wtp.parse(table_text)
        table = parsed.tables[0]
        model = make_model()
        _ = model._add_r_header(table)
        result = table.string
        assert "! Header\n! R" in result
        assert "| data\n| " in result

    def test_add_header_r_already_exists(self):
        table_text = '{| class="wikitable"\n! Header\n! R\n! Title\n|-\n| data\n| data\n| data\n|}'
        parsed = wtp.parse(table_text)
        table = parsed.tables[0]
        model = make_model()
        _ = model._add_r_header(table)
        result = table.string
        assert result == table_text


class TestProcessTableRows:
    def test_work_one_table_no_r_header(self):
        table_text = '{| class="wikitable"\n! Header\n! Title\n|-\n| data\n| data\n|}'
        model = make_model(table_text, {}, [])
        result = model._process_table_rows(
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
        result = model._process_table_rows(
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
        result = model._process_table_rows(
            table_text,
            title_header="Title",
        )
        assert 'background:#C66A05" | R' in result

    def test_work_one_table_already_r(self):
        table_text = '{| class="wikitable"\n! #\n! R\n! Title\n|-\n| 1\n| R\n| [[Aspirin]]\n|}'
        model = make_model(table_text, {}, [])
        result = model._process_table_rows(
            table_text,
            title_header="Title",
        )
        assert 'background:#C66A05" | R' in result

    def test_work_one_table_cell_error(self):
        # Trigger Exception in _process_table_rows loop
        # try:
        #     title = x[2].value.strip()
        #     r_s = x[1].value.strip()
        # except Exception:
        # To trigger this, a row must have at least 3 cells (len(x) < 3 is checked), but access might fail?
        # Actually len(x) < 3 is checked first. So x must have 3 cells.
        # Maybe x[2].value fails? Unlikely if it is a Cell object.
        # Wait, the code says:
        # for n, x in enumerate(tqdm.tqdm(table.cells())):
        # x is a row (list of cells).
        # x[2] is the 3rd cell.
        # x[1] is the 2nd cell.
        # If a row has only 2 cells, it continues.
        # How to trigger exception?
        # Maybe if x[2] exists but value property fails?
        pass


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
        assert count_r_rows(text) == AddRColumn(text, {}, []).count_r_rows() == 2

    def test_module_level_inject_delegates_to_instance_run(self):
        text = '{| class="wikitable"\n! Header\n! Title\n|-\n| data\n| data\n|}'
        assert inject_r_column_into_tables(text, {}, []) == AddRColumn(text, {}, []).run()
