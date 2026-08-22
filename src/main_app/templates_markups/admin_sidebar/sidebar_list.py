"""
"""

from __future__ import annotations

import functools

from .objects import (
    SidebarItem,
    SidebarGroup,
    dashboard_item,
)

@functools.lru_cache(maxsize=1)
def load_groups_menu() -> list[SidebarGroup]:
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
            dashboard_item(
                "admins",
                "Coordinators",
                "bi-person-gear",
                "adminpanel.coordinators.dashboard",
                "/adminpanel/coordinators/",
            ),
            dashboard_item(
                "users",
                "Users",
                "bi-person",
                "adminpanel.users.dashboard",
                "/adminpanel/users/",
            ),
        ],
    )
    settings_group = SidebarGroup(
        id="settings",
        title="Settings",
        icon="bi-sliders",
        items=[
            dashboard_item(
                "settings",
                "Settings",
                "bi-gear",
                "adminpanel.settings.dashboard",
                "/adminpanel/settings/",
            ),
            dashboard_item(
                "errors",
                "App Errors",
                "bi-exclamation-triangle",
                "adminpanel.errors.dashboard",
                "/adminpanel/errors/",
            ),
            SidebarItem(
                id="db_admin",
                requires_admin=1,
                fallback_href="/adminpanel/db_admin",
                title="DB admin",
                icon="bi-database",
            ),
        ],
    )

    return [
        main_group,
        users_group,
        settings_group,
    ]

__all__ = [
    "load_groups_menu",
]
