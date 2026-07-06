"""Additional unit tests for add_rtt.py covering edge cases not in the original suite."""

from __future__ import annotations

import wikitextparser as wtp
from wikitextparser._cell import Cell


table = wtp.Table("""
{|
| A || colspan="2" | B
|-
| C || D || E
|}
""")

def test_table_data():
    assert table.data() == [['A', 'B', 'B'], ['C', 'D', 'E']]

def test_table_cells_len():
    cells = table.cells()
    assert len(cells[0]) == 3
    # assert cells[0] == [Cell('\n| A '), Cell('|| colspan="2" | B'), Cell('|| colspan="2" | B')]
    # assert cells[1] == [Cell('\n| C '), Cell('|| D '), Cell('|| E')]
    assert len(cells[1]) == 3

def test_table_cells():
    cells = table.cells()
    assert cells[0][2].string == Cell('|| colspan="2" | B').string
