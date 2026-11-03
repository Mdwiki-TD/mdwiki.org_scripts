"""Service layer for the Toolforge jobs page. Flask-free."""

from __future__ import annotations

import logging
import os
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

import requests

from ...api_services.clients.http_client import HttpClient

logger = logging.getLogger(__name__)

API_URL = "https://api.svc.tools.eqiad1.wikimedia.cloud:30003"  # inside toolforge environment

EXTERNAL_API_URL = "https://api.svc.toolforge.org"  # external endpoint

TOKEN_ENV = "TOOLS_DEPLOY_TOKEN"

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
    """Fetch and normalize the jobs of a tool from the Toolforge Jobs API.

    Two modes are supported:
    - internal: inside Toolforge, authenticated with the client certificate.
    - external: from anywhere else, authenticated with ``?token=$TOOLS_DEPLOY_TOKEN``.
    """

    def __init__(
        self,
        tool_name: str | None = None,
        home_dir: str | None = None,
        verify: bool | None = None,
        timeout: int = REQUEST_TIMEOUT,
        http_client: HttpClient | None = None,
        token: str | None = None,
        internal: bool | None = None,
    ) -> None:
        self.http_client = http_client or HttpClient()
        self.tool_name = tool_name or os.environ.get("TOOL_NAME", "mdw")
        self.home_dir = home_dir or str(Path.home())
        self.token = token or os.environ.get(TOKEN_ENV, "")
        # Without a deploy token we assume we run inside Toolforge.
        self.internal = internal if internal is not None else not self.token
        self.api_url = API_URL if self.internal else EXTERNAL_API_URL
        # The internal cert is self-signed (internal to k8s); the external one is valid.
        self.verify = verify if verify is not None else not self.internal
        self.timeout = timeout

    @property
    def jobs_url(self) -> str:
        """Return the jobs endpoint of the configured tool."""
        return f"{self.api_url}/jobs/v1/tool/{self.tool_name}/jobs"

    @property
    def request_url(self) -> str:
        """Return the final URL, with the deploy token appended for the external API."""
        if self.internal:
            return self.jobs_url
        return f"{self.jobs_url}?{urlencode({'token': self.token})}"

    @property
    def client_cert(self) -> tuple[str, str]:
        """Return the (cert, key) paths used for client authentication."""
        base = f"{self.home_dir}/.toolskube"
        return f"{base}/client.crt", f"{base}/client.key"

    def _redact(self, text: str) -> str:
        """Hide the deploy token, which requests puts in error messages (it is in the URL)."""
        if not self.token:
            return text
        for variant in {self.token, quote(self.token), quote(self.token, safe="")}:
            text = text.replace(variant, "***")
        return text

    def fetch_jobs(self) -> dict[str, Any]:
        """Call the API and return the decoded JSON payload."""
        if not self.internal and not self.token:
            raise ValueError(f"{TOKEN_ENV} is not set")

        kwargs: dict[str, Any] = {"verify": self.verify, "timeout": self.timeout}
        if self.internal:
            # The client certificate is only used by the internal endpoint.
            kwargs["cert"] = self.client_cert

        response = self.http_client.get(
            self.request_url,
            **kwargs,
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
            # No traceback here: the exception text can contain the token URL.
            reason = self._redact(str(exc))
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
    "Message",
    "ToolforgeJobsService",
]
