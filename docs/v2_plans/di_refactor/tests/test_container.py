"""Unit tests for the lightweight DI container."""

from __future__ import annotations

import pytest

from main_app.di.container import Container, init_container, reset_container


class Alpha:
    def __init__(self, value: int = 1) -> None:
        self.value = value


class Beta:
    def __init__(self, alpha: Alpha) -> None:
        self.alpha = alpha


def test_singleton_factory_is_cached() -> None:
    c = Container()
    counter = {"n": 0}

    def factory() -> Alpha:
        counter["n"] += 1
        return Alpha(counter["n"])

    c.register_factory(Alpha, factory)

    a1 = c.resolve(Alpha)
    a2 = c.resolve(Alpha)
    assert a1 is a2
    assert counter["n"] == 1


def test_transient_creates_new_instance() -> None:
    c = Container()
    counter = {"n": 0}

    def factory() -> Alpha:
        counter["n"] += 1
        return Alpha(counter["n"])

    c.register_transient(Alpha, factory)

    a1 = c.resolve(Alpha)
    a2 = c.resolve(Alpha)
    assert a1 is not a2
    assert a1.value == 1
    assert a2.value == 2


def test_override_replaces_registration() -> None:
    c = Container()
    c.register_factory(Alpha, lambda: Alpha(1))
    c.override(Alpha, Alpha(99))
    assert c.resolve(Alpha).value == 99


def test_missing_registration_raises() -> None:
    c = Container()
    with pytest.raises(KeyError):
        c.resolve(Alpha)


def test_nested_resolution() -> None:
    c = Container()
    c.register_factory(Alpha, lambda: Alpha(7))
    c.register_factory(Beta, lambda: Beta(c.resolve(Alpha)))

    b = c.resolve(Beta)
    assert b.alpha.value == 7


def test_process_wide_helpers() -> None:
    reset_container()
    with pytest.raises(RuntimeError):
        from main_app.di.container import get_container

        get_container()

    c = init_container()
    c.register_singleton(Alpha, Alpha(42))
    from main_app.di.container import get_container

    assert get_container().resolve(Alpha).value == 42
    reset_container()
