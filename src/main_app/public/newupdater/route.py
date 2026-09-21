"""Blueprint for `/newupdater/` — synchronous medical-content updater, built on MethodView."""

from __future__ import annotations

import logging
from urllib.parse import unquote

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue
from flask.views import MethodView

from ...services import newupdater_service as svc
from ..auth.decorators import oauth_required

logger = logging.getLogger(__name__)


def _parse_title(title: str) -> str:
    title = title.replace("+", " ").replace("_", " ").strip()
    title = unquote(title)
    title = title.rstrip("/")
    return title


class NewUpdaterBaseView(MethodView):
    """Base view holding the shared render/process logic for the updater views."""

    def _render_outcome(self, title: str, save: bool) -> str:
        """Run the updater for a title (or render the empty form) and return the page."""
        if not title:
            return render_template(
                "newupdater.html",
                title="Medical content updater",
                form_title="",
                outcome=None,
                save=save,
            )

        user = getattr(g, "_current_user", None)

        try:
            outcome = svc.newupdater_one_title(
                title=title,
                save=save,
                summary="Med updater.",
                user=user,
            )
        except Exception as exc:
            logger.exception("work_on_title failed for %s", title)
            flash(f"Error processing {title!r}: {exc!r}", "danger")
            return render_template(
                "newupdater.html",
                title="Medical content updater",
                form_title=title,
                outcome=None,
                save=save,
            )

        return render_template(
            "newupdater.html",
            title=f"Medical content updater — {title}",
            form_title=title,
            outcome=outcome,
            save=save,
        )


class NewUpdaterWorkerView(NewUpdaterBaseView):
    """Preview the update for a title without saving it."""

    def get(self, title: str) -> str:
        """Render the dry-run result for the title extracted from the URL."""
        return self._render_outcome(_parse_title(title), save=False)


class NewUpdaterAutoSaveView(NewUpdaterBaseView):
    """Update a title and save the result automatically."""

    def get(self, title: str) -> str:
        """Render the saved result for the title extracted from the URL.

        NOTE: this route is already used in https://mdwiki.org/wiki/MediaWiki:Sidebars:
            `**https://mdw.toolforge.org/newupdater/save/{{urlencode:{{PAGENAME}}}}|Med updater`
        """
        return self._render_outcome(_parse_title(title), save=True)


class NewUpdaterUpdateView(NewUpdaterBaseView):
    """Dispatch the ``title``/``save`` query arguments to the proper worker view."""

    def get(self) -> ResponseReturnValue:
        """Redirect to the worker or auto-save view based on the query arguments."""
        title = _parse_title(request.args.get("title") or "")
        save = request.args.get("save") == "1"

        # If the title is empty, just render the default page without redirecting.
        if not title:
            return self._render_outcome("", save=False)

        if save:
            # Redirect to the auto_save route: /save/<path:title>
            return redirect(url_for("newupdater.auto_save", title=title))
        # Redirect to the worker route: /<path:title>
        return redirect(url_for("newupdater.worker", title=title))


class NewUpdaterIndexView(MethodView):
    """Render the updater landing page (public — no login required)."""

    def get(self) -> str:
        """Render the empty updater form."""
        return render_template(
            "newupdater.html",
            title="Medical content updater",
            form_title="",
            outcome=None,
            save=False,
        )


class NewUpdaterRoutes:
    """Route registrar binding the newupdater MethodViews to a Blueprint."""

    @classmethod
    def register(cls, bp: Blueprint) -> None:
        """Register the worker, auto-save, dispatch and index views on the blueprint."""
        bp.add_url_rule(
            "/<path:title>",
            view_func=oauth_required(NewUpdaterWorkerView.as_view("worker")),
            methods=["GET"],
        )
        bp.add_url_rule(
            "/save/<path:title>",
            view_func=oauth_required(NewUpdaterAutoSaveView.as_view("auto_save")),
            methods=["GET"],
        )
        bp.add_url_rule(
            "/update",
            view_func=oauth_required(NewUpdaterUpdateView.as_view("newupdater")),
            methods=["GET"],
        )
        # Public landing page — intentionally not wrapped in oauth_required.
        bp.add_url_rule(
            "/",
            view_func=NewUpdaterIndexView.as_view("index"),
            methods=["GET"],
        )


__all__ = [
    "NewUpdaterAutoSaveView",
    "NewUpdaterBaseView",
    "NewUpdaterIndexView",
    "NewUpdaterRoutes",
    "NewUpdaterUpdateView",
    "NewUpdaterWorkerView",
]
