"""Unit tests for src/main_app/templates_markups/admin_sidebar.py."""

from __future__ import annotations

from src.main_app.templates_markups.admin_sidebar import (
    SidebarItem,
    create_side,
    generate_list_item,
)


class TestSidebarItem:
    def test_create(self):
        item = SidebarItem(id="test", title="Test", fallback_href="/test", requires_admin=False)
        assert item.id == "test"
        assert item.requires_admin is False
        assert item.fallback_href == "/test"
        assert item.title == "Test"
        assert item.icon is None
        assert item.link_target is None
        assert item.disabled is False

    def test_with_icon(self):
        item = SidebarItem(id="x", title="X", fallback_href="/x", icon="bi-gear")
        assert item.icon == "bi-gear"


class TestGenerateListItem:
    def test_basic_link(self):
        item = SidebarItem(
            id="test", fallback_href="/test", title="Test Page", icon=None, link_target=None, disabled=False
        )
        html = generate_list_item(item)
        assert "/test" in html
        assert "Test Page" in html
        assert "<a" in html

    def test_with_icon(self):
        item = SidebarItem(
            id="test", fallback_href="/test", title="Test", icon="bi-gear", link_target=None, disabled=False
        )
        html = generate_list_item(item)
        assert "bi-gear" in html

    def test_with_target_blank(self):
        item = SidebarItem(
            id="test", fallback_href="/test", title="Test", icon="bi-gear", link_target="_blank", disabled=False
        )
        html = generate_list_item(item)
        assert "target='_blank'" in html

    def test_no_target_by_default(self):
        item = SidebarItem(id="test", fallback_href="/test", title="Test", icon=None, link_target=None, disabled=False)
        html = generate_list_item(item)
        assert "target=" not in html


class TestCreateSide:
    def test_returns_html_string(self, mock_app):
        with mock_app.test_request_context():
            html = create_side("admins", is_admin=True)
            assert isinstance(html, str)
            assert "<ul" in html

    def test_contains_coordinators_link(self, mock_app):
        with mock_app.test_request_context():
            html = create_side("admins", is_admin=True)
            assert "Coordinators" in html

    def test_contains_users_link(self, mock_app):
        with mock_app.test_request_context():
            html = create_side("admins", is_admin=True)
            assert "Users" in html
