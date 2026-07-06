"""
test example from:
https://mdwiki.org/wiki/WikiProjectMed:WikiProject_Medicine/Popular_pages
"""

from __future__ import annotations

from src.main_app.jobs_workers.public_jobs_workers.add_r_column.add_rtt import (
    AddRColumn,
)

table_text = """
{| class="wikitable sortable"
! Rank
! R
! Page title
! Views
! Daily average
! Assessment
! Importance
|-
| 1
|
| [[test]]
| [https://pageviews.toolforge.org/?project=en.wikipedia.org&amp;start=2026-04-01&amp;end=2026-04-30&amp;pages=Sexual_intercourse&amp;redirects=1 {{FORMATNUM:343160}}]
| {{FORMATNUM:11438}}
| style="text-align:center; white-space:nowrap; font-weight:bold; background:#B2FF66" | [[:Category:B-Class articles|B]]
| style="text-align:center; white-space:nowrap; font-weight:bold; background:#ffc1ff" | [[:Category:Mid-importance articles|Mid]]
|-
| 2
|
| [[Suicide methods]]
| [https://pageviews.toolforge.org/?project=en.wikipedia.org&amp;start=2026-04-01&amp;end=2026-04-30&amp;pages=Suicide_methods&amp;redirects=1 {{FORMATNUM:290707}}]
| {{FORMATNUM:9690}}
| style="text-align:center; white-space:nowrap; font-weight:bold; background:#B2FF66" | [[:Category:B-Class articles|B]]
| style="text-align:center; white-space:nowrap; font-weight:bold; background:#ffd6ff" | [[:Category:Low-importance articles|Low]]
|-
|}
"""


class TestAddRColumn:
    def test_basic(self):
        pages = ["Sexual intercourse"]
        redirects = {"test": "Sexual intercourse"}
        model = AddRColumn(table_text, redirects, pages)
        result = model.run()
        first = (
            "| 1\n"
            '| style="text-align:center; white-space:nowrap; font-weight:bold; background:#C66A05" | R\n'
            "| [[test]]"
        )
        assert first in result
