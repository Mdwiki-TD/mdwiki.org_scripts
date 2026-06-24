"""Admin blueprint package."""

from flask import Blueprint

from .admin_panel import bp_admin
from .routes import (
    coordinators_module,
    jobs_module,
    settings_module,
    users_module,
)


def register_bp_admin_blueprints(_bp: Blueprint) -> None:
    _bp.register_blueprint(coordinators_module.bp)
    _bp.register_blueprint(users_module.bp)
    _bp.register_blueprint(settings_module.bp)
    _bp.register_blueprint(jobs_module.bp)


register_bp_admin_blueprints(bp_admin)
