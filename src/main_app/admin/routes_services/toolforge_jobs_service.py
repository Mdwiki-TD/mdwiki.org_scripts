"""Service layer for the Toolforge jobs pages. Flask-free.

The HTTP calls live in ToolforgeJobsService; this module only shapes the
results for the pages and the job actions (show, logs, restart, delete).
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any
from collections.abc import Callable

import requests

from ...api_services.clients import ToolforgeJobsService

from .toolforge_jobs_mapping import (
    DEFAULT_LOG_LINES,
    MAX_LOG_LINES,
    JobActionResult,
    JobDetailPage,
    JobLogsPage,
    JobsPage,
)

logger = logging.getLogger(__name__)

# Toolforge API message levels mapped to flash categories.
_LEVEL_TO_CATEGORY = {
    "info": "info",
    "warning": "warning",
    "error": "danger",
}


class JobsPageService:
    """Build the data of the jobs pages from the Toolforge Jobs API."""

    def __init__(self, toolforge: ToolforgeJobsService | None = None) -> None:
        self.toolforge = toolforge or ToolforgeJobsService()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _job_status(job: dict[str, Any]) -> str:
        """Return a lowercase short status for a job."""
        status = job.get("status") or {}
        short = status.get("short") or job.get("status_short") or "unknown"
        return str(short).lower()

    @classmethod
    def _normalize_job(cls, job: dict[str, Any]) -> dict[str, Any]:
        """Add the keys the templates use (status_key, status_messages)."""
        job["status_key"] = cls._job_status(job)
        job["status_messages"] = (job.get("status") or {}).get("messages", [])
        return job

    @staticmethod
    def _convert_messages(raw: Any) -> list[tuple[str, str]]:
        """Convert API messages to (text, category) pairs."""
        if not isinstance(raw, dict):
            return []
        messages: list[tuple[str, str]] = []
        for level, texts in raw.items():
            category = _LEVEL_TO_CATEGORY.get(level, "info")
            messages.extend((str(text), category) for text in texts or [])
        return messages

    @staticmethod
    def _normalize_logs(payload: Any) -> list[str]:
        """Turn the logs payload into a list of text lines.

        The shape is handled defensively: a plain string, a list of strings,
        or a list of dicts carrying a ``message`` (and optionally a timestamp).
        """
        entries = payload.get("logs") if isinstance(payload, dict) else payload
        if entries is None:
            return []
        if isinstance(entries, str):
            return entries.splitlines()
        if not isinstance(entries, (list, tuple)):
            return [str(entries)]

        lines: list[str] = []
        for entry in entries:
            if isinstance(entry, dict):
                text = entry.get("message") or entry.get("line") or entry.get("log") or str(entry)
                stamp = entry.get("timestamp")
                lines.append(f"{stamp} {text}" if stamp else str(text))
            else:
                lines.append(str(entry))
        return lines

    def _failure_message(self, action: str, exc: Exception) -> tuple[str, str]:
        """Log an API failure and return the flash message for it."""
        if isinstance(exc, (requests.RequestException, ValueError)):
            # No traceback here: the exception text can contain the token URL.
            reason = self.toolforge.redact(str(exc))
            logger.error("Failed to %s: %s", action, reason)
            return (f"Failed to {action}: {reason}", "danger")

        logger.exception("Failed to %s", action)
        return (f"Failed to {action}: Could not find the TLS certificate file", "danger")

    def _run_action(self, action: str, call: Callable[[], Any], success_text: str) -> JobActionResult:
        """Run a mutating API call and turn the outcome into flash messages."""
        try:
            payload = call()
        except (requests.RequestException, ValueError, OSError) as exc:
            logger.exception("Failed to %s", action)
            return JobActionResult(messages=[self._failure_message(action, exc)], ok=False)

        messages: list[tuple[str, str]] = [(success_text, "success")]
        messages.extend(self._convert_messages(payload.get("messages") if isinstance(payload, dict) else None))
        return JobActionResult(messages=messages)

    # ------------------------------------------------------------------
    # Pages
    # ------------------------------------------------------------------

    def build_jobs_page(self) -> JobsPage:
        """Fetch the jobs and build the page data, never raising."""
        action = "load Toolforge jobs"
        try:
            payload = self.toolforge.list_jobs()
            if not isinstance(payload, dict):
                raise ValueError("Unexpected response from the Toolforge API")
        except (requests.RequestException, ValueError, OSError) as exc:
            logger.exception("Failed to %s", action)
            return JobsPage(messages=[self._failure_message(action, exc)], error=True)

        jobs = [self._normalize_job(job) for job in payload.get("jobs") or []]
        summary = Counter(job["status_key"] for job in jobs)
        return JobsPage(
            jobs=jobs,
            status_summary=dict(summary),
            messages=self._convert_messages(payload.get("messages")),
        )

    def build_job_page(self, job_id: str) -> JobDetailPage:
        """Fetch one job and build the page data, never raising."""
        action = f"load job '{job_id}'"
        try:
            payload = self.toolforge.show_job(job_id)
            if not isinstance(payload, dict):
                raise ValueError("Unexpected response from the Toolforge API")
        except (requests.RequestException, ValueError, OSError) as exc:
            logger.exception("Failed to %s", action)
            return JobDetailPage(job_id=job_id, messages=[self._failure_message(action, exc)], error=True)

        job = payload.get("job") if isinstance(payload.get("job"), dict) else payload
        return JobDetailPage(
            job_id=job_id,
            job=self._normalize_job(job),
            messages=self._convert_messages(payload.get("messages")),
        )

    def build_logs_page(self, job_id: str, lines: int = DEFAULT_LOG_LINES) -> JobLogsPage:
        """Fetch the logs of one job and keep the last ``lines`` lines, never raising."""
        lines = min(max(lines, 1), MAX_LOG_LINES)
        action = f"load logs of job '{job_id}'"
        try:
            payload = self.toolforge.get_logs(job_id)
        except (requests.RequestException, ValueError, OSError) as exc:
            logger.exception("Failed to %s", action)
            return JobLogsPage(job_id=job_id, lines=lines, messages=[self._failure_message(action, exc)], error=True)

        all_lines = self._normalize_logs(payload)
        return JobLogsPage(
            job_id=job_id,
            logs=all_lines[-lines:],
            lines=lines,
            total_lines=len(all_lines),
            messages=self._convert_messages(payload.get("messages") if isinstance(payload, dict) else None),
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def restart_job(self, job_id: str) -> JobActionResult:
        """Restart one job."""
        return self._run_action(
            f"restart job '{job_id}'",
            lambda: self.toolforge.restart_job(job_id),
            f"Job '{job_id}' restarted.",
        )

    def delete_job(self, job_id: str) -> JobActionResult:
        """Delete one job."""
        return self._run_action(
            f"delete job '{job_id}'",
            lambda: self.toolforge.delete_job(job_id),
            f"Job '{job_id}' deleted.",
        )


__all__ = [
    "DEFAULT_LOG_LINES",
    "MAX_LOG_LINES",
    "JobsPageService",
]
