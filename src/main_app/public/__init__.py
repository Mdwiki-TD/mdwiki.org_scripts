""" """

from flask import Flask

from ..admin.route import bp_admin
from .auth.routes import bp_auth
from .fixred import bp_fixred
from .main_routes import bp_main
from .newupdater.route import bp_newupdater
from .profile import bp_profile
from .public_jobs import jobs_public_module


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(bp_main)
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_admin)
    app.register_blueprint(bp_profile)

    app.register_blueprint(jobs_public_module.bp)
    app.register_blueprint(bp_newupdater)
    app.register_blueprint(bp_fixred)


__all__ = [
    "register_blueprints",
]
