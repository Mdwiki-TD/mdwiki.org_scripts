"""Public routes for managing background jobs."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    flash,
    render_template,
)

from ..admin.decorators import admin_required
from ..jobs_workers.objects import JobData
from .auth.utils import user_login_required
from .shared_jobs_routes import JobsBp

logger = logging.getLogger(__name__)


class PublicJobsRoutes(JobsBp):
    """Jobs management routes."""

    def __init__(
        self,
        bp: Blueprint,
        jobs_data_infos: dict[str, JobData],
        bp_name: str,
    ) -> None:
        self.bp = bp
        self.jobs_data_infos: dict[str, JobData] = jobs_data_infos
        self.bp_name = bp_name
        super().__init__(jobs_data_infos, bp_name)

    def _setup_routes(self) -> None:
        routes = [
            ("/<string:job_type>", "GET", self.jobs_list),
            ("/<string:job_type>/<int:job_id>", "GET", self.job_detail),
            ("/<string:job_type>/<int:job_id>/expand", "GET", self.job_detail_expand),
            ("/job-file/<string:result_file>/<string:job_type>", "GET", user_login_required(self.read_job_result_file)),
            ("/<string:job_type>/<int:job_id>/cancel", "POST", user_login_required(self.cancel_job)),
            ("/<string:job_type>/start", "POST", user_login_required(self.start_job)),
            ("/<string:job_type>/<int:job_id>/delete", "POST", admin_required(self.delete_job)),
            ("/<string:job_type>/<int:job_id>/mark_as_completed", "POST", admin_required(self.mark_as_completed)),
            ("/list", "GET", self.all_jobs_list),
        ]
        for rule, method, target in routes:
            self.bp.route(rule, methods=[method])(target)

    def all_jobs_list(self) -> str:
        try:
            jobs = self.shared_service.job_service.list_jobs(limit=100)
        except Exception:  # pragma: no cover - defensive guard
            logger.exception("Unable to load jobs list.")
            flash("Unable to load jobs list.", "danger")
            jobs = []
        return render_template("jobs_templates/all_jobs_list.html", jobs=jobs)

__all__ = [
    "PublicJobsRoutes",
]
