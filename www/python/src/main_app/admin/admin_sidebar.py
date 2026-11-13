"""Admin sidebar ."""

from __future__ import annotations

import logging

from ..templates_markups.sidebar import Sidebar, SidebarGroup, SidebarItem

logger = logging.getLogger(__name__)


def load_admin_tools() -> list[SidebarGroup]:
    """Build the static sidebar menu structure.

    No Flask request/app context is touched here — URLs are resolved lazily
    by `SidebarItem.resolve_href()` at render time — so this result is safe
    to cache for the lifetime of the process.
    """
    main_group = SidebarGroup(
        id="main",
        title="Main",
        icon="bi-file-text",
        items=[],
    )

    users_group = SidebarGroup(
        id="users",
        title="Users",
        icon="bi-person",
        items=[
            SidebarItem.dashboard_item(
                "admins",
                "Admins",
                "bi-person-gear",
                "admin_panel.admins.dashboard",
                "/admin_panel/admins/",
            ),
            SidebarItem.dashboard_item(
                "users",
                "Users",
                "bi-person",
                "admin_panel.users.dashboard",
                "/admin_panel/users/",
            ),
        ],
    )
    settings_group = SidebarGroup(
        id="settings",
        title="Settings",
        icon="bi-sliders",
        items=[
            SidebarItem.dashboard_item(
                "settings",
                "Settings",
                "bi-gear",
                "admin_panel.settings.dashboard",
                "/admin_panel/settings/",
            ),
            SidebarItem(
                id="db_admin",
                requires_admin=True,
                fallback_href="/admin_panel/db_admin",
                title="DB admin",
                icon="bi-database",
            ),
        ],
    )

    errors_group = SidebarGroup(
        id="errors_group",
        title="Errors",
        icon="bi-exclamation-triangle",
        items=[
            SidebarItem.dashboard_item(
                "errors",
                "App Errors",
                "bi-exclamation-triangle",
                "admin_panel.errors.dashboard",
                "/admin_panel/errors/",
            ),
            SidebarItem(
                id="error_logs",
                requires_admin=True,
                fallback_href="/admin_panel/error-logs",
                title="Request Errors logs",
                icon="bi-exclamation-triangle",
            ),
        ],
    )

    other_group = SidebarGroup(
        id="other_group",
        title="Other",
        icon="bi-exclamation-triangle",
        items=[
            SidebarItem(
                id="tf_jobs",
                requires_admin=True,
                fallback_href="/admin_panel/tfj",
                title="ToolForge Jobs",
                icon="bi-hdd-network",
            ),
        ],
    )

    return [
        main_group,
        users_group,
        settings_group,
        errors_group,
        other_group,
    ]


def create_admin_sidebar(
    path: str,
    is_admin: bool = False,
    list_items: list[SidebarGroup] | None = None,
) -> str:
    """
    Generate sidebar HTML structure based on menu definitions.

    This is the public entry point used by the Jinja template.
    """
    main_menu = list_items or load_admin_tools()
    sidebar = Sidebar(main_menu)
    return sidebar.render(path, is_admin=is_admin)


__all__ = [
    "create_admin_sidebar",
]
