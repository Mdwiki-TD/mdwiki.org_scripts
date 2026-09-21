"""Regression tests pinning the admin endpoint names templates and JS depend on.

Converting ``admin_panel``, ``routes/users`` and ``routes/settings`` to MethodView
must not break any ``url_for(...)`` call already shipped in the templates or the
sidebar/navbar markup. These tests fail the moment an endpoint is renamed.
"""

from __future__ import annotations

import pytest


@pytest.mark.usefixtures("mock_app")
class TestAdminEndpointNames:
    """Every admin endpoint referenced by a template/navbar/sidebar must resolve."""

    def test_admin_panel_endpoint_resolves(self, mock_app):
        from flask import url_for

        # Referenced by src/main_app/templates_markups/navbar/navbar_list.py
        with mock_app.test_request_context():
            assert url_for("adminpanel.dashboard") == "/adminpanel/"

    def test_users_endpoints_resolve(self, mock_app):
        from flask import url_for

        with mock_app.test_request_context():
            assert url_for("adminpanel.users.dashboard") == "/adminpanel/users/"
            assert url_for("adminpanel.users.update_can_run_jobs", user_id=1) == "/adminpanel/users/1/can_run_jobs"
            assert (
                url_for("adminpanel.users.update_can_run_bg_jobs", user_id=1) == "/adminpanel/users/1/can_run_bg_jobs"
            )

    def test_settings_endpoints_resolve(self, mock_app):
        from flask import url_for

        with mock_app.test_request_context():
            assert url_for("adminpanel.settings.dashboard") == "/adminpanel/settings/"
            assert url_for("adminpanel.settings.create") == "/adminpanel/settings/create"
            assert url_for("adminpanel.settings.update") == "/adminpanel/settings/update"


@pytest.mark.usefixtures("mock_app")
class TestAdminEndpointGuards:
    """The refactored views must still be behind ``admin_required``."""

    def test_admin_dashboard_requires_login(self, mock_client):
        resp = mock_client.get("/adminpanel/")
        assert resp.status_code == 302
        assert "login" in resp.headers["Location"]

    def test_users_dashboard_requires_login(self, mock_client):
        resp = mock_client.get("/adminpanel/users/")
        assert resp.status_code == 302
        assert "login" in resp.headers["Location"]

    def test_settings_dashboard_requires_login(self, mock_client):
        resp = mock_client.get("/adminpanel/settings/")
        assert resp.status_code == 302
        assert "login" in resp.headers["Location"]

    def test_settings_create_requires_login(self, mock_client):
        resp = mock_client.post("/adminpanel/settings/create", data={})
        assert resp.status_code == 302
        assert "login" in resp.headers["Location"]

    def test_user_permission_toggle_requires_login(self, mock_client):
        resp = mock_client.post("/adminpanel/users/1/can_run_jobs", data={"can_run_jobs": "1"})
        assert resp.status_code == 302
        assert "login" in resp.headers["Location"]


@pytest.mark.usefixtures("mock_app")
class TestAdminBlueprintGuard:
    """The single blueprint-level ``admin_guard`` must cover every admin endpoint.

    Flask propagates a parent blueprint's ``before_request`` to its nested child
    blueprints, so registering the guard once on ``adminpanel`` protects the
    sub-blueprints (users, settings, coordinators, jobs, errors) too.
    """

    def test_guard_lets_active_admin_through(self, mock_client, monkeypatch):
        from types import SimpleNamespace

        admin_user = SimpleNamespace(username="test_admin", is_active_admin=True)
        monkeypatch.setattr("src.main_app.admin.decorators.get_current_user", lambda: admin_user)

        resp = mock_client.get("/adminpanel/")
        assert resp.status_code == 200

    def test_guard_blocks_non_admin(self, mock_client, monkeypatch):
        from types import SimpleNamespace

        regular_user = SimpleNamespace(username="regular", is_active_admin=False)
        monkeypatch.setattr("src.main_app.admin.decorators.get_current_user", lambda: regular_user)

        for url in ("/adminpanel/", "/adminpanel/users/", "/adminpanel/settings/", "/adminpanel/coordinators/"):
            resp = mock_client.get(url)
            assert resp.status_code == 403, f"{url} should be 403 for a non-admin, got {resp.status_code}"

    def test_guard_redirects_anonymous_user(self, mock_client):
        for url in ("/adminpanel/", "/adminpanel/users/", "/adminpanel/settings/", "/adminpanel/coordinators/"):
            resp = mock_client.get(url)
            assert resp.status_code == 302, f"{url} should redirect anonymous users, got {resp.status_code}"
            assert "login" in resp.headers["Location"]

    def test_guard_leaves_public_routes_untouched(self, mock_client):
        # The guard is scoped to the admin blueprint and must not leak elsewhere.
        resp = mock_client.get("/")
        assert resp.status_code == 200
