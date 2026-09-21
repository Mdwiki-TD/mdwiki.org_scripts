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
