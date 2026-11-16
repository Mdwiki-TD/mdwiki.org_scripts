"""Unit tests for src/main_app/jobs_workers/public_jobs_workers/medicine_articles/worker.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from src.main_app.jobs_workers.objects import JobsRunner
from src.main_app.jobs_workers.public_jobs_workers.medicine_articles.worker import (
    MedicineArticlesWorker,
)

WORKER_PATH = "src.main_app.jobs_workers.public_jobs_workers.medicine_articles.worker"


@pytest.fixture
def worker():
    return MedicineArticlesWorker(JobsRunner(job_id=1, user={"username": "test_user"}))


class TestMedicineArticlesWorker:
    @patch(f"{WORKER_PATH}.MwClientPage")
    @patch(f"{WORKER_PATH}.WikiReplicaDB")
    @patch("src.main_app.jobs_workers.base_worker.WikiSiteClient.get_user_site")
    def test_process_success(self, mock_get_user_site, mock_replica_db_cls, mock_page_cls, worker):
        mock_get_user_site.return_value = MagicMock()

        # WikiReplicaDB("enwiki").select_safe returns different results per call
        lang_rows = [
            {"ll_lang": "ar", "counts": 200},
            {"ll_lang": "fr", "counts": 300},
        ]
        total_rows = [{"articles": 1000}]

        mock_db_instance = MagicMock()
        mock_replica_db_cls.return_value = mock_db_instance
        mock_db_instance.select_safe.side_effect = [lang_rows, total_rows]

        mock_page = MagicMock()
        mock_page_cls.return_value = mock_page

        result = worker.process()

        assert result.status == "completed"
        assert result.summary.page_updated is True
        assert result.summary.total_articles == 1000
        # en not in lang_rows so it gets added with total_articles value
        # langs: fr=300, en=1000, ar=200 → sorted desc
        assert result.summary.total_languages == 3
        assert result.summary.total_articles_all_langs == 1500
        assert len(result.languages) == 3
        # sorted descending: en=1000, fr=300, ar=200
        assert result.languages[0].lang == "en"
        assert result.languages[0].count == 1000
        assert result.languages[1].lang == "fr"
        assert result.languages[2].lang == "ar"

        # MwClientPage.edit called with wikitext and "update"
        mock_page.edit.assert_called_once()
        call_args = mock_page.edit.call_args
        assert call_args[0][1] == "update"
        wikitext = call_args[0][0]
        assert "WikiProject Medicine/Total medical articles" in wikitext
        assert "sortable wikitable" in wikitext

    @patch(f"{WORKER_PATH}.MwClientPage")
    @patch(f"{WORKER_PATH}.WikiReplicaDB")
    @patch("src.main_app.jobs_workers.base_worker.WikiSiteClient.get_user_site")
    def test_process_en_already_in_lang_counts(self, mock_get_user_site, mock_replica_db_cls, mock_page_cls, worker):
        """When 'en' is already in the language counts, it should NOT be overwritten."""
        mock_get_user_site.return_value = MagicMock()

        lang_rows = [
            {"ll_lang": "en", "counts": 5000},
            {"ll_lang": "de", "counts": 100},
        ]
        total_rows = [{"articles": 5000}]

        mock_db_instance = MagicMock()
        mock_replica_db_cls.return_value = mock_db_instance
        mock_db_instance.select_safe.side_effect = [lang_rows, total_rows]

        mock_page = MagicMock()
        mock_page_cls.return_value = mock_page

        result = worker.process()

        assert result.status == "completed"
        # en=5000, de=100 → total = 5100
        assert result.summary.total_articles_all_langs == 5100
        assert result.summary.total_languages == 2
        # en not duplicated
        en_entries = [lc for lc in result.languages if lc.lang == "en"]
        assert len(en_entries) == 1
        assert en_entries[0].count == 5000

    @patch("src.main_app.jobs_workers.base_worker.WikiSiteClient.get_user_site")
    def test_process_no_site(self, mock_get_user_site, worker):
        mock_get_user_site.return_value = None
        result = worker.process()
        assert result.status == "failed"

    @patch(f"{WORKER_PATH}.WikiReplicaDB")
    @patch("src.main_app.jobs_workers.base_worker.WikiSiteClient.get_user_site")
    def test_process_fetch_lang_counts_error(self, mock_get_user_site, mock_replica_db_cls, worker):
        mock_get_user_site.return_value = MagicMock()
        mock_replica_db_cls.side_effect = Exception("db connection failed")

        result = worker.process()

        assert result.status == "failed"
        assert len(result.errors) > 0
        assert result.errors[0]["error_type"] == "Exception"

    @patch(f"{WORKER_PATH}.WikiReplicaDB")
    @patch("src.main_app.jobs_workers.base_worker.WikiSiteClient.get_user_site")
    def test_process_fetch_total_articles_error(self, mock_get_user_site, mock_replica_db_cls, worker):
        mock_get_user_site.return_value = MagicMock()

        # First call (lang counts) succeeds, second call (total) raises
        mock_db_instance = MagicMock()
        mock_replica_db_cls.return_value = mock_db_instance
        mock_db_instance.select_safe.side_effect = [
            [{"ll_lang": "ar", "counts": 10}],
            Exception("total query failed"),
        ]

        result = worker.process()

        assert result.status == "failed"
        assert len(result.errors) > 0

    @patch(f"{WORKER_PATH}.MwClientPage")
    @patch(f"{WORKER_PATH}.WikiReplicaDB")
    @patch("src.main_app.jobs_workers.base_worker.WikiSiteClient.get_user_site")
    def test_process_page_edit_error(self, mock_get_user_site, mock_replica_db_cls, mock_page_cls, worker):
        mock_get_user_site.return_value = MagicMock()

        lang_rows = [{"ll_lang": "en", "counts": 100}]
        total_rows = [{"articles": 100}]

        mock_db_instance = MagicMock()
        mock_replica_db_cls.return_value = mock_db_instance
        mock_db_instance.select_safe.side_effect = [lang_rows, total_rows]

        mock_page = MagicMock()
        mock_page_cls.return_value = mock_page
        mock_page.edit.side_effect = Exception("API edit failed")

        result = worker.process()

        assert result.status == "failed"
        assert result.summary.page_updated is False
        assert len(result.errors) > 0

    @patch(f"{WORKER_PATH}.MwClientPage")
    @patch(f"{WORKER_PATH}.WikiReplicaDB")
    @patch("src.main_app.jobs_workers.base_worker.WikiSiteClient.get_user_site")
    def test_process_sets_page_title(self, mock_get_user_site, mock_replica_db_cls, mock_page_cls, worker):
        mock_get_user_site.return_value = MagicMock()

        mock_db_instance = MagicMock()
        mock_replica_db_cls.return_value = mock_db_instance
        mock_db_instance.select_safe.side_effect = [
            [{"ll_lang": "fr", "counts": 5}],
            [{"articles": 50}],
        ]

        mock_page = MagicMock()
        mock_page_cls.return_value = mock_page

        import datetime

        year = datetime.datetime.now().year
        result = worker.process()

        expected_title = f"WikiProjectMed:WikiProject Medicine/Stats/Number of articles by language {year}"
        assert result.page_title == expected_title

    @patch(f"{WORKER_PATH}.WikiReplicaDB")
    @patch("src.main_app.jobs_workers.base_worker.WikiSiteClient.get_user_site")
    def test_fetch_total_articles_empty_result(self, mock_get_user_site, mock_replica_db_cls, worker):
        mock_get_user_site.return_value = MagicMock()

        mock_db_instance = MagicMock()
        mock_replica_db_cls.return_value = mock_db_instance
        mock_db_instance.select_safe.return_value = []

        # Call the helper directly
        total = worker._fetch_total_articles()
        assert total == 0


class TestBuildWikitext:
    @patch("src.main_app.jobs_workers.base_worker.WikiSiteClient.get_user_site")
    def test_wikitext_structure(self, mock_get_user_site, worker):
        mock_get_user_site.return_value = MagicMock()

        languages = {"en": 1000, "ar": 200}
        worker.result.summary.total_articles_all_langs = 1200

        text = worker._build_wikitext(languages)

        assert "{{:WPM:WikiProject Medicine/Total medical articles}}" in text
        assert "sortable wikitable" in text
        assert "!Lang" in text
        assert "!#" in text
        assert "!en" in text
        assert "|1,000" in text
        assert "!ar" in text
        assert "|200" in text
        assert "|}" in text

    @patch("src.main_app.jobs_workers.base_worker.WikiSiteClient.get_user_site")
    def test_wikitext_contains_totals_transclusion(self, mock_get_user_site, worker):
        mock_get_user_site.return_value = MagicMock()
        worker.result.summary.total_articles_all_langs = 500

        text = worker._build_wikitext({"fr": 500})

        assert text.startswith("{{:WPM:WikiProject Medicine/Total medical articles}}")

    @patch("src.main_app.jobs_workers.base_worker.WikiSiteClient.get_user_site")
    def test_wikitext_numbers_are_comma_separated(self, mock_get_user_site, worker):
        mock_get_user_site.return_value = MagicMock()
        worker.result.summary.total_articles_all_langs = 1234567

        text = worker._build_wikitext({"en": 1234567})

        assert "1,234,567" in text


class TestJobType:
    def test_job_type(self, worker):
        assert worker.JOB_TYPE == "medicine_articles"
        assert worker.job_type == "medicine_articles"
