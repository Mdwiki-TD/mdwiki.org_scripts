"""
Defines the main routes for the application, such as the homepage.
"""

from __future__ import annotations

from .auth_route import AuthView
from .main_route import MainView
from .profile_view import ProfileView

__all__ = [
    "MainView",
    "ProfileView",
    "AuthView",
]
