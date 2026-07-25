"""Public routes for managing background jobs."""

from __future__ import annotations

import logging
from typing import Any

from flask import (
    Blueprint,
    flash,
    render_template,
    request,
)
from flask.typing import ResponseReturnValue
from werkzeug.wrappers.response import Response

from ..admin.decorators import admin_required
from ..db.services import JobsService
from ..jobs_workers.objects import JobData
from .auth.utils import user_login_required
from .jobs_routes_utils import JobsBp

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
        self.bp.route("/<string:job_type>", methods=["GET"])(self.jobs_list)
        self.bp.route("/<string:job_type>/<int:job_id>", methods=["GET"])(self.job_detail)
        self.bp.route("/<string:job_type>/<int:job_id>/expand", methods=["GET"])(self.job_detail_expand)
        self.bp.route("/job-file/<string:result_file>/<string:job_type>", methods=["GET"])(
            user_login_required(self.read_job_result_file)
        )

        self.bp.route("/<string:job_type>/<int:job_id>/cancel", methods=["POST"])(user_login_required(self.cancel_job))
        self.bp.route("/<string:job_type>/start", methods=["POST"])(user_login_required(self.start_job))
        self.bp.route("/<string:job_type>/<int:job_id>/delete", methods=["POST"])(admin_required(self.delete_job))

        self.bp.route("/list", methods=["GET"])(self.all_jobs_list)

    def all_jobs_list(self) -> str:
        try:
            jobs = JobsService().list_jobs(limit=100)
        except Exception:  # pragma: no cover - defensive guard
            logger.exception("Unable to load jobs list.")
            flash("Unable to load jobs list.", "danger")
            jobs: list[Any] = []
        return render_template("jobs_templates/all_jobs_list.html", jobs=jobs)

    def cancel_job(self, job_type: str, job_id: int) -> Response:
        return self.cancel_running_job(job_type, job_id)

    def jobs_list(self, job_type: str) -> str:
        return self.jobs_lists(job_type)

    def job_detail(self, job_type: str, job_id: int) -> Response | str:
        return self.job_details(job_type, job_id)

    def job_detail_expand(self, job_type: str, job_id: int) -> Response | str:
        return self.job_details(job_type, job_id, expand_all=True)

    def start_job(self, job_type: str) -> ResponseReturnValue:
        args = request.form.to_dict()
        return self.start_new_job(job_type, args, check_can_run_bg_jobs=True)

    def delete_job(self, job_type: str, job_id: int) -> Response:
        return self.delete_job_record(job_type, job_id)

    def read_job_result_file(self, result_file: str, job_type: str) -> ResponseReturnValue:
        return self.read_job_file(result_file, job_type)


__all__ = [
    "PublicJobsRoutes",
]
