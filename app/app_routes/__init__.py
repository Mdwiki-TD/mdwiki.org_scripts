"""

"""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
    send_from_directory,
)

bp_main = Blueprint("main", __name__)
logger = logging.getLogger(__name__)


@bp_main.get("/")
def index():
    return render_template(
        "index.html",
    )


@bp_main.get("/dup")
def dup():
    return render_template("dup.html", )


@bp_main.get("/fixred")
def fixred():
    return render_template("fixred.html", )


@bp_main.get("/redirect")
def redirect():
    return render_template("redirect.html", )


@bp_main.get("/mdwiki4")
def mdwiki4():
    return render_template("mdwiki4.html", )


@bp_main.get("/import-history")
def import_history():
    return render_template("import-history.html", )


@bp_main.get("/fixref")
def fixref():
    return render_template("fixref.html", )


@bp_main.get("/favicon.ico")
def favicon():
    return send_from_directory("static", "favicon.ico", mimetype="image/x-icon")


__all__ = ["bp_main"]
