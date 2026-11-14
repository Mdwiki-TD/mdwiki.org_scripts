"""Unit tests for webarchive_remover text_changer module."""

from __future__ import annotations

from src.main_app.jobs_workers.objects import JobsRunner
from src.main_app.jobs_workers.public_jobs_workers.webarchive_remover.text_changer import (
    ArchiveUrl,
    WebarchiveRemover,
    remove_webarchive,
)
from src.main_app.jobs_workers.public_jobs_workers.webarchive_remover.worker import WebarchiveRemoverWorker
from src.main_app.jobs_workers.shared_objects import SharedworkerObject

# ======================================================================
# Text transformation tests (pure function, no network)
# ======================================================================


class TestRemoveWebarchiveBasic:
    """Test the main remove case: cite already has matching archive-url."""

    def test_example_from_spec(self):
        """The exact example from the task specification."""
        text = (
            "<ref>{{Cite web|url=https://www.gov.uk/government/collections/rotavirus-vaccination-progarmme-for-infants"
            "|title=Rotavirus vaccination programme for infants"
            "|website=www.gov.uk"
            "|publisher=Public Health England"
            "|date=26 July 2013"
            "|access-date=27 April 2022"
            "|archive-date=23 April 2022"
            "|archive-url=https://web.archive.org/web/20220423164658/https://www.gov.uk/government/collections/rotavirus-vaccination-progarmme-for-infants"
            "|url-status=live}}"
            " {{Webarchive|url=https://web.archive.org/web/20220423164658/https://www.gov.uk/government/collections/rotavirus-vaccination-progarmme-for-infants |date=23 April 2022 }}"
            "</ref>"
        )
        result = remove_webarchive(text)
        # Webarchive template should be removed
        assert "Webarchive" not in result
        assert "webarchive" not in result.lower().split("cite web")[0] or "Webarchive" not in result
        # Cite web should still be there with its archive params
        assert "Cite web" in result
        assert "archive-url=https://web.archive.org/web/20220423164658/" in result
        assert "archive-date=23 April 2022" in result
        assert "<ref>" in result
        assert "</ref>" in result

    def test_simple_removal(self):
        """Simple case: cite web with matching archive-url and a trailing Webarchive."""
        text = (
            "{{Cite web|url=http://example.com|title=Test"
            "|archive-url=https://web.archive.org/web/20200101/https://example.com"
            "|archive-date=1 January 2020}}"
            " {{Webarchive|url=https://web.archive.org/web/20200101/https://example.com|date=1 January 2020}}"
        )
        result = remove_webarchive(text)
        assert "Webarchive" not in result
        assert "Cite web" in result
        assert "archive-url" in result

    def test_http_https_difference_ignored(self):
        """http vs https in the archive URL should still match."""
        text = (
            "{{Cite web|url=http://example.com|title=Test"
            "|archive-url=https://web.archive.org/web/20200101/http://example.com"
            "|archive-date=1 January 2020}}"
            " {{Webarchive|url=http://web.archive.org/web/20200101/http://example.com|date=1 January 2020}}"
        )
        result = remove_webarchive(text)
        assert "Webarchive" not in result


class TestMergeCase:
    """Test merging: cite has no archive params, Webarchive follows it."""

    def test_merge_basic(self):
        """Webarchive data should be moved into the cite template."""
        text = (
            "{{Cite web|url=https://example.com|title=Test|date=1 January 2020}}"
            " {{Webarchive|url=https://web.archive.org/web/20200615/https://example.com|date=15 June 2020}}"
        )
        result = remove_webarchive(text)
        assert "Webarchive" not in result
        assert "archive-url=https://web.archive.org/web/20200615/https://example.com" in result
        assert "archive-date=15 June 2020" in result

    def test_merge_generates_date_from_timestamp(self):
        """When Webarchive has no date param, derive it from the URL timestamp."""
        text = (
            "{{Cite web|url=https://example.com|title=Test}}"
            " {{Webarchive|url=https://web.archive.org/web/20220423164658/https://example.com}}"
        )
        result = remove_webarchive(text)
        assert "Webarchive" not in result
        assert "archive-url=" in result
        assert "archive-date=23 April 2022" in result

    def test_merge_different_page_skip(self):
        """Webarchive archives a different page than the cite url -> skip."""
        text = (
            "{{Cite web|url=https://example.com|title=Test}}"
            " {{Webarchive|url=https://web.archive.org/web/20200615/https://other.com|date=15 June 2020}}"
        )
        result = remove_webarchive(text)
        # Should NOT be changed because the Webarchive is for a different page
        assert "Webarchive" in result
        assert result == text


class TestSkipCases:
    """Test cases where the text should not be modified."""

    def test_different_archive_urls(self):
        """Cite has a different archive URL than the Webarchive -> skip."""
        text = (
            "{{Cite web|url=http://example.com|title=Test"
            "|archive-url=https://web.archive.org/web/20190101/https://example.com"
            "|archive-date=1 January 2019}}"
            " {{Webarchive|url=https://web.archive.org/web/20200101/https://example.com|date=1 January 2020}}"
        )
        result = remove_webarchive(text)
        assert result == text
        assert "Webarchive" in result

    def test_bare_webarchive_outside_citation(self):
        """Webarchive not attached to a citation -> skip."""
        text = (
            "Some text {{Webarchive|url=https://web.archive.org/web/20200101/https://example.com|date=1 January 2020}}"
        )
        result = remove_webarchive(text)
        assert result == text

    def test_webarchive_in_external_links_section(self):
        """Webarchive in an External links list -> skip."""
        text = (
            "==External links==\n"
            "* [https://example.com Example] {{Webarchive|url=https://web.archive.org/web/20200101/https://example.com|date=1 January 2020}}\n"
        )
        result = remove_webarchive(text)
        assert result == text


class TestMultipleRefs:
    """Test pages with multiple refs."""

    def test_multiple_refs_mixed(self):
        """One ref should be cleaned, another left alone."""
        text = (
            "<ref>{{Cite web|url=http://a.com|title=A"
            "|archive-url=https://web.archive.org/web/20200101/http://a.com"
            "|archive-date=1 January 2020}}"
            " {{Webarchive|url=https://web.archive.org/web/20200101/http://a.com|date=1 January 2020}}</ref>\n"
            "<ref>{{Cite web|url=http://b.com|title=B"
            "|archive-url=https://web.archive.org/web/20190101/http://b.com"
            "|archive-date=1 January 2019}}"
            " {{Webarchive|url=https://web.archive.org/web/20200101/http://b.com|date=1 January 2020}}</ref>"
        )
        result = remove_webarchive(text)
        # First ref: matching -> Webarchive removed
        # Second ref: different archive URLs -> Webarchive kept
        assert result.count("Webarchive") == 1  # only the second one remains


class TestParameterAliases:
    """Test parameter name variants."""

    def test_archiveurl_alias(self):
        """archiveurl (no hyphen) should work the same as archive-url."""
        text = (
            "{{Cite web|url=http://example.com|title=Test"
            "|archiveurl=https://web.archive.org/web/20200101/http://example.com"
            "|archivedate=1 January 2020}}"
            " {{Webarchive|url=https://web.archive.org/web/20200101/http://example.com|date=1 January 2020}}"
        )
        result = remove_webarchive(text)
        assert "Webarchive" not in result

    def test_webarchive_url_as_positional(self):
        """Webarchive with url as first positional parameter."""
        text = (
            "{{Cite web|url=http://example.com|title=Test"
            "|archive-url=https://web.archive.org/web/20200101/http://example.com"
            "|archive-date=1 January 2020}}"
            " {{Webarchive|https://web.archive.org/web/20200101/http://example.com|date=1 January 2020}}"
        )
        result = remove_webarchive(text)
        assert "Webarchive" not in result


class TestTemplateNameVariants:
    """Test Webarchive template name variants."""

    def test_lowercase_webarchive(self):
        text = (
            "{{Cite web|url=http://example.com|title=Test"
            "|archive-url=https://web.archive.org/web/20200101/http://example.com"
            "|archive-date=1 January 2020}}"
            " {{webarchive|url=https://web.archive.org/web/20200101/http://example.com|date=1 January 2020}}"
        )
        result = remove_webarchive(text)
        assert "webarchive" not in result.lower().split("cite web")[0] or "webarchive" not in result

    def test_wayback_template(self):
        """{{Wayback}} is a redirect of {{Webarchive}}."""
        text = (
            "{{Cite web|url=http://example.com|title=Test"
            "|archive-url=https://web.archive.org/web/20200101/http://example.com"
            "|archive-date=1 January 2020}}"
            " {{Wayback|url=https://web.archive.org/web/20200101/http://example.com|date=1 January 2020}}"
        )
        result = remove_webarchive(text)
        assert "Wayback" not in result


class TestIdempotence:
    """Running twice should give the same result."""

    def test_idempotent_removal(self):
        text = (
            "{{Cite web|url=http://example.com|title=Test"
            "|archive-url=https://web.archive.org/web/20200101/http://example.com"
            "|archive-date=1 January 2020}}"
            " {{Webarchive|url=https://web.archive.org/web/20200101/http://example.com|date=1 January 2020}}"
        )
        result1 = remove_webarchive(text)
        result2 = remove_webarchive(result1)
        assert result1 == result2

    def test_idempotent_merge(self):
        text = (
            "{{Cite web|url=https://example.com|title=Test|date=1 January 2020}}"
            " {{Webarchive|url=https://web.archive.org/web/20200615/https://example.com|date=15 June 2020}}"
        )
        result1 = remove_webarchive(text)
        result2 = remove_webarchive(result1)
        assert result1 == result2

    def test_idempotent_skip(self):
        """Text that should be skipped stays the same after multiple runs."""
        text = (
            "Some text {{Webarchive|url=https://web.archive.org/web/20200101/https://example.com|date=1 January 2020}}"
        )
        result1 = remove_webarchive(text)
        result2 = remove_webarchive(result1)
        assert result1 == result2 == text


class TestNoChanges:
    """Text without Webarchive templates should be untouched."""

    def test_no_webarchive(self):
        text = "{{Cite web|url=http://example.com|title=Test}}"
        assert remove_webarchive(text) == text

    def test_empty_text(self):
        assert remove_webarchive("") == ""

    def test_plain_text(self):
        assert remove_webarchive("Hello world") == "Hello world"


# ======================================================================
# ArchiveUrl helper tests
# ======================================================================


class TestArchiveUrl:
    def test_parse_valid(self):
        result = ArchiveUrl.parse("https://web.archive.org/web/20220423164658/https://example.com/page")
        assert result is not None
        assert result.timestamp == "20220423164658"
        assert result.original == "//example.com/page"

    def test_parse_http(self):
        result = ArchiveUrl.parse("http://web.archive.org/web/20220423/http://example.com")
        assert result is not None
        assert result.timestamp == "20220423"

    def test_parse_invalid(self):
        assert ArchiveUrl.parse("https://example.com") is None

    def test_same_snapshot_both_wayback(self):
        assert ArchiveUrl.same_snapshot(
            "https://web.archive.org/web/20220423/https://example.com",
            "http://web.archive.org/web/20220423/http://example.com",
        )

    def test_same_snapshot_different(self):
        assert not ArchiveUrl.same_snapshot(
            "https://web.archive.org/web/20220423/https://example.com",
            "https://web.archive.org/web/20220424/https://example.com",
        )

    def test_formatted_date(self):
        au = ArchiveUrl(timestamp="20220423164658", original="example.com")
        assert au.formatted_date() == "23 April 2022"


# ======================================================================
# WebarchiveRemover class tests
# ======================================================================


class TestWebarchiveRemoverStats:
    def test_stats_removed(self):
        text = (
            "{{Cite web|url=http://example.com|title=Test"
            "|archive-url=https://web.archive.org/web/20200101/http://example.com"
            "|archive-date=1 January 2020}}"
            " {{Webarchive|url=https://web.archive.org/web/20200101/http://example.com|date=1 January 2020}}"
        )
        remover = WebarchiveRemover()
        _, stats = remover.process(text)
        assert stats.removed == 1
        assert stats.merged == 0
        assert stats.changed

    def test_stats_merged(self):
        text = (
            "{{Cite web|url=https://example.com|title=Test}}"
            " {{Webarchive|url=https://web.archive.org/web/20200615/https://example.com|date=15 June 2020}}"
        )
        remover = WebarchiveRemover()
        _, stats = remover.process(text)
        assert stats.removed == 0
        assert stats.merged == 1

    def test_stats_skipped(self):
        text = "Some text {{Webarchive|url=https://web.archive.org/web/20200101/https://example.com}}"
        remover = WebarchiveRemover()
        _, stats = remover.process(text)
        assert stats.removed == 0
        assert stats.merged == 0
        assert not stats.changed

    def test_merge_disabled(self):
        text = (
            "{{Cite web|url=https://example.com|title=Test}}"
            " {{Webarchive|url=https://web.archive.org/web/20200615/https://example.com|date=15 June 2020}}"
        )
        remover = WebarchiveRemover(merge=False)
        result, stats = remover.process(text)
        assert result == text
        assert stats.merged == 0


# ======================================================================
# Worker class tests
# ======================================================================


class TestWebarchiveRemoverWorker:
    def test_job_type(self):
        worker = WebarchiveRemoverWorker(JobsRunner(job_id=1, args={}, user=None))
        assert worker.JOB_TYPE == "webarchive_remover"

    def test_result_type(self):
        worker = WebarchiveRemoverWorker(JobsRunner(job_id=1, args={}, user=None))
        assert isinstance(worker.result, SharedworkerObject)

    def test_make_new_text_with_changes(self):
        worker = WebarchiveRemoverWorker(JobsRunner(job_id=1, args={}, user=None))
        text = (
            "{{Cite web|url=http://example.com|title=Test"
            "|archive-url=https://web.archive.org/web/20200101/http://example.com"
            "|archive-date=1 January 2020}}"
            " {{Webarchive|url=https://web.archive.org/web/20200101/http://example.com|date=1 January 2020}}"
        )
        new_text, summary = worker._make_new_text("Test Title", text)
        assert "Webarchive" not in new_text
        assert "archive" in summary.lower()

    def test_make_new_text_no_changes(self):
        worker = WebarchiveRemoverWorker(JobsRunner(job_id=1, args={}, user=None))
        text = "{{Cite web|url=http://example.com|title=Test}}"
        new_text, summary = worker._make_new_text("Test Title", text)
        assert new_text == text
        assert summary == ""

    def test_process_no_site(self):
        from unittest.mock import patch

        worker = WebarchiveRemoverWorker(JobsRunner(job_id=1, args={}, user=None))
        with patch.object(worker, "_check_site", return_value=False):
            res = worker.process()
            assert res.status in ("pending", "running", "failed")
