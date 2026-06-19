"""Public routes for managing background jobs."""

from __future__ import annotations

import logging
from typing import Any

from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask.typing import ResponseReturnValue
from werkzeug.wrappers.response import Response

from ..db.services import list_jobs
from ..jobs_workers.objects import JobData
from ..jobs_workers.public_jobs_workers.workers_list_public import jobs_data_public
from ..su_services import load_job_result
from .admin.admins_required import admin_required
from .jobs_routes_utils import (
    cancel_job_handler,
    delete_job_handler,
    job_detail_handler,
    jobs_list_handler,
    start_job_handler,
)

logger = logging.getLogger(__name__)

class PublicJobsRoutes:
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
        self._setup_routes()

    def _setup_routes(self) -> None:
        # ================================
        # All Jobs List route
        # ================================

        @self.bp.get("/list")
        def all_jobs_list() -> str:
            try:
                jobs = list_jobs(limit=100)
            except Exception:  # pragma: no cover - defensive guard
                logger.exception("Unable to load jobs list.")
                flash("Unable to load jobs list.", "danger")
                jobs: list[Any] = []
            return render_template("jobs_templates/all_jobs_list.html", jobs=jobs)

        # ================================
        # Cancel Jobs routes
        # ================================

        @self.bp.post("/<string:job_type>/<int:job_id>/cancel")
        def cancel_job(job_type: str, job_id: int) -> Response:
            if job_type not in self.jobs_data_infos:
                flash("Job type not found.", "warning")
                abort(404)

            result = cancel_job_handler(job_id, job_type)

            if result == "job_detail":
                return redirect(url_for(f"{self.bp_name}.job_detail", job_type=job_type, job_id=job_id))

            return redirect(url_for(f"{self.bp_name}.jobs_list", job_type=job_type))

        # ================================
        # Jobs List routes
        # ================================

        @self.bp.get("/<string:job_type>")
        def jobs_list(job_type: str) -> str:
            template_data: JobData | None = self.jobs_data_infos.get(job_type)
            if not template_data:
                abort(404)

            return jobs_list_handler(job_type, template_data, bp_name=self.bp_name)

        # ================================
        # Job Detail routes
        # ================================

        @self.bp.get("/<string:job_type>/<int:job_id>")
        def job_detail(job_type: str, job_id: int) -> Response | str:
            # Load template data
            template_data: JobData | None = self.jobs_data_infos.get(job_type)

            if not template_data:
                abort(404)

            return job_detail_handler(job_id, job_type, template_data, bp_name=self.bp_name)

        @self.bp.get("/<string:job_type>/<int:job_id>/expand")
        def job_detail_expand(job_type: str, job_id: int) -> Response | str:
            # Load template data
            template_data: JobData | None = self.jobs_data_infos.get(job_type)

            if not template_data:
                abort(404)

            return job_detail_handler(job_id, job_type, template_data, bp_name=self.bp_name, expand_all=True)

        # ================================
        # Start Job routes
        # ================================

        @self.bp.post("/<string:job_type>/start")
        def start_job(job_type: str) -> ResponseReturnValue:
            if job_type not in self.jobs_data_infos:
                abort(404)

            args = request.form.to_dict()

            job_id = start_job_handler(job_type, args, bp_name=self.bp_name)
            if not job_id:
                return redirect(url_for(f"{self.bp_name}.jobs_list", job_type=job_type))

            return redirect(url_for(f"{self.bp_name}.job_detail", job_type=job_type, job_id=job_id))

        # ================================
        # Delete Job routes
        # ================================

        @self.bp.post("/<string:job_type>/<int:job_id>/delete")
        @admin_required
        def delete_job(job_type: str, job_id: int) -> Response:
            if job_type not in self.jobs_data_infos:
                abort(404)
            result = delete_job_handler(job_id, job_type)

            if result == "job_detail":
                return redirect(url_for(f"{self.bp_name}.job_detail", job_type=job_type, job_id=job_id))

            return redirect(url_for(f"{self.bp_name}.jobs_list", job_type=job_type))

        @self.bp.get("/job-file/<string:result_file>/<string:job_type>")
        def read_job_result_file(result_file: str, job_type: str) -> ResponseReturnValue:
            """ """
            if job_type not in self.jobs_data_infos:
                abort(404)
            result_data = load_job_result(result_file)
            return jsonify(result_data)


# Public API module
jobs_public_module = PublicJobsRoutes(
    bp=Blueprint("public_jobs", __name__, url_prefix="/jobs"),
    jobs_data_infos=jobs_data_public,
    bp_name="public_jobs",
)

__all__ = [
    "jobs_public_module",
]
