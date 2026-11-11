"""Application configuration helpers."""

from __future__ import annotations

from .classes import (
    get_settings,
    CookieConfig,
    CorsConfig,
    JobsConfig,
    OAuthConfig,
    Paths,
    SecurityConfig,
    SessionConfig,
    Settings,
)
from .flask_config import (
    Config,
    ConfigLoader,
    DevelopmentConfig,
    ProductionConfig,
    TestingConfig,
)

# Singleton settings instance
app_settings = get_settings()

__all__ = [
    "ConfigLoader",
    "Config",
    "Settings",
    "DevelopmentConfig",
    "ProductionConfig",
    "TestingConfig",
    "CookieConfig",
    "CorsConfig",
    "JobsConfig",
    "OAuthConfig",
    "Paths",
    "SecurityConfig",
    "SessionConfig",
    "get_settings",
]
