"""Unit tests for flask_app/main_app/app_routes/auth/utils.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from flask_app.main_app.app_routes.auth.utils import oauth_required

def test_oauth_required_decorator_no_user(app):
    @oauth_required
    def protected():
        return "allowed"

    with app.test_request_context("/protected"):
        with patch("flask_app.main_app.app_routes.auth.utils.current_user", return_value=None):
            response = protected()
            assert response.status_code == 302
            assert "/login" in response.location


def test_oauth_required_decorator_with_user(app):
    @oauth_required
    def protected():
        return "allowed"

    with app.test_request_context("/protected"):
        with patch("flask_app.main_app.app_routes.auth.utils.current_user", return_value=MagicMock()):
            response = protected()
            assert response == "allowed"
