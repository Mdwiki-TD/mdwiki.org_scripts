"""Application configuration helpers."""

from __future__ import annotations

from .classes import (
    CookieConfig,
    CorsConfig,
    JobsConfig,
    OAuthConfig,
    Paths,
    SecurityConfig,
    SessionConfig,
    Settings,
    get_settings,
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
