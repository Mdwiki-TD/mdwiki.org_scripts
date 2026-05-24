""" """

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
    request,
)

bp_fixred = Blueprint("fixred", __name__, url_prefix="/fixred")
logger = logging.getLogger(__name__)


@bp_fixred.route("/", methods=["GET"])
def fixred():
    title = request.values.get("title", "")

    result = None
    if title:
        logger.info(f"fixred triggered for title: {title}")
        # TODO: integrate fixred.py backend call directly
        result = f"Fix redirects job started for: {title}"

    return render_template(
        "fixred.html",
        title=title,
        result=result,
    )


__all__ = ["bp_fixred"]
