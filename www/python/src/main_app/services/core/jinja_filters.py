"""
Flask application factory.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from flask import request

logger = logging.getLogger(__name__)


class FormatTimestamps:
    @staticmethod
    def _format_timestamp(
        value: str | datetime,
        format_str: str = "%Y-%m-%d %H:%M:%S",
        default: str = "",
    ) -> str:
        """Format a timestamp string or datetime/date object using the specified format string."""
        if not value:
            return default

        if not format_str:
            format_str = "%Y-%m-%d %H:%M:%S"

        if isinstance(value, datetime) or hasattr(value, "strftime"):
            dt = value
        else:
            try:
                dt = datetime.fromisoformat(value)
            except (ValueError, TypeError):
                logger.exception("Failed to parse timestamp: %s", value)
                logger.error("type of value: %s", type(value))
                return default

        return dt.strftime(format_str)  # type: ignore

    @staticmethod
    def format_long_date(value: str | datetime, default: str = "") -> str:
        """Format ISO8601 like '2026-05-28T23:51:50' to '2026-05-28 23:51:50'."""
        return FormatTimestamps._format_timestamp(
            value=value,
            format_str="%Y-%m-%d %H:%M:%S",
            default=default,
        )

    @staticmethod
    def format_date(value: str | datetime, format_str: str = "%Y-%m-%d %H:%M:%S", default: str = "") -> str:
        """Format ISO8601 like '2026-05-28T23:51:50' to '2026-05-28 23:51:50'."""
        return FormatTimestamps._format_timestamp(
            value=value,
            format_str=format_str,
            default=default,
        )

    @staticmethod
    def format_short_date(value: str | datetime, default: str = "") -> str:
        """Format ISO8601 like '2026-05-28T23:51:50' to '23:51:50"""
        return FormatTimestamps._format_timestamp(
            value=value,
            format_str="%H:%M:%S",
            default=default,
        )


class JinjaFilterHelpers:
    """Static helper methods for Jinja2 template filters.

    These are collected in the :data:`filters` dict and registered with Flask's
    Jinja2 environment.
    """

    @staticmethod
    def get_status_class(status: str) -> str:
        """Map a job status string to a Bootstrap CSS class."""
        status_classes = {
            "running": "primary",
            "imported": "success",
            "imported_fallback": "success",
            "completed": "success",
            "changed": "success",
            "missing": "warning",
            "skipped": "warning",
            "cancelled": "warning",
            "failed": "danger",
            "error": "danger",
            "errors": "danger",
            "pending": "secondary",
        }
        return status_classes.get(str(status).lower(), "secondary")

    @staticmethod
    def short_url(value: str) -> str:
        """Extract the last segment of a URL path.

        For example, 'https://commons.wikimedia.org/wiki/File:Example.svg?test'
        becomes 'File:Example.svg'.
        """
        if not value or not isinstance(value, str):
            return ""
        url = ""
        try:
            url = value.rstrip("/").rsplit("/", 1)[-1]
        except Exception:
            logger.exception("Failed to extract short URL from: %s", value)
        url = url.split("?")[0].strip()
        return url

    @staticmethod
    def check_active_route(route_name: str) -> str:
        """Return 'active fw-bold' if *route_name* matches the current request path."""
        route_name = route_name.replace("%20", " ")
        if route_name == request.path:
            return "active fw-bold"
        return ""

    @staticmethod
    def commas_filter(value: str) -> str:
        """Format a number with comma separators."""
        try:
            return f"{value:,}"
        except (ValueError, TypeError):
            return value

    @staticmethod
    def to_json_filter(value: object, indent: int = 2) -> str:
        """Serialize a value for template display (UTF-8-preserving)."""
        return json.dumps(value, ensure_ascii=False, indent=indent)

    @staticmethod
    def is_job_running(job_status: str | None) -> bool:
        """Return True if the job status indicates it's running or pending."""
        if not job_status:
            return False
        return job_status.lower() in ["pending", "running"]


# ---------------------------------------------------------------------------
# Legacy compatibility layer — no business logic, delegates to JinjaFilterHelpers
# ---------------------------------------------------------------------------


def get_status_class(status: str) -> str:
    """Legacy entry point. Use :meth:`JinjaFilterHelpers.get_status_class` instead."""
    return JinjaFilterHelpers.get_status_class(status)


def short_url(value: str) -> str:
    """Legacy entry point. Use :meth:`JinjaFilterHelpers.short_url` instead."""
    return JinjaFilterHelpers.short_url(value)


def check_active_route(route_name: str) -> str:
    """Legacy entry point. Use :meth:`JinjaFilterHelpers.check_active_route` instead."""
    return JinjaFilterHelpers.check_active_route(route_name)


def commas_filter(value: str) -> str:
    """Legacy entry point. Use :meth:`JinjaFilterHelpers.commas_filter` instead."""
    return JinjaFilterHelpers.commas_filter(value)


def to_json_filter(value: object, indent: int = 2) -> str:
    """Legacy entry point. Use :meth:`JinjaFilterHelpers.to_json_filter` instead."""
    return JinjaFilterHelpers.to_json_filter(value, indent)


def is_job_running(job_status: str | None) -> bool:
    """Legacy entry point. Use :meth:`JinjaFilterHelpers.is_job_running` instead."""
    return JinjaFilterHelpers.is_job_running(job_status)


filters = {
    "format_long_date": FormatTimestamps.format_long_date,
    "format_short_date": FormatTimestamps.format_short_date,
    "format_date": FormatTimestamps.format_date,
    "get_status_class": JinjaFilterHelpers.get_status_class,
    "short_url": JinjaFilterHelpers.short_url,
    "check_active_route": JinjaFilterHelpers.check_active_route,
    "is_job_running": JinjaFilterHelpers.is_job_running,
    "commas": JinjaFilterHelpers.commas_filter,
    "to_json": JinjaFilterHelpers.to_json_filter,
}

__all__ = [
    "FormatTimestamps",
    "JinjaFilterHelpers",
    "filters",
]
