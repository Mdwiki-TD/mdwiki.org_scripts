"""Regression tests pinning the endpoint names that templates and JS depend on.

Refactoring ``fixred``, ``newupdater`` and ``main_routes`` to MethodView must not
break any ``url_for(...)`` call already shipped in the templates. These tests fail
the moment an endpoint is renamed or dropped.
"""

from __future__ import annotations

import pytest


@pytest.mark.usefixtures("mock_app")
class TestEndpointNames:
    """Every endpoint referenced by a template/JS ``url_for`` must still resolve."""

    def test_main_endpoints_resolve(self, mock_app):
        from flask import url_for

        with mock_app.test_request_context():
            assert url_for("main.index") == "/"
            assert url_for("main.favicon") == "/favicon.ico"

    def test_fixred_endpoints_resolve(self, mock_app):
        from flask import url_for

        with mock_app.test_request_context():
            assert url_for("fixred.index") == "/fixred/"
            # Legacy POST alias kept for templates/fixred_one.html
            assert url_for("fixred.fixred_post") == "/fixred/"

    def test_newupdater_endpoints_resolve(self, mock_app):
        from flask import url_for

        with mock_app.test_request_context():
            assert url_for("newupdater.index") == "/newupdater/"
            assert url_for("newupdater.newupdater") == "/newupdater/update"
            assert url_for("newupdater.worker", title="Aspirin") == "/newupdater/Aspirin"
            assert url_for("newupdater.auto_save", title="Aspirin") == "/newupdater/save/Aspirin"

    def test_auth_and_profile_endpoints_resolve(self, mock_app):
        from flask import url_for

        with mock_app.test_request_context():
            # The auth blueprint registers with an empty url_prefix.
            assert url_for("auth.login") == "/login"
            assert url_for("auth.callback") == "/callback"
            assert url_for("auth.logout") == "/logout"
            assert url_for("profile.dashboard") == "/profile/"


@pytest.mark.usefixtures("mock_app")
class TestLegacyAliasBehaviour:
    """The legacy ``fixred.fixred_post`` alias must behave like the unified POST."""

    def test_legacy_post_alias_requires_auth(self, mock_client):
        resp = mock_client.post("/fixred/", data={"title": "Test"})
        assert resp.status_code == 302
        assert "login" in resp.headers["Location"]

    def test_index_and_alias_share_a_url(self, mock_app):
        from flask import url_for

        with mock_app.test_request_context():
            assert url_for("fixred.index") == url_for("fixred.fixred_post")

    def test_newupdater_index_is_public(self, mock_client):
        # index has no oauth_required, unlike worker/auto_save
        resp = mock_client.get("/newupdater/")
        assert resp.status_code == 200

    def test_newupdater_worker_requires_auth(self, mock_client):
        resp = mock_client.get("/newupdater/save/Some_Page")
        assert resp.status_code == 302
        assert "login" in resp.headers["Location"]
