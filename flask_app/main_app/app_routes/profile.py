from __future__ import annotations

import logging

from flask import Blueprint, flash, g, render_template

from ..db.services import get_user_jobs_stats

logger = logging.getLogger(__name__)

bp_profile = Blueprint("profile", __name__, url_prefix="/profile")


@bp_profile.route("/", methods=["GET"])
def dashboard():
    user = getattr(g, "_current_user", None)
    if not user:
        flash("You must be logged in to view your profile.", "warning")
        return render_template("profile.html")

    try:
        data = get_user_jobs_stats(user.username)
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Unable to load user stats.")
        flash("Unable to load your job statistics.", "danger")
        data = {"stats": {}, "recent_jobs": []}

    return render_template(
        "profile.html",
        username=user.username,
        stats=data["stats"],
        recent_jobs=data["recent_jobs"],
    )


@bp_profile.route("/<string:user_name>", methods=["GET"])
def user_dashboard(user_name: str):
    try:
        data = get_user_jobs_stats(user_name)
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Unable to load user stats.")
        flash("Unable to load user job statistics.", "danger")
        data = {"stats": {}, "recent_jobs": []}

    return render_template(
        "profile.html",
        username=user_name,
        stats=data["stats"],
        recent_jobs=data["recent_jobs"],
    )


__all__ = ["bp_profile"]
