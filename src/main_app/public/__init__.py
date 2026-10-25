""" """

from flask import Blueprint, Flask

from ..jobs_workers.public_jobs_workers.workers_list_public import jobs_data_public
from .auth.routes import AuthView
from .fixred import FixRedView
from .main_routes import MainRoutes
from .newupdater.route import NewUpdaterRoutes
from .profile import ProfileView
from .public_jobs import PublicJobsRoutes

from ..models import RouteModule

PUBLIC_ROUTE_MODULES: list[RouteModule] = [
    RouteModule(MainRoutes, "main", ""),
    RouteModule(AuthView, "auth", ""),  # /auth
    RouteModule(ProfileView, "profile", "/profile"),
    RouteModule(FixRedView, "fixred", "/fixred"),
    RouteModule(NewUpdaterRoutes, "newupdater", "/newupdater"),
    RouteModule(
        PublicJobsRoutes,
        "public_jobs",
        "/jobs",
        extra_kwargs={
            "jobs_data_infos": jobs_data_public,
            "bp_name": "public_jobs",
        },
    ),
]


class PublicRouteRegister:
    """Registers all route blueprints on a Flask app."""

    @staticmethod
    def register(app: Flask) -> None:
        for module in PUBLIC_ROUTE_MODULES:
            bp = Blueprint(module.name, __name__, url_prefix=module.url_prefix)
            instance = module.route_cls(**module.extra_kwargs)
            instance.register(bp)
            app.register_blueprint(bp)


__all__ = [
    "PublicRouteRegister",
]
