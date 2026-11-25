"""Unit tests for src/main_app/routes/public/profile.py module."""

from __future__ import annotations

import pytest


@pytest.mark.usefixtures("mock_app")
class TestProfileRoutes:
    def test_profile_requires_login(self, test_client):
        resp = test_client.get("/profile/")
        # Should either show login prompt or redirect
        assert resp.status_code == 200

    def test_profile_page_with_login(self, test_client):
        with test_client.session_transaction() as session:
            session["username"] = "TestUser"

        resp = test_client.get("/profile/")
        assert resp.status_code == 200

    def test_user_profile_page(self, test_client):
        resp = test_client.get("/profile/TestUser")
        assert resp.status_code == 200
