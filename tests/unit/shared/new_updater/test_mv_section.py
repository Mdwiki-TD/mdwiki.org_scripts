"""Unit tests for src/main_app/shared/new_updater/mv_section.py."""

from __future__ import annotations

from src.main_app.shared.new_updater.mv_section import MoveExternalLinksSection


class TestMoveExternalLinksSection:
    def test_no_external_links(self):
        text = "== Summary ==\nSome text.\n"
        bot = MoveExternalLinksSection(text)
        assert bot.new_text == text

    def test_external_links_section_detected(self):
        text = "== Summary ==\nText.\n== External links ==\n* link1\n"
        bot = MoveExternalLinksSection(text)
        assert bot.ext_sec != ""

    def test_empty_text(self):
        bot = MoveExternalLinksSection("")
        assert bot.new_text == ""

    def test_make_new_txt_returns_string(self):
        text = "== Summary ==\nText.\n== External links ==\n* link1\n"
        bot = MoveExternalLinksSection(text)
        result = bot.make_new_txt()
        assert result == """== Summary ==\nText.\n== External links ==\n* link1\n"""

    def test_no_sections(self):
        text = "Just some text without sections."
        bot = MoveExternalLinksSection(text)
        assert bot.ext_sec == ""
