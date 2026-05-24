""" """

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
)

bp_dup = Blueprint("dup", __name__, url_prefix="/dup")
logger = logging.getLogger(__name__)


@bp_dup.route("/", methods=["GET"])
def dup():
    return render_template("dup.html", title="Fix duplicate redirects")


__all__ = ["bp_dup"]
