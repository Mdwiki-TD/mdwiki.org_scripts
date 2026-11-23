"""Regression tests pinning the admin endpoint names templates and JS depend on.

Converting ``admin_panel``, ``routes/users`` and ``routes/settings`` to MethodView
must not break any ``url_for(...)`` call already shipped in the templates or the
sidebar/navbar markup. These tests fail the moment an endpoint is renamed.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from src.main_app.database.services import AdminService, UsersService


@pytest.mark.usefixtures("mock_app")
class TestAdminEndpointNames:
    """Every admin endpoint referenced by a template/navbar/sidebar must resolve."""

    def test_admin_panel_endpoint_resolves(self, mock_app):
        from flask import url_for

        # Referenced by src/main_app/templates_markups/navbar/navbar_list.py
        with mock_app.test_request_context():
            assert url_for("admin_panel.dashboard") == "/admin_panel/"

    def test_users_endpoints_resolve(self, mock_app):
        from flask import url_for

        with mock_app.test_request_context():
            assert url_for("admin_panel.users.dashboard") == "/admin_panel/users/"
            assert url_for("admin_panel.users.update_can_run_jobs", user_id=1) == "/admin_panel/users/1/can_run_jobs"
            assert (
                url_for("admin_panel.users.update_can_run_bg_jobs", user_id=1) == "/admin_panel/users/1/can_run_bg_jobs"
            )

    def test_settings_endpoints_resolve(self, mock_app):
        from flask import url_for

        with mock_app.test_request_context():
            assert url_for("admin_panel.settings.dashboard") == "/admin_panel/settings/"
            assert url_for("admin_panel.settings.create") == "/admin_panel/settings/create"
            assert url_for("admin_panel.settings.update") == "/admin_panel/settings/update"


@pytest.mark.usefixtures("mock_app")
class TestAdminEndpointGuards:
    """The refactored views must still be behind ``admin_required``."""

    def test_admin_dashboard_requires_login(self, mock_client):
        resp = mock_client.get("/admin_panel/")
        assert resp.status_code == 302
        assert "login" in resp.headers["Location"]

    def test_users_dashboard_requires_login(self, mock_client):
        resp = mock_client.get("/admin_panel/users/")
        assert resp.status_code == 302
        assert "login" in resp.headers["Location"]

    def test_settings_dashboard_requires_login(self, mock_client):
        resp = mock_client.get("/admin_panel/settings/")
        assert resp.status_code == 302
        assert "login" in resp.headers["Location"]

    def test_settings_create_requires_login(self, mock_client):
        resp = mock_client.post("/admin_panel/settings/create", data={})
        assert resp.status_code == 302
        assert "login" in resp.headers["Location"]

    def test_user_permission_toggle_requires_login(self, mock_client):
        resp = mock_client.post("/admin_panel/users/1/can_run_jobs", data={"can_run_jobs": "1"})
        assert resp.status_code == 302
        assert "login" in resp.headers["Location"]


@pytest.mark.usefixtures("mock_app")
class TestAdminBlueprintGuard:
    """The single blueprint-level ``admin_guard`` must cover every admin endpoint.

    Flask propagates a parent blueprint's ``before_request`` to its nested child
    blueprints, so registering the guard once on ``admin_panel`` protects the
    sub-blueprints (users, settings, admins, jobs, errors) too.
    """

    def test_guard_lets_active_admin_through(self, mock_client, monkeypatch):
        from types import SimpleNamespace

        admin_user = SimpleNamespace(username="test_admin", is_active_admin=True)
        monkeypatch.setattr(
            "src.main_app.decorators.admin_decorators.CurrentUserResolver.get_current_user", lambda: admin_user
        )

        resp = mock_client.get("/admin_panel/")
        assert resp.status_code == 200

    def test_guard_blocks_non_admin(self, mock_client, monkeypatch):
        from types import SimpleNamespace

        regular_user = SimpleNamespace(username="regular", is_active_admin=False)
        monkeypatch.setattr(
            "src.main_app.decorators.admin_decorators.CurrentUserResolver.get_current_user", lambda: regular_user
        )

        for url in ("/admin_panel/", "/admin_panel/users/", "/admin_panel/settings/", "/admin_panel/admins/"):
            resp = mock_client.get(url)
            assert resp.status_code == 403, f"{url} should be 403 for a non-admin, got {resp.status_code}"

    def test_guard_redirects_anonymous_user(self, mock_client):
        for url in ("/admin_panel/", "/admin_panel/users/", "/admin_panel/settings/", "/admin_panel/admins/"):
            resp = mock_client.get(url)
            assert resp.status_code == 302, f"{url} should redirect anonymous users, got {resp.status_code}"
            assert "login" in resp.headers["Location"]

    def test_guard_leaves_public_routes_untouched(self, mock_client):
        # The guard is scoped to the admin blueprint and must not leak elsewhere.
        resp = mock_client.get("/")
        assert resp.status_code == 200


@pytest.fixture()
def _fake_admin_user(monkeypatch):
    """Fake an authenticated admin user for tests that need it."""
    admin_user = SimpleNamespace(username="test_admin", is_active_admin=True)
    monkeypatch.setattr(
        "src.main_app.decorators.admin_decorators.CurrentUserResolver.get_current_user", lambda: admin_user
    )
    monkeypatch.setattr(
        "src.main_app.decorators.auth_decorators.CurrentUserResolver.get_current_user", lambda: admin_user
    )
    monkeypatch.setattr(
        "src.main_app.routes.public.routes_utils.CurrentUserResolver.get_current_user", lambda: admin_user
    )


@pytest.fixture
def client(mock_app):
    """Test client bound to mock_app."""
    return mock_app.test_client()


@pytest.mark.usefixtures("_fake_admin_user")
class TestAdminDashboard:
    """Tests for the admin dashboard."""

    def _seed_admin(self, username: str = "coord1", is_active: bool = True):
        """Seed an admin via real services."""
        UsersService().create_user(username)
        admin_service = AdminService()
        admin_service.add_admin(username)
        if not is_active:
            record = admin_service.get_record_by_id(
                admin_service.session.query(admin_service.model)
                .filter(admin_service.model.username == username)
                .first()
                .id
            )
            admin_service.set_admin_active(record.id, False)
        return admin_service.session.query(admin_service.model).filter(admin_service.model.username == username).first()

    def test_dashboard_requires_auth(self, client, mock_app):
        """Dashboard should return 200 for authenticated admin."""
        resp = client.get("/admin_panel/admins/")

        assert resp.status_code == 200

    def test_renders_with_admins(self, client):
        """Dashboard should list admins."""
        self._seed_admin("coord_active", is_active=True)

        resp = client.get("/admin_panel/admins/")

        assert resp.status_code == 200
        html = resp.data.decode()
        assert "coord_active" in html

    def test_renders_with_empty_list(self, client):
        """Dashboard should render with no admins."""
        resp = client.get("/admin_panel/admins/")

        assert resp.status_code == 200


@pytest.mark.usefixtures("_fake_admin_user")
class TestAddAdmin:
    """Tests for adding an admin."""

    def _seed_user(self, username: str = "new_user"):
        """Seed a user record for foreign key."""
        UsersService().create_user(username)

    def test_missing_username(self, client):
        """POST /add with empty username should redirect."""
        resp = client.post(
            "/admin_panel/admins/add",
            data={"username": ""},
        )

        assert resp.status_code == 302

    def test_user_not_found(self, client):
        """POST /add with non-existent user should redirect."""
        resp = client.post(
            "/admin_panel/admins/add",
            data={"username": "unknown_user"},
        )

        assert resp.status_code == 302

    def test_duplicate_user(self, client):
        """POST /add with existing admin should redirect."""
        self._seed_user("existing_user")
        admin_service = AdminService()
        admin_service.add_admin("existing_user")

        resp = client.post(
            "/admin_panel/admins/add",
            data={"username": "existing_user"},
        )

        assert resp.status_code == 302

    def test_success(self, client):
        """POST /add with valid new user should create admin."""
        self._seed_user("new_coord")

        resp = client.post(
            "/admin_panel/admins/add",
            data={"username": "new_coord"},
        )

        assert resp.status_code == 302
        admin_service = AdminService()
        admins = admin_service.list_admins()
        assert any(c.username == "new_coord" for c in admins)


@pytest.mark.usefixtures("_fake_admin_user")
class TestSetRecordActiveStatus:
    """Tests for activating/deactivating admins."""

    def _seed_admin(self, username: str = "toggle_coord"):
        """Seed an admin via real services."""
        UsersService().create_user(username)
        return AdminService().add_admin(username)

    def test_activate_success(self, client):
        """POST /<id>/activate should set is_active=True."""
        coord = self._seed_admin("activate_coord")
        AdminService().set_admin_active(coord.id, False)

        resp = client.post(f"/admin_panel/admins/{coord.id}/activate")

        assert resp.status_code == 302
        updated = AdminService().get_record_by_id(coord.id)
        assert updated.is_active is True

    def test_deactivate_success(self, client):
        """POST /<id>/deactivate should set is_active=False."""
        coord = self._seed_admin("deactivate_coord")

        resp = client.post(f"/admin_panel/admins/{coord.id}/deactivate")

        assert resp.status_code == 302
        updated = AdminService().get_record_by_id(coord.id)
        assert updated.is_active is False

    def test_not_found(self, client):
        """POST /<id>/activate with nonexistent id should redirect."""
        resp = client.post("/admin_panel/admins/99999/activate")

        assert resp.status_code == 302


@pytest.mark.usefixtures("_fake_admin_user")
class TestDeleteAdmin:
    """Tests for deleting an admin."""

    def _seed_admin(self, username: str = "del_coord"):
        """Seed an admin via real services."""
        UsersService().create_user(username)
        return AdminService().add_admin(username)

    def test_success(self, client):
        """POST /<id>/delete should remove the admin."""
        coord = self._seed_admin("del_coord_ok")

        resp = client.post(f"/admin_panel/admins/{coord.id}/delete")

        assert resp.status_code == 302
        assert AdminService().get_record_by_id(coord.id) is None

    def test_not_found(self, client):
        """POST /<id>/delete with nonexistent id should redirect."""
        resp = client.post("/admin_panel/admins/99999/delete")

        assert resp.status_code == 302
