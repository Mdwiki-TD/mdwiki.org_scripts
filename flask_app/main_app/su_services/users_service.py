""" """

from __future__ import annotations

import logging
from typing import Optional

from ..db.models import UserTokenRecord
from ..db.services import get_user_token, upsert_user_token

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    def save_and_get_user(
        user_id: int,
        username: str,
        access_key: str,
        access_secret: str,
    ) -> Optional[UserTokenRecord]:
        """Business logic for upserting and retrieving the user token record."""
        try:
            # 1. Update or insert into database via repository
            upsert_user_token(
                user_id=user_id,
                username=username,
                access_key=access_key,
                access_secret=access_secret,
            )
            # 2. Get the fresh record
            return get_user_token(user_id)
        except Exception as e:
            logger.exception("Failed to upsert or fetch user credentials: %s", e)
            return None

    @staticmethod
    def get_authenticated_user(user_id: int) -> Optional[UserTokenRecord]:
        """Fetch the user token record by ID for session restoration."""
        try:
            return get_user_token(user_id)
        except Exception as e:
            logger.error("Error loading user token for ID %s: %s", user_id, e)
            return None


__all__ = [
    "UserService",
]
