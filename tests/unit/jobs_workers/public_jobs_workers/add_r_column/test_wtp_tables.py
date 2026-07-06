"""Additional unit tests for add_rtt.py covering edge cases not in the original suite."""

from __future__ import annotations

import wikitextparser as wtp
from wikitextparser._cell import Cell


table = wtp.Table("""
{|
| A || colspan="2" | B
|- test="test"
| class='ss' | C || D || E
|}
""")

def test_table_data():
    assert table.data() == [['A', 'B', 'B'], ['C', 'D', 'E']]
    assert table.row_attrs == [{"test":"test"}]
    table.row_attrs = [{"test":"test!"}]
    assert '|- test="test!"' in table.string

def test_table_cells_len():
    cells = table.cells()
    assert len(cells[0]) == 3
    # assert cells[0] == [Cell('\n| A '), Cell('|| colspan="2" | B'), Cell('|| colspan="2" | B')]
    # assert cells[1] == [Cell('\n| C '), Cell('|| D '), Cell('|| E')]
    assert len(cells[1]) == 3

def test_table_cells():
    cells = table.cells()
    assert cells[0][2].string == Cell('|| colspan="2" | B').string


table_header = wtp.Table("""
{|
! Head1
! Head2
|-
| C || D
|}
""")

def test_table_head_cells():
    cells = table_header.cells()
    assert cells[0][1].string == Cell('\n! Head2').string

def test_table_head_cells_text():
    cells = table_header.cells()

    assert cells[0][1].is_header is True

    assert cells[1][1].string == Cell('|| D').string
    assert Cell('|| D').is_header is False
