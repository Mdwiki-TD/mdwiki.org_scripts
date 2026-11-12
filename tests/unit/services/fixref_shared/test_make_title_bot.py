"""Unit tests for src/main_app/services/fixref_shared/make_title_bot.py module."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from src.main_app.services.fixref_shared.make_title_bot import TitleMaker, _cached_fetch_title


@pytest.fixture(autouse=True)
def clear_make_title_cache():
    _cached_fetch_title.cache_clear()
    yield
    _cached_fetch_title.cache_clear()


class TestMakeTitle:
    def test_empty_url_returns_empty(self):
        assert TitleMaker().make_title("") == ""
        assert TitleMaker().make_title("   ") == ""

    @patch("src.main_app.services.fixref_shared.make_title_bot.CitationApi.get_citation_title")
    def test_valid_response_returns_title(self, mock_get_citation):
        mock_get_citation.return_value = "Aspirin"
        result = TitleMaker().make_title("https://example.com/article")
        assert result == "Aspirin"

    @patch("src.main_app.services.fixref_shared.make_title_bot.CitationApi.get_citation_title")
    def test_empty_response_returns_empty(self, mock_get_citation):
        mock_get_citation.return_value = ""
        result = TitleMaker().make_title("https://example.com/empty")
        assert result == ""

    @patch("src.main_app.services.fixref_shared.make_title_bot.CitationApi.get_citation_title")
    def test_not_found_title_returns_empty(self, mock_get_citation):
        mock_get_citation.return_value = "Not found."
        result = TitleMaker().make_title("https://example.com/404")
        assert result == ""

    @patch("src.main_app.services.fixref_shared.make_title_bot.CitationApi.get_citation_title")
    def test_caching(self, mock_get_citation):
        mock_get_citation.return_value = "Cached Title"
        result1 = TitleMaker().make_title("https://example.com/cached")
        result2 = TitleMaker().make_title("https://example.com/cached")
        assert result1 == "Cached Title"
        assert result2 == "Cached Title"
        assert mock_get_citation.call_count == 1
