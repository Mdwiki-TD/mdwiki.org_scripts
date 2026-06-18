"""Admin blueprint package."""

from .coordinators import coordinators_module
from .jobs import jobs_module
from .settings import settings_module
from .users import users_module

__all__ = [
    "coordinators_module",
    "users_module",
    "settings_module",
    "jobs_module",
]
