""" """

from dataclasses import dataclass, field
from typing import Any

from flask import Blueprint, Flask

from ..jobs_workers.public_jobs_workers.workers_list_public import jobs_data_public
from .auth.routes import AuthView
from .fixred import FixRedView
from .main_routes import MainRoutes
from .newupdater.route import NewUpdaterRoutes
from .profile import ProfileView
from .public_jobs import PublicJobsRoutes


@dataclass(frozen=True)
class PublicRouteModule:
    route_cls: type
    name: str
    url_prefix: str = ""
    extra_kwargs: dict[str, Any] = field(default_factory=dict)


PUBLIC_ROUTE_MODULES: list[PublicRouteModule] = [
    PublicRouteModule(MainRoutes, "main", ""),
    PublicRouteModule(AuthView, "auth", ""),  # /auth
    PublicRouteModule(ProfileView, "profile", "/profile"),
    PublicRouteModule(FixRedView, "fixred", "/fixred"),
    PublicRouteModule(NewUpdaterRoutes, "newupdater", "/newupdater"),
    PublicRouteModule(
        PublicJobsRoutes,
        "public_jobs",
        "/jobs",
        extra_kwargs={
            "jobs_data_infos": jobs_data_public,
            "bp_name": "public_jobs",
        },
    ),
]


class RouteRegistrar:
    """Registers all route blueprints on a Flask app."""

    @staticmethod
    def register(app: Flask):
        for module in PUBLIC_ROUTE_MODULES:
            bp = Blueprint(module.name, __name__, url_prefix=module.url_prefix)
            module.route_cls(**module.extra_kwargs).register(bp)
            app.register_blueprint(bp)


__all__ = [
    "RouteRegistrar",
]
