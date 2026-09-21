"""Admin-only routes for managing user permissions, built on MethodView."""

from __future__ import annotations

import logging
from typing import Any

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask.typing import ResponseReturnValue
from flask.views import MethodView

from ...database.services import UsersService
from ..decorators import admin_required

logger = logging.getLogger(__name__)


class UserDashboardView(MethodView):
    """View rendering the user management dashboard."""

    decorators = [admin_required]

    def __init__(self) -> None:
        self.user_service = UsersService()

    def get(self) -> str:
        """List every user along with their permission flags."""
        try:
            users = self.user_service.list_users()
        except Exception as e:  # pragma: no cover - defensive guard
            logger.error("Error listing users: %s", e)
            flash("Error listing users", "error")
            users: list[Any] = []

        total = len(users)

        return render_template(
            "admins/users.html",
            users=users,
            total_users=total,
        )


class BaseTogglePermissionView(MethodView):
    """Base view toggling a single boolean permission flag for a user."""

    decorators = [admin_required]

    # Name of the submitted form field and of the permission being changed.
    form_field = "can_run_jobs"
    permission_label = "can_run_jobs"

    def __init__(self) -> None:
        self.user_service = UsersService()

    def post(self, user_id: int) -> ResponseReturnValue:
        """Flip the permission for ``user_id`` and redirect back to the dashboard."""
        desired = 1 if request.form.get(self.form_field, "0") == "1" else 0

        try:
            record = self._toggle(user_id, bool(desired))
        except LookupError:
            logger.exception("Unable to update user permissions.")
            flash(f"User with id {user_id} was not found", "warning")
        except Exception:  # pragma: no cover - defensive guard
            logger.exception("Unable to update user permissions.")
            flash("Unable to update user permissions. Please try again.", "danger")
        else:
            if record is None:
                flash("Unable to update user permissions. Please try again.", "danger")
            else:
                flash(f"User '{record.username}' permissions updated.", "success")
                logger.info("User '%s' [%s]=%s updated.", record.username, self.permission_label, desired)

        return redirect(url_for("adminpanel.users.dashboard"))

    def _toggle(self, user_id: int, enabled: bool) -> Any:
        """Persist the new flag value, returning the updated record (or None)."""
        raise NotImplementedError


class UpdateCanRunJobsView(BaseTogglePermissionView):
    """View toggling the ``can_run_jobs`` permission."""

    form_field = "can_run_jobs"
    permission_label = "can_run_jobs"

    def _toggle(self, user_id: int, enabled: bool) -> Any:
        return self.user_service.toggle_can_run_jobs(user_id, enabled)


class UpdateCanRunBgJobsView(BaseTogglePermissionView):
    """View toggling the ``can_run_bg_jobs`` permission."""

    form_field = "can_run_bg_jobs"
    permission_label = "can_run_bg_jobs"

    def _toggle(self, user_id: int, enabled: bool) -> Any:
        return self.user_service.toggle_can_run_bg_jobs(user_id, enabled)


class UsersRoutes:
    """User management routes registrar using class-based views."""

    @classmethod
    def register(cls, bp: Blueprint) -> None:
        """Register the dashboard and the two permission-toggle endpoints."""
        bp.add_url_rule(
            "/",
            view_func=UserDashboardView.as_view("dashboard"),
            methods=["GET"],
        )
        bp.add_url_rule(
            "/<int:user_id>/can_run_jobs",
            view_func=UpdateCanRunJobsView.as_view("update_can_run_jobs"),
            methods=["POST"],
        )
        bp.add_url_rule(
            "/<int:user_id>/can_run_bg_jobs",
            view_func=UpdateCanRunBgJobsView.as_view("update_can_run_bg_jobs"),
            methods=["POST"],
        )


__all__ = [
    "UsersRoutes",
]
