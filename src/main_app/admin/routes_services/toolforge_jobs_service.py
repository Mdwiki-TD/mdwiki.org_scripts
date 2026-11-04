"""Service layer for the Toolforge jobs page. Flask-free.

The HTTP calls live in ToolforgeJobsService; this module only shapes the
result for the page.
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

import requests

from ...api_services.clients import ToolforgeJobsService

logger = logging.getLogger(__name__)

# Toolforge API message levels mapped to flash categories.
_LEVEL_TO_CATEGORY = {
    "info": "info",
    "warning": "warning",
    "error": "danger",
}


@dataclass
class JobsPage:
    """Everything the template needs, plus messages to flash."""

    jobs: list[dict[str, Any]] = field(default_factory=list)
    status_summary: dict[str, int] = field(default_factory=dict)
    messages: list[tuple[str, str]] = field(default_factory=list)
    error: bool = False

    def to_context(self) -> dict[str, Any]:
        """Return the template context."""
        return {
            "jobs": self.jobs,
            "status_summary": self.status_summary,
            "total_jobs": len(self.jobs),
            "error": self.error,
        }


class JobsPageService:
    """Build the data of the jobs page from the Toolforge Jobs API."""

    def __init__(self, toolforge: ToolforgeJobsService | None = None) -> None:
        self.toolforge = toolforge or ToolforgeJobsService()

    @staticmethod
    def _job_status(job: dict[str, Any]) -> str:
        """Return a lowercase short status for a job."""
        status = job.get("status") or {}
        short = status.get("short") or job.get("status_short") or "unknown"
        return str(short).lower()

    @staticmethod
    def _convert_messages(raw: dict[str, list[str]] | None) -> list[tuple[str, str]]:
        """Convert API messages to (text, category) pairs."""
        messages: list[tuple[str, str]] = []
        for level, texts in (raw or {}).items():
            category = _LEVEL_TO_CATEGORY.get(level, "info")
            messages.extend((str(text), category) for text in texts or [])
        return messages

    def build_jobs_page(self) -> JobsPage:
        """Fetch the jobs and build the page data, never raising."""
        try:
            payload = self.toolforge.list_jobs()
            if not isinstance(payload, dict):
                raise ValueError("Unexpected response from the Toolforge API")
        except (requests.RequestException, ValueError) as exc:
            # No traceback here: the exception text can contain the token URL.
            reason = self.toolforge.redact(str(exc))
            logger.error("Failed to load Toolforge jobs: %s", reason)
            return JobsPage(
                messages=[(f"Failed to load Toolforge jobs: {reason}", "danger")],
                error=True,
            )
        except OSError:
            logger.exception("Failed to load Toolforge jobs")
            return JobsPage(
                messages=[("Failed to load Toolforge jobs: Could not find the TLS certificate file", "danger")],
                error=True,
            )

        jobs = payload.get("jobs") or []
        for job in jobs:
            job["status_key"] = self._job_status(job)
            job["status_messages"] = (job.get("status") or {}).get("messages", [])

        summary = Counter(job["status_key"] for job in jobs)
        return JobsPage(
            jobs=jobs,
            status_summary=dict(summary),
            messages=self._convert_messages(payload.get("messages")),
        )


__all__ = [
    "JobsPage",
    "JobsPageService",
]
