"""
conftest for unit tests
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

# ── jobs_workers fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_base_worker(monkeypatch: pytest.MonkeyPatch):
    """Mock external/non-DB dependencies for base worker tests.

    Keeps:
    - save_job_result_by_name  (filesystem write)
    - get_user_site            (external MediaWiki API)
    """
    mocks = {
        "get_user_site": MagicMock(return_value=MagicMock(name="mw_site")),
        "save_job_result_by_name": MagicMock(),
    }
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.save_job_result_by_name",
        mocks["save_job_result_by_name"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.get_user_site",
        mocks["get_user_site"],
    )
    return mocks
