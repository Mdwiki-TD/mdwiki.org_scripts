"""Unit tests for src/main_app/app_routes/public_jobs.py module."""

from __future__ import annotations

import pytest


@pytest.mark.usefixtures("mock_app")
class TestNewJobsRoutes:
    def test_jobs_list_requires_valid_type(self, mock_client):
        resp = mock_client.get("/jobs/invalid_type")
        assert resp.status_code == 404

    def test_all_jobs_list_page(self, mock_client):
        resp = mock_client.get("/jobs/list")
        assert resp.status_code == 200
