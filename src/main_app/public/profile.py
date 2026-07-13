from __future__ import annotations

import logging

from flask import Blueprint, flash, render_template

from ..db.services import get_all_user_jobs_stats
from .auth.utils import load_user

logger = logging.getLogger(__name__)


class ProfileRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.bp.route("/", methods=["GET"])
        @self.bp.route("/<string:user_name>", methods=["GET"])
        def dashboard(user_name: str = "") -> str:
            user = load_user()

            if not user_name:
                if not user:
                    flash("You must be logged in to view your profile.", "warning")
                    return render_template("profile.html")

                user_name = user.username

            try:
                data = get_all_user_jobs_stats(user_name)
            except Exception:  # pragma: no cover - defensive guard
                logger.exception("Unable to load user stats.")
                flash("Unable to load user job statistics.", "danger")
                data = {
                    "stats": {"total": 0, "completed": 0, "failed": 0, "cancelled": 0},
                    "recent_jobs": [],
                }

            return render_template(
                "profile.html",
                username=user_name,
                stats=data["stats"],
                recent_jobs=data["recent_jobs"],
            )


__all__ = [
    "ProfileRoutes",
]
