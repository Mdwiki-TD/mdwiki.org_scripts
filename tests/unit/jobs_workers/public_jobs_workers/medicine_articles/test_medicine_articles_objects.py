"""Unit tests for src/main_app/jobs_workers/public_jobs_workers/medicine_articles/objects.py."""

from __future__ import annotations

from src.main_app.jobs_workers.public_jobs_workers.medicine_articles.objects import (
    LangCount,
    MedicineArticlesSummary,
    MedicineArticlesWorkerObject,
)
from src.main_app.jobs_workers.shared_objects import WorkerMapping


class TestLangCount:
    def test_defaults(self):
        lc = LangCount(lang="en")
        assert lc.lang == "en"
        assert lc.count == 0
        assert lc.status == "pending"
        assert lc.error is None

    def test_mutable(self):
        lc = LangCount(lang="ar", count=1500, status="completed")
        assert lc.lang == "ar"
        assert lc.count == 1500
        assert lc.status == "completed"

    def test_to_json(self):
        lc = LangCount(lang="fr", count=42, status="completed", error=None)
        d = lc.to_json()
        assert d == {"lang": "fr", "count": 42, "status": "completed", "error": None}

    def test_to_json_with_error(self):
        lc = LangCount(lang="de", count=0, status="failed", error="db timeout")
        d = lc.to_json()
        assert d["lang"] == "de"
        assert d["error"] == "db timeout"


class TestMedicineArticlesSummary:
    def test_defaults(self):
        s = MedicineArticlesSummary()
        assert s.total_articles == 0
        assert s.total_articles_all_langs == 0
        assert s.total_languages == 0
        assert s.page_updated is False

    def test_mutable(self):
        s = MedicineArticlesSummary()
        s.total_articles = 100
        s.total_articles_all_langs = 5000
        s.total_languages = 50
        s.page_updated = True
        assert s.total_articles == 100
        assert s.total_articles_all_langs == 5000
        assert s.total_languages == 50
        assert s.page_updated is True

    def test_to_json(self):
        s = MedicineArticlesSummary(total_articles=10, total_languages=3)
        d = s.to_json()
        assert d["total_articles"] == 10
        assert d["total_languages"] == 3
        assert d["page_updated"] is False


class TestMedicineArticlesWorkerObject:
    def test_inherits_worker_mapping(self):
        obj = MedicineArticlesWorkerObject()
        assert isinstance(obj, WorkerMapping)

    def test_default_lists_are_empty(self):
        obj = MedicineArticlesWorkerObject()
        assert obj.languages == []

    def test_default_summary(self):
        obj = MedicineArticlesWorkerObject()
        assert obj.summary.total_articles == 0
        assert obj.summary.total_languages == 0

    def test_lists_are_independent(self):
        a = MedicineArticlesWorkerObject()
        b = MedicineArticlesWorkerObject()
        a.languages.append(LangCount(lang="en", count=10))
        assert len(b.languages) == 0

    def test_default_page_fields(self):
        obj = MedicineArticlesWorkerObject()
        assert obj.page_title == ""
        assert obj.page_url == ""

    def test_to_json(self):
        obj = MedicineArticlesWorkerObject(status="completed")
        obj.summary.total_languages = 5
        obj.languages.append(LangCount(lang="en", count=100, status="completed"))
        d = obj.to_json()
        assert d["status"] == "completed"
        assert d["summary"]["total_languages"] == 5
        assert len(d["languages"]) == 1
        assert d["languages"][0]["lang"] == "en"
        assert "page_title" in d
