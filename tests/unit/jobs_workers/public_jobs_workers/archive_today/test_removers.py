from __future__ import annotations

from src.main_app.jobs_workers.public_jobs_workers.archive_today.archive_params_data import ArchiveParamsUrlsData
from src.main_app.jobs_workers.public_jobs_workers.archive_today.removers import (
    ArchiveTodayRemover,
    Cs2ArchiveTodayRemover,
)


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
