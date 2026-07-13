"""Admin blueprint package."""

from .coordinators import CoordinatorsRoutes
from .jobs import AdminJobsRoutes
from .settings import SettingsRoutes
from .users import UsersRoutes

__all__ = [
    "CoordinatorsRoutes",
    "UsersRoutes",
    "SettingsRoutes",
    "AdminJobsRoutes",
]
