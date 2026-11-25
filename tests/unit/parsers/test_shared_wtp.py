from __future__ import annotations

import wikitextparser as wtp
from src.main_app.parsers.shared_wtp import (
    WtpUtils,
)


class TestWtpUtils:
    def test_is_value_valid(self):
        parsed = wtp.parse("{{cite web |url=https://example.com |title= |empty= }}")
        temp = parsed.templates[0]

        assert WtpUtils.is_value_valid(temp.get_arg("url"), check_values=True) is True
        assert WtpUtils.is_value_valid(temp.get_arg("title"), check_values=True) is False
        assert WtpUtils.is_value_valid(temp.get_arg("empty"), check_values=True) is False
        assert WtpUtils.is_value_valid(temp.get_arg("nonexistent"), check_values=True) is False
        assert WtpUtils.is_value_valid(temp.get_arg("title"), check_values=False) is True

    def test_find_templates(self):
        parsed = wtp.parse("{{cite web |url=x}} {{cite book |title=y}} {{other |z=1}}")
        found = WtpUtils.find_templates(parsed, ["cite web", "cite journal"])
        assert len(found) == 1
        assert found[0].name.strip() == "cite web"

    def test_parse_templates(self):
        parsed = wtp.parse("{{cite_web |url=x}} {{cite_book |title=y}}")
        dict_templates = WtpUtils.parse_templates(parsed)
        assert "cite web" in dict_templates
        assert "cite book" in dict_templates

    def test_get_args(self):
        parsed = wtp.parse("{{cite web |url=https://example.com |archive-url= |Title=My Title}}")
        temp = parsed.templates[0]

        args = WtpUtils.get_args(temp, ["url", "Title"])
        assert len(args) == 2
        # check_values=True filters out empty archive-url
        args_with_empty = WtpUtils.get_args(temp, ["archive-url"], check_values=True)
        assert len(args_with_empty) == 0
        args_without_check = WtpUtils.get_args(temp, ["archive-url"], check_values=False)
        assert len(args_without_check) == 1

    def test_get_args_values(self):
        parsed = wtp.parse("{{cite web |url=https://example.com |title=Test Title }}")
        temp = parsed.templates[0]
        values = WtpUtils.get_args_values(temp, ["url", "title"])
        assert values == ["https://example.com", "Test Title"]

    def test_get_arg_value(self):
        parsed = wtp.parse("{{cite web |url=https://example.com }}")
        temp = parsed.templates[0]
        assert WtpUtils.get_arg_value(temp, ["url"]) == "https://example.com"
        assert WtpUtils.get_arg_value(temp, ["missing"]) == ""

    def test_get_text_templates_list(self):
        text = "{{webarchive |url=https://archive.today/123}} {{cite web |title=foo}}"
        templates = WtpUtils.get_text_templates_list(text, ["webarchive"])
        assert len(templates) == 1
        assert templates[0].name.strip() == "webarchive"

    def test_get_arg_value_from_text(self):
        text = "{{webarchive |url=https://archive.today/123 |date=2020}}"
        val = WtpUtils.get_arg_value_from_text(text, ["webarchive"], "url")
        assert val == "https://archive.today/123"
        val_none = WtpUtils.get_arg_value_from_text(text, ["nonexistent"], "url")
        assert val_none == ""
