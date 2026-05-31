from __future__ import annotations

from unittest.mock import MagicMock, patch

from flask import g, session
from flask_app.main_app.su_services.users_service import current_user


def test_current_user_from_session(app):
    with app.test_request_context():
        session["uid"] = 123
        with patch("flask_app.main_app.su_services.users_service.get_user_token") as mock_get:
            mock_user = MagicMock()
            mock_user.username = "test_user"
            mock_get.return_value = mock_user

            user = current_user()
            assert user == mock_user
            assert session["username"] == "test_user"
            assert g._current_user == mock_user


def test_current_user_cached_in_g(app):
    with app.test_request_context():
        g._current_user = "cached_user"
        assert current_user() == "cached_user"


def test_current_user_no_session(app):
    with app.test_request_context():
        # No uid in session, no cookie
        with patch("flask_app.main_app.su_services.users_service.get_user_token") as mock_get:
            user = current_user()
            assert user is None
            mock_get.assert_not_called()
