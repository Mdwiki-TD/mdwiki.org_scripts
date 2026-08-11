"""Lightweight dependency-injection container.

Design goals
------------
* Explicit constructor injection (no service locator anti-pattern in business code).
* Flask-friendly: one container per application instance.
* Easy to override in tests.
* No external DI framework required (keeps the dependency surface small).
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class Container:
    """Simple service container with singleton and factory support."""

    def __init__(self) -> None:
        self._singletons: dict[type, Any] = {}
        self._factories: dict[type, Callable[[], Any]] = {}
        self._lock = threading.RLock()

    def register_singleton(self, interface: type[T], instance: T) -> None:
        """Register an already-created instance as a singleton."""
        with self._lock:
            self._singletons[interface] = instance

    def register_factory(self, interface: type[T], factory: Callable[[], T]) -> None:
        """Register a factory that will be called on first resolve (then cached)."""
        with self._lock:
            self._factories[interface] = factory
            self._singletons.pop(interface, None)  # clear any previous instance

    def register_transient(self, interface: type[T], factory: Callable[[], T]) -> None:
        """Register a factory that is called on every resolve (not cached)."""
        # Stored under a private key so resolve() can detect it.
        with self._lock:
            self._factories[interface] = factory
            # Mark as transient by storing a sentinel alongside
            self._singletons[interface] = _TRANSIENT

    def resolve(self, interface: type[T]) -> T:
        """Return an instance of *interface*.

        Raises KeyError if nothing is registered for the type.
        """
        with self._lock:
            # Fast path: already-created singleton
            existing = self._singletons.get(interface)
            if existing is not None and existing is not _TRANSIENT:
                return existing  # type: ignore[return-value]

            factory = self._factories.get(interface)
            if factory is None:
                raise KeyError(f"No provider registered for {interface!r}")

            instance = factory()

            # Cache unless it was registered as transient
            if existing is not _TRANSIENT:
                self._singletons[interface] = instance

            return instance  # type: ignore[return-value]

    def override(self, interface: type[T], instance: T) -> None:
        """Replace a registration (useful in tests)."""
        with self._lock:
            self._singletons[interface] = instance
            self._factories.pop(interface, None)

    def clear(self) -> None:
        """Remove all registrations (mainly for tests)."""
        with self._lock:
            self._singletons.clear()
            self._factories.clear()


class _TransientSentinel:
    """Sentinel marking a registration as transient."""


_TRANSIENT = _TransientSentinel()

# ---------------------------------------------------------------------------
# Process-wide helpers (one container per Flask app is preferred;
# these helpers support the common single-app deployment).
# ---------------------------------------------------------------------------

_app_container: Container | None = None
_app_container_lock = threading.Lock()


def init_container(container: Container | None = None) -> Container:
    """Initialise (or replace) the process-wide container."""
    global _app_container
    with _app_container_lock:
        _app_container = container or Container()
        return _app_container


def get_container() -> Container:
    """Return the process-wide container. Raises if not initialised."""
    if _app_container is None:
        raise RuntimeError("DI container not initialised. Call init_container() from create_app().")
    return _app_container


def reset_container() -> None:
    """Clear the process-wide container (for tests)."""
    global _app_container
    with _app_container_lock:
        if _app_container is not None:
            _app_container.clear()
        _app_container = None
