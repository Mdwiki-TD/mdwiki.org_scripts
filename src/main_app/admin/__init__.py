"""Admin blueprint package."""

from flask import Blueprint, Flask

from ..jobs_workers.admin_jobs_workers.workers_list import jobs_data_admins
from .admin_panel import AdminPanel
from .routes import (
    AdminJobsRoutes,
    CoordinatorsRoutes,
    SettingsRoutes,
    UsersRoutes,
)


def register_bp_admin_blueprints(app: Flask) -> None:
    bp_admin = Blueprint("adminpanel", __name__, url_prefix="/admin")
    admin_model = AdminPanel(bp_admin)  # noqa: F841

    bp_coords = Blueprint("coordinators", __name__, url_prefix="/coordinators")
    coords_model = CoordinatorsRoutes(bp_coords)

    bp_users = Blueprint("users", __name__, url_prefix="/users")
    users_model = UsersRoutes(bp_users)

    # Settings module
    bp_settings = Blueprint("settings", __name__, url_prefix="/settings")
    settings_module = SettingsRoutes(bp_settings)

    # Public API module
    jobs_module = AdminJobsRoutes(
        bp=Blueprint("jobs", __name__, url_prefix="/jobs"),
        jobs_data_infos=jobs_data_admins,
        bp_name="adminpanel.jobs",
    )

    # Register blueprints
    bp_admin.register_blueprint(coords_model.bp)
    bp_admin.register_blueprint(users_model.bp)
    bp_admin.register_blueprint(settings_module.bp)
    bp_admin.register_blueprint(jobs_module.bp)

    app.register_blueprint(bp_admin)


__all__ = [
    "register_bp_admin_blueprints",
]
