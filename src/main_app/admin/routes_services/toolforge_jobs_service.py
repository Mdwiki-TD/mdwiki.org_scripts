"""Service layer for the Toolforge jobs page. Flask-free."""

from __future__ import annotations

import logging
import os
from collections import Counter
from dataclasses import dataclass, field
from typing import Any
from pathlib import Path

import requests

from ...api_services.clients.http_client import HttpClient

logger = logging.getLogger(__name__)

API_URL = "https://api.svc.tools.eqiad1.wikimedia.cloud:30003"
REQUEST_TIMEOUT = 15  # seconds

# (text, category) pair, ready to be passed to flask.flash by the view.
Message = tuple[str, str]

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
    messages: list[Message] = field(default_factory=list)
    error: bool = False

    def to_context(self) -> dict[str, Any]:
        """Return the template context."""
        return {
            "jobs": self.jobs,
            "status_summary": self.status_summary,
            "total_jobs": len(self.jobs),
            "error": self.error,
        }


class ToolforgeJobsService:
    """Fetch and normalize the jobs of a tool from the Toolforge Jobs API."""

    def __init__(
        self,
        api_url: str = API_URL,
        tool_name: str | None = None,
        home_dir: str | None = None,
        verify: bool = False,
        timeout: int = REQUEST_TIMEOUT,
        http_client: HttpClient | None = None,
    ) -> None:
        self.http_client = http_client or HttpClient()
        self.api_url = api_url
        self.tool_name = tool_name or os.environ.get("TOOL_NAME", "mdw")
        self.home_dir = home_dir or str(Path.home())
        # The cert is self-signed and internal to k8s (internal endpoint).
        self.verify = verify
        self.timeout = timeout

    @property
    def jobs_url(self) -> str:
        """Return the jobs endpoint of the configured tool."""
        return f"{self.api_url}/jobs/v1/tool/{self.tool_name}/jobs"

    @property
    def client_cert(self) -> tuple[str, str]:
        """Return the (cert, key) paths used for client authentication."""
        base = f"{self.home_dir}/.toolskube"
        return f"{base}/client.crt", f"{base}/client.key"

    def fetch_jobs(self) -> dict[str, Any]:
        """Call the API and return the decoded JSON payload."""
        response = self.http_client.get(
            self.jobs_url,
            cert=self.client_cert,
            verify=self.verify,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _job_status(job: dict[str, Any]) -> str:
        """Return a lowercase short status for a job."""
        status = job.get("status") or {}
        short = status.get("short") or job.get("status_short") or "unknown"
        return str(short).lower()

    @staticmethod
    def _convert_messages(raw: dict[str, list[str]] | None) -> list[Message]:
        """Convert API messages to (text, category) pairs."""
        messages: list[Message] = []
        for level, texts in (raw or {}).items():
            category = _LEVEL_TO_CATEGORY.get(level, "info")
            messages.extend((str(text), category) for text in texts or [])
        return messages

    def build_jobs_page(self) -> JobsPage:
        """Fetch the jobs and build the page data, never raising."""
        try:
            payload = self.fetch_jobs()
        except (requests.RequestException, ValueError) as exc:
            logger.exception("Failed to load Toolforge jobs")
            return JobsPage(
                messages=[(f"Failed to load Toolforge jobs: {exc}", "danger")],
                error=True,
            )
        except OSError as exc:
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
    "Message",
    "ToolforgeJobsService",
]
