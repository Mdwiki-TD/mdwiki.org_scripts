"""Main routes for the application (homepage and favicon), built on MethodView."""

from __future__ import annotations

import logging

from flask import Blueprint, current_app, render_template, send_from_directory
from flask.typing import ResponseReturnValue
from flask.views import MethodView

from ...jobs_workers.public_jobs_workers.workers_list_public import (
    jobs_data_for_all_pages,
    jobs_data_one_page,
)

logger = logging.getLogger(__name__)


class MainIndexView(MethodView):
    """Render the application homepage."""

    def get(self) -> ResponseReturnValue:
        """Render the index page with the job catalogs for all and single page tools."""
        return render_template(
            "index.html",
            jobs_data_for_all_pages=jobs_data_for_all_pages,
            jobs_data_one_page=jobs_data_one_page,
        )


class FaviconView(MethodView):
    """Serve the site favicon from the static folder."""

    def get(self) -> ResponseReturnValue:
        """Stream ``favicon.ico`` from the configured static directory."""
        return send_from_directory(current_app.static_folder, "favicon.ico", mimetype="image/x-icon")


class MainRoutes:
    """Route registrar binding the main MethodViews to a Blueprint."""

    @classmethod
    def register(cls, bp: Blueprint) -> None:
        """Register the homepage and favicon views on the blueprint."""
        bp.add_url_rule(
            "/",
            view_func=MainIndexView.as_view("index"),
            methods=["GET"],
        )
        bp.add_url_rule(
            "/favicon.ico",
            view_func=FaviconView.as_view("favicon"),
            methods=["GET"],
        )


__all__ = [
    "FaviconView",
    "MainIndexView",
    "MainRoutes",
]
