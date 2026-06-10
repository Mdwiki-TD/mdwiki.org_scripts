from __future__ import annotations

from flask.app import Flask

from src.main_app.db.services.user_token_service import (
    delete_user_token,
    get_user_token,
    upsert_user_token,
)
from src.main_app.db.services.users_service import create_user


def test_delete_user_cascades(app: Flask) -> None:
    with app.app_context():
        user = create_user("svc_dave")
        upsert_user_token(user_id=user.user_id, access_key="k", access_secret="s")
        assert get_user_token(user.user_id) is not None


def test_upsert_get_delete_user_token(app: Flask) -> None:
    with app.app_context():
        # Test insert
        user = create_user("svc_eve")
        upsert_user_token(user_id=user.user_id, access_key="key", access_secret="secret")

        token_record = get_user_token(user.user_id)
        assert token_record is not None
        assert token_record.access_token is not None
        assert token_record.access_secret is not None

        # Test update
        upsert_user_token(user_id=user.user_id, access_key="new_key", access_secret="new_secret")
        token_record = get_user_token(user.user_id)

        # Test delete token only
        delete_user_token(user.user_id)
        assert get_user_token(user.user_id) is None
