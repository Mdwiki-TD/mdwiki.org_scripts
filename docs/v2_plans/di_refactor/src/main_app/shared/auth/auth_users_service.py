"""User authentication service — bridges OAuth callbacks to the DB layer.

Refactored for constructor injection.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ...db.models import UserRecord
from ...db.services import (
    AdminService,
    UsersService,
    UserTokenService,
)
from ..core.crypto import encrypt_value
from .current_user import CurrentUser

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class AuthUsersNewService:
    """Orchestrates user + token + admin-role lookup after OAuth."""

    def __init__(
        self,
        users_service: UsersService | None = None,
        user_token_service: UserTokenService | None = None,
        admin_service: AdminService | None = None,
    ) -> None:
        # Fallback to zero-arg construction keeps backward compatibility
        # during the migration. Remove the fallbacks once all call sites
        # go through the container.
        self.users_service = users_service or UsersService()
        self.user_token_service = user_token_service or UserTokenService()
        self.admin_service = admin_service or AdminService()

    def save_and_get_user(
        self,
        username: str,
        access_key: str,
        access_secret: str,
    ) -> CurrentUser | None:
        """Upsert OAuth credentials and return a CurrentUser composite."""
        username = (username or "").strip()
        if not username:
            logger.warning("OAuth callback received an empty username")
            return None

        try:
            user: UserRecord | None = self.users_service.get_user_by_username(username)
            if not user:
                user = self.users_service.create_user(username)
            if not user:
                return None
            user_id: int = user.user_id
        except Exception as e:
            logger.exception("Failed to upsert or fetch user credentials: %s", e)
            return None

        try:
            encrypted_token = encrypt_value(access_key)
            encrypted_secret = encrypt_value(access_secret)
            self.user_token_service.upsert_user_token(
                user_id=user_id,
                encrypted_token=encrypted_token,
                encrypted_secret=encrypted_secret,
            )
        except Exception as e:
            logger.exception("Failed to upsert or fetch user credentials: %s", e)
            return None

        try:
            token = self.user_token_service.get_user_token(user_id)
            if not token:
                return None
            is_active_admin = self.admin_service.is_active_coordinator(username)
        except Exception as e:
            logger.exception("Failed to upsert or fetch user credentials: %s", e)
            return None

        return CurrentUser(
            user_id=user_id,
            username=username,
            access_token=token.access_token,
            access_secret=token.access_secret,
            is_active_admin=is_active_admin,
            can_run_jobs=user.can_run_jobs,
            can_run_bg_jobs=user.can_run_bg_jobs,
        )

    def get_authenticated_user(self, user_id: int) -> CurrentUser | None:
        """Fetch the CurrentUser composite for session restoration."""
        try:
            token = self.user_token_service.get_authenticated_user_token(user_id)
            if not token:
                return None
            username = token.user.username
            return CurrentUser(
                user_id=user_id,
                username=username,
                access_token=token.access_token,
                access_secret=token.access_secret,
                is_active_admin=self.admin_service.is_active_coordinator(username),
                can_run_jobs=token.user.can_run_jobs,
                can_run_bg_jobs=token.user.can_run_bg_jobs,
            )
        except Exception as e:
            logger.error("Error loading user for ID %s: %s", user_id, e)
            return None


class AuthUserService:
    """Backward-compatible façade.

    New code should resolve ``AuthUsersNewService`` from the container
    instead of calling these static methods.
    """

    @staticmethod
    def save_and_get_user(
        username: str,
        access_key: str,
        access_secret: str,
    ) -> CurrentUser | None:
        from ...di.flask_integration import resolve

        try:
            svc = resolve(AuthUsersNewService)
        except Exception:
            svc = AuthUsersNewService()
        return svc.save_and_get_user(username, access_key, access_secret)

    @staticmethod
    def get_authenticated_user(user_id: int) -> CurrentUser | None:
        from ...di.flask_integration import resolve

        try:
            svc = resolve(AuthUsersNewService)
        except Exception:
            svc = AuthUsersNewService()
        return svc.get_authenticated_user(user_id)


__all__ = [
    "AuthUsersNewService",
    "AuthUserService",
]
