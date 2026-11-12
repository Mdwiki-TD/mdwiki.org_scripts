"""Public Blueprints"""

from __future__ import annotations

from typing import Any

from flask import Blueprint, Flask

from ..jobs_workers.public_jobs_workers.workers_list_public import jobs_data_public
from ..models import RouteModule
from ..templates_markups import NavigationBar, main_nav_list
from .newupdater.route import NewUpdaterRoutes
from .routes import (
    AuthView,
    MainView,
    ProfileView,
)
from .routes.fixred import FixRedView
from .shared_jobs_registrar import SharedJobRoutesRegistrar

PUBLIC_ROUTE_MODULES: list[RouteModule] = [
    RouteModule(route_cls=MainView, name="main", url_prefix=""),
    RouteModule(route_cls=AuthView, name="auth", url_prefix=""),  # "/auth"
    RouteModule(route_cls=ProfileView, name="profile", url_prefix="/profile"),
    RouteModule(FixRedView, "fixred", "/fixred"),
    RouteModule(NewUpdaterRoutes, "newupdater", "/newupdater"),
    RouteModule(
        route_cls=SharedJobRoutesRegistrar,
        name="public_jobs",
        url_prefix="/jobs",
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
    def inject_navbar() -> dict[str, Any]:
        main_navbar = NavigationBar(main_nav_list)

        return {
            "main_navbar": main_navbar,
        }

    @classmethod
    def register(cls, app: Flask) -> None:
        app.context_processor(cls.inject_navbar)

        for module in PUBLIC_ROUTE_MODULES:
            bp = Blueprint(module.name, __name__, url_prefix=module.url_prefix)

            instance = module.route_cls()
            instance.register(bp, **module.extra_kwargs)
            app.register_blueprint(bp)


__all__ = [
    "PublicRouteRegister",
]
