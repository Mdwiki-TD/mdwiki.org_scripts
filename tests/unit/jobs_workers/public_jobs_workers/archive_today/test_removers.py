from __future__ import annotations

import wikitextparser as wtp

from src.main_app.jobs_workers.public_jobs_workers.archive_today.shared_wtp import (
    ArchiveParamsUrlsData,
    WtpUtils,
)
from src.main_app.jobs_workers.public_jobs_workers.archive_today.removers import (
    ArchiveTodayRemover,
    Cs2ArchiveTodayRemover,
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


class TestArchiveParamsUrlsData:
    def test_is_archiveis_url(self):
        data = ArchiveParamsUrlsData()
        assert data._is_archiveis_url("https://archive.today/12345") is True
        assert data._is_archiveis_url("http://archive.is/abc") is True
        assert data._is_archiveis_url("https://archive.ph/xyz") is True
        assert data._is_archiveis_url("https://archive.org/web/12345") is False
        assert data._is_archiveis_url("https://example.com") is False

    def test_build_start_patterns(self):
        data = ArchiveParamsUrlsData()
        patterns = data._build_start_patterns()
        assert "https://archive.today" in patterns
        assert "http://archive.today" in patterns
        assert "https://archive.is" in patterns


class TestCs2ArchiveTodayRemover:
    def test_remove_archive_today_from_cite_web(self):
        remover = Cs2ArchiveTodayRemover()
        text = (
            "{{cite web |title=Test |url=https://example.com "
            "|archive-url=https://archive.today/20201010/http://example.com "
            "|archive-date=2020-10-10 |url-status=dead}}"
        )
        new_text, removed = remover.remove(text)
        assert removed == 1
        assert "archive-url" not in new_text
        assert "archive-date" not in new_text
        assert "url=https://example.com" in new_text

    def test_remove_archive_is_sites(self):
        remover = Cs2ArchiveTodayRemover()
        for site in ArchiveParamsUrlsData.ARCHIVEIS_SITES:
            text = f"{{{{cite web |title=Test |archive-url=https://{site}/abc |archive-date=2020-01-01}}}}"
            new_text, removed = remover.remove(text)
            assert removed == 1
            assert "archive-url" not in new_text
            assert "archive-date" not in new_text

    def test_keep_other_archives(self):
        remover = Cs2ArchiveTodayRemover()
        text = (
            "{{cite web |title=Test |url=https://example.com "
            "|archive-url=https://web.archive.org/web/20201010/http://example.com "
            "|archive-date=2020-10-10}}"
        )
        new_text, removed = remover.remove(text)
        assert removed == 0
        assert text == new_text


class TestArchiveTodayRemover:
    def test_remove_webarchive_template(self):
        remover = ArchiveTodayRemover()
        text = "Some intro text {{webarchive |url=https://archive.today/2020.01.01 |date=2020-01-01}} and more text."
        new_text, count = remover.remove(text)
        assert count == 1
        assert "webarchive" not in new_text
        assert "Some intro text  and more text." == new_text

    def test_keep_webarchive_with_wayback(self):
        remover = ArchiveTodayRemover()
        text = "Text {{webarchive |url=https://web.archive.org/web/20200101/http://example.com}} more text."
        new_text, count = remover.remove(text)
        assert count == 0
        assert new_text == text

    def test_callable(self):
        remover = ArchiveTodayRemover()
        text = "{{webarchive |url=https://archive.today/123}}"
        new_text, count = remover(text)
        assert count == 1
        assert new_text == ""
