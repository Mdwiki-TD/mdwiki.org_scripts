from dataclasses import dataclass


@dataclass(frozen=True)
class CurrentUser:
    """Lightweight representation of the authenticated user."""

    user_id: str
    username: str
