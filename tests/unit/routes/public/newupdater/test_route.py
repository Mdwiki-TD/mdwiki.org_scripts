"""
Unit tests for src/main_app/routes/public/newupdater/route.py.
"""

from __future__ import annotations

import pytest


@pytest.mark.usefixtures("mock_app")
class TestNewupdaterRoute:
    def test_index_not_requires_auth(self, test_client):
        resp = test_client.get("/newupdater/")
        assert resp.status_code == 200

    def test_requires_auth(self, test_client):
        resp = test_client.get("/newupdater/save/test")
        assert resp.status_code == 302

    def test_get_with_login(self, test_client, monkeypatch):

        with test_client.session_transaction() as session:
            session["username"] = "TestUser"

        from src.main_app.services.auth.current_user import CurrentUser

        monkeypatch.setattr(
            "src.main_app.decorators.auth_decorators.CurrentUserResolver.get_current_user",
            lambda: CurrentUser(user_id=1, username="TestUser", access_token=b"t", access_secret=b"s"),
        )
        resp = test_client.get("/newupdater/save/test")
        assert resp.status_code == 200
