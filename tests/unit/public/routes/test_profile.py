"""Unit tests for src/main_app/public/profile.py module."""

from __future__ import annotations

import pytest


@pytest.mark.usefixtures("mock_app")
class TestProfileRoutes:
    def test_profile_requires_login(self, mock_client):
        resp = mock_client.get("/profile/")
        # Should either show login prompt or redirect
        assert resp.status_code == 200

    def test_profile_page_with_login(self, mock_client, mock_login):
        mock_login("TestUser")
        resp = mock_client.get("/profile/")
        assert resp.status_code == 200

    def test_user_profile_page(self, mock_client):
        resp = mock_client.get("/profile/TestUser")
        assert resp.status_code == 200
