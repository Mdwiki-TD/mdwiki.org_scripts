""" """

from __future__ import annotations

from .mapping import NavLink

main_nav_list = [
    NavLink(
        text="New Jobs",
        icon="bi-sliders",
        url_endpoint="public_jobs.all_jobs_list",
        title="New Jobs",
        path="/jobs/",
    ),
    NavLink(
        text="Admins",
        icon="bi-people-fill",
        url_endpoint="admin_panel.dashboard",
        path="/admin_panel",
        for_admins=True,
    ),
    NavLink(
        text="GitHub",
        icon="bi-github",
        static_url="https://github.com/MrIbrahem/mdwiki.org_scripts",
        link_target="_blank",
        path="",
    ),
]


__all__ = [
    "main_nav_list",
]
