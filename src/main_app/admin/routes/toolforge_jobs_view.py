"""
Admin-only routes for browsing the Toolforge jobs of this tool.

Thin HTTP layer: all the work is delegated to ToolforgeJobsService.
"""

from __future__ import annotations

import logging

from flask import Blueprint, flash, render_template
from flask.views import MethodView

from ..decorators import admin_required
from ..routes_services import Message, ToolforgeJobsService

logger = logging.getLogger(__name__)


class BaseJobsView(MethodView):
    """Base view holding the shared service and HTTP helpers."""

    decorators = [admin_required]

    def __init__(self, service: ToolforgeJobsService | None = None) -> None:
        self.service = service or ToolforgeJobsService()

    @staticmethod
    def _flash_all(messages: list[Message]) -> None:
        """Flash every message returned by the service."""
        for text, category in messages:
            flash(text, category)


class JobsView(BaseJobsView):
    """View to list the Toolforge jobs and their current status."""

    def get(self) -> str:
        """Render the jobs table with a status summary."""
        page = self.service.build_jobs_page()
        self._flash_all(page.messages)
        return render_template("admins/tf_jobs.html", **page.to_context())


class ToolforgeJobsView:
    """Registrar class to bind the jobs MethodView to a Blueprint."""

    @staticmethod
    def register(bp: Blueprint) -> None:
        """Register jobs URL rules on the provided blueprint."""
        view = JobsView.as_view("tf_jobs")
        bp.add_url_rule("/", view_func=view)


__all__ = [
    "ToolforgeJobsView",
]
