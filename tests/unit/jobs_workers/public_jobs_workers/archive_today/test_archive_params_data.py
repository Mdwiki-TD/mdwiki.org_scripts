from __future__ import annotations

from src.main_app.jobs_workers.public_jobs_workers.archive_today.archive_params_data import ArchiveParamsUrlsData


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
