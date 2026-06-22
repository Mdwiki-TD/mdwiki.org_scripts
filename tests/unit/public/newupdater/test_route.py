"""
Unit tests for src/main_app/public/newupdater/route.py.
"""

from __future__ import annotations

import pytest


@pytest.mark.usefixtures("mock_app")
class TestNewupdaterRoute:
    def test_index_not_requires_auth(self, mock_client):
        resp = mock_client.get("/newupdater/")
        assert resp.status_code == 200

    def test_requires_auth(self, mock_client):
        resp = mock_client.get("/newupdater/save/test")
        assert resp.status_code == 302

    def test_get_with_login(self, mock_client, mock_login, monkeypatch):
        mock_login("TestUser")
        from src.main_app.shared.auth.current_user import CurrentUser

        monkeypatch.setattr(
            "src.main_app.public.auth.utils.load_user",
            lambda: CurrentUser(user_id=1, username="TestUser", access_token=b"t", access_secret=b"s"),
        )
        resp = mock_client.get("/newupdater/save/test")
        assert resp.status_code == 200
