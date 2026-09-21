"""Admin blueprint package."""

from dataclasses import dataclass, field
from typing import Any

from flask import Blueprint

from ...jobs_workers.admin_jobs_workers.workers_list import jobs_data_admins
from .coordinators import CoordinatorView
from .errors_route import CheckErrorsView
from .jobs import AdminJobsRoutes
from .settings import SettingsRoutes
from .users import UsersRoutes


@dataclass(frozen=True)
class AdminRouteModule:
    route_cls: type
    name: str
    url_prefix: str = ""
    extra_kwargs: dict[str, Any] = field(default_factory=dict)


ADMIN_ROUTE_MODULES: list[AdminRouteModule] = [
    AdminRouteModule(route_cls=CoordinatorView, name="coordinators", url_prefix="/coordinators"),
    AdminRouteModule(route_cls=UsersRoutes, name="users", url_prefix="/users"),
    AdminRouteModule(route_cls=SettingsRoutes, name="settings", url_prefix="/settings"),
    AdminRouteModule(
        route_cls=AdminJobsRoutes,
        name="jobs",
        url_prefix="/jobs",
        extra_kwargs={
            "jobs_data_infos": jobs_data_admins,
            "bp_name": "adminpanel.jobs",
        },
    ),
    AdminRouteModule(route_cls=CheckErrorsView, name="errors", url_prefix="/errors"),
]


class AdminRouteRegister:

    @staticmethod
    def register(bp_admin: Blueprint) -> None:
        for module in ADMIN_ROUTE_MODULES:
            bp = Blueprint(module.name, __name__, url_prefix=module.url_prefix)
            instance = module.route_cls(**module.extra_kwargs)
            instance.register(bp)
            bp_admin.register_blueprint(bp)


__all__ = [
    "AdminRouteRegister",
    "ADMIN_ROUTE_MODULES",
]
