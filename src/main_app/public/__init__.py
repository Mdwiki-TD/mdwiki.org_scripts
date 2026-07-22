""" """

from flask import Blueprint, Flask

from ..jobs_workers.public_jobs_workers.workers_list_public import jobs_data_public
from .auth.routes import AuthRoutes
from .fixred import FixRedRoutes
from .main_routes import MainRoutes
from .newupdater.route import NewUpdaterRoutes
from .profile import ProfileRoutes
from .public_jobs import PublicJobsRoutes


def register_blueprints(app: Flask) -> None:
    bp_main = Blueprint("main", __name__)
    main_model = MainRoutes(bp_main)

    # Public API module
    jobs_public_module = PublicJobsRoutes(
        bp=Blueprint("public_jobs", __name__, url_prefix="/jobs"),
        jobs_data_infos=jobs_data_public,
        bp_name="public_jobs",
    )

    bp_auth = Blueprint("auth", __name__)
    auth_model = AuthRoutes(bp_auth)

    bp_profile = Blueprint("profile", __name__, url_prefix="/profile")
    profile_model = ProfileRoutes(bp_profile)

    bp_fixred = Blueprint("fixred", __name__, url_prefix="/fixred")
    fixred_model = FixRedRoutes(bp_fixred)

    bp_newupdater = Blueprint("newupdater", __name__, url_prefix="/newupdater")
    newupdater_model = NewUpdaterRoutes(bp_newupdater)

    app.register_blueprint(auth_model.bp)
    app.register_blueprint(profile_model.bp)
    app.register_blueprint(main_model.bp)
    app.register_blueprint(jobs_public_module.bp)
    app.register_blueprint(newupdater_model.bp)
    app.register_blueprint(fixred_model.bp)


__all__ = [
    "register_blueprints",
]
