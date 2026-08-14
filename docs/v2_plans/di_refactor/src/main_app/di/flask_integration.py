"""Flask helpers for the DI container."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from flask import current_app, g

from .container import Container, get_container

if TYPE_CHECKING:
    from flask import Flask

T = TypeVar("T")


def init_di(app: Flask, container: Container) -> None:
    """Attach the container to the Flask app and register a teardown."""

    app.extensions["di_container"] = container

    @app.teardown_appcontext
    def _clear_request_scoped(_exc: BaseException | None = None) -> None:
        # Placeholder for future request-scoped services.
        g.pop("_di_request_cache", None)


def resolve[T](interface: type[T]) -> T:
    """Resolve a service from the current application container.

    Prefer constructor injection in new code. Use this helper only in
    places that cannot receive dependencies via ``__init__`` (e.g. some
    Flask view functions during the migration).
    """
    # Prefer the app-attached container when inside a request / app context.
    try:
        container: Container = current_app.extensions["di_container"]
        return container.resolve(interface)
    except (RuntimeError, KeyError):
        # Fallback to the process-wide container (CLI, workers, tests).
        return get_container().resolve(interface)
