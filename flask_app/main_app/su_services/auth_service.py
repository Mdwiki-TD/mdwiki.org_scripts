"""OAuth callback business logic extracted from auth/routes.py."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any, Tuple

from ..app_routes.auth.oauth import complete_login
from .users_service import UserService

logger = logging.getLogger(__name__)


class OAuthCallbackError(Exception):
    """Raised when a step of the OAuth callback fails."""

    def __init__(self, message: str, *, flash_category: str = "danger") -> None:
        super().__init__(message)
        self.flash_category = flash_category


def extract_token_credentials(access_token: Any) -> Tuple[str, str]:
    """Extract key/secret from an OAuth access token object."""
    token_key = getattr(access_token, "key", None)
    token_secret = getattr(access_token, "secret", None)

    if not (token_key and token_secret) and isinstance(access_token, Sequence):
        token_key = access_token[0]
        token_secret = access_token[1]

    if not (token_key and token_secret):
        raise OAuthCallbackError("Missing OAuth credentials")

    return str(token_key), str(token_secret)


def extract_identity_fields(identity: dict[str, Any]) -> Tuple[int, str]:
    """Extract user_id and username from an OAuth identity dict."""
    user_identifier = None
    user_identifier_keys = {"sub", "id", "central_id", "user_id"}
    for key in user_identifier_keys:
        user_identifier = identity.get(key)
        if user_identifier:
            logger.debug("Found user identifier in OAuth identity: %s", key)
            break

    if not user_identifier:
        raise OAuthCallbackError("Missing user id")

    try:
        user_id = int(user_identifier)
    except (TypeError, ValueError) as exc:
        raise OAuthCallbackError("Invalid user identifier") from exc

    username = identity.get("username") or identity.get("name")
    if not username:
        raise OAuthCallbackError("Missing username")

    return user_id, username


def complete_oauth_callback(request_token: Any, query_string: str) -> Tuple[int, str, Any]:
    """Complete the OAuth handshake and persist credentials.

    Returns:
        (user_id, username, user_record)

    Raises:
        OAuthIdentityError: If identity verification fails.
        OAuthCallbackError: If token extraction or user persistence fails.
    """
    access_token, identity = complete_login(request_token, query_string)
    token_key, token_secret = extract_token_credentials(access_token)
    user_id, username = extract_identity_fields(identity)

    user_record = UserService.save_and_get_user(
        user_id=user_id,
        username=username,
        access_key=token_key,
        access_secret=token_secret,
    )

    if not user_record:
        raise OAuthCallbackError("Failed to process user credentials")

    return user_id, username, user_record


__all__ = [
    "OAuthCallbackError",
    "complete_oauth_callback",
    "extract_token_credentials",
    "extract_identity_fields",
]
