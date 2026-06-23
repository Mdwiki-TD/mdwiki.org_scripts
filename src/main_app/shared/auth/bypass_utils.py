"""
Utilities for development and testing authorization bypass.
"""

from __future__ import annotations

from flask import current_app


def is_ui_test_bypass_enabled() -> bool:
    """Check if the UI test bypass for coordinators is enabled.

    This feature exists only for local development and automated UI/E2E testing.
    It must not be used as a production authorization mechanism.

    The bypass is effective only when:
    - The application is running with DevelopmentConfig (ENV == "development").
    - UI_TEST_BYPASS_COORDINATOR_CHECK is True in the configuration.
    """
    return (
        current_app.config.get("ENV") == "development"
        and current_app.config.get(
            "UI_TEST_BYPASS_COORDINATOR_CHECK",
            False,
        )
    )


__all__ = [
    "is_ui_test_bypass_enabled",
]
