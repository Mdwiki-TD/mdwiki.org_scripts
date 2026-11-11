"""Blueprint for `/fixred/` — single-page redirect fixer, built on MethodView."""

from __future__ import annotations

import logging

from flask import Blueprint, flash, g, render_template, request
from flask.typing import ResponseReturnValue
from flask.views import MethodView

from ..services import fixred_one
from .auth.decorators import oauth_required

logger = logging.getLogger(__name__)


def _normalize_title(raw: str) -> str:
    return (raw or "").replace("_", " ").strip()


class FixRedView(MethodView):
    """View to render the redirect-fixer form and to process a submitted title."""

    def get(self) -> ResponseReturnValue:
        """Render the fix-redirects form for the optional title query argument."""
        title = _normalize_title(request.args.get("title", ""))
        save = 1 if request.args.get("save") == "1" else 0
        return render_template(
            "fixred_one.html",
            title="Fix redirects in page text",
            form_title=title,
            outcome=None,
            save=save,
        )

    def post(self) -> ResponseReturnValue:
        """Rewrite the redirect links on the submitted page and render the result."""
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

    @classmethod
    def register(cls, bp: Blueprint) -> None:
        """Register the unified view and its legacy POST alias on the blueprint."""
        # Primary endpoint: one MethodView answering both GET and POST on "/".
        bp.add_url_rule(
            "/",
            view_func=oauth_required(cls.as_view("index")),
            methods=["GET", "POST"],
        )

        # ------------------------------------------------------------------
        # TODO: Backward Compatibility / Temporary Alias
        # Legacy POST endpoint "fixred_post" merged into FixRedView.post.
        # templates/fixred_one.html still targets url_for("fixred.fixred_post").
        # Remove this rule once the template is updated to "fixred.index".
        # ------------------------------------------------------------------
        bp.add_url_rule(
            "/",
            endpoint="fixred_post",
            view_func=oauth_required(cls.as_view("fixred_post_legacy")),
            methods=["POST"],
        )


__all__ = [
    "FixRedView",
]
