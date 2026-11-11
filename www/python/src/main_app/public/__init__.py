"""Public Blueprints"""

from __future__ import annotations

from typing import Any

from flask import Blueprint, Flask

from ..jobs_workers.public_jobs_workers.workers_list_public import jobs_data_public
from ..models import RouteModule
from .auth_route import AuthView
from .fixred import FixRedView
from .main_routes import MainRoutes
from .newupdater.route import NewUpdaterRoutes
from .profile import ProfileView
from .shared_jobs_registrar import SharedJobRoutesRegistrar

PUBLIC_ROUTE_MODULES: list[RouteModule] = [
    RouteModule(MainRoutes, "main", ""),
    RouteModule(AuthView, "auth", ""),  # /auth
    RouteModule(ProfileView, "profile", "/profile"),
    RouteModule(FixRedView, "fixred", "/fixred"),
    RouteModule(NewUpdaterRoutes, "newupdater", "/newupdater"),
    RouteModule(
        SharedJobRoutesRegistrar,
        "public_jobs",
        "/jobs",
        extra_kwargs={
            "jobs_data_infos": jobs_data_public,
            "bp_name": "public_jobs",
            "register_all_jobs_list": True,
        },
    ),
]


class PublicRouteRegister:
    """Registers all route blueprints on a Flask app."""

    @staticmethod
    def register(app: Flask) -> None:
        for module in PUBLIC_ROUTE_MODULES:
            bp = Blueprint(module.name, __name__, url_prefix=module.url_prefix)
            instance = module.route_cls()
            instance.register(bp, **module.extra_kwargs)
            app.register_blueprint(bp)


__all__ = [
    "PublicRouteRegister",
]
