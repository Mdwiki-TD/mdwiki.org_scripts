"""Generic job status pages: HTML view + JSON poller."""

from __future__ import annotations

import logging

from flask import Blueprint, abort, jsonify, render_template

from ...jobs.store import get_store

bp_jobs = Blueprint("jobs", __name__, url_prefix="/jobs")
logger = logging.getLogger(__name__)


@bp_jobs.get("/<job_id>")
def status(job_id: str):
    job = get_store().get(job_id)
    if job is None:
        abort(404)
    return render_template("jobs/status.html", job=job, title=f"Job {job_id}")


@bp_jobs.get("/<job_id>.json")
def status_json(job_id: str):
    job = get_store().get(job_id)
    if job is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(job.to_dict())


__all__ = ["bp_jobs"]
