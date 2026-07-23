""""""

from __future__ import annotations

import logging

from flask import Blueprint, flash, g, render_template, request

from ..shared import fixred_one
from .auth.utils import oauth_required

# from .utils.routes_utils import can_run_jobs

logger = logging.getLogger(__name__)


def _normalize_title(raw: str) -> str:
    return (raw or "").replace("_", " ").strip()


class FixRedRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.bp.route("/", methods=["GET"])
        @oauth_required
        def index() -> str:
            title = _normalize_title(request.args.get("title", ""))
            save = 1 if request.args.get("save") == "1" else 0
            return render_template(
                "fixred_one.html",
                title="Fix redirects in page text",
                form_title=title,
                outcome=None,
                save=save,
            )

        @self.bp.route("/", methods=["POST"])
        @oauth_required
        def fixred_post() -> str:
            title = _normalize_title(request.form.get("title", ""))
            save = request.form.get("save") == "1"

            if not title:
                return render_template(
                    "fixred_one.html",
                    title="Fix redirects in page text",
                    form_title="",
                    outcome=None,
                    save=save,
                )

            user = getattr(g, "_current_user", None)

            try:
                outcome = fixred_one.work_on_title(
                    title=title,
                    save=save,
                    summary="Fix redirects.",
                    user=user,
                )
            except Exception as exc:
                logger.exception("work_on_title failed for %s", title)
                flash(f"Error processing {title!r}: {exc!r}", "danger")
                return render_template(
                    "fixred_one.html",
                    title="Fix redirects in page text",
                    form_title=title,
                    outcome=None,
                    save=save,
                )

            return render_template(
                "fixred_one.html",
                title=f"Fix redirects in page text — {title}",
                form_title=title,
                outcome=outcome,
                save=save,
            )


__all__ = [
    "FixRedRoutes",
]
