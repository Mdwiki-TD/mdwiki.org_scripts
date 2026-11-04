"""Standalone client for the Toolforge jobs API. Flask-free.

Every method maps to one endpoint of ``/jobs/v1`` and returns the decoded
result of the HTTP request. Use ``request()`` directly to get the raw
``requests.Response`` (status code, headers, body).
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from .http_client import HttpClient
from .toolforge_api_service import ToolforgeApiService


class ToolforgeJobsService(ToolforgeApiService):
    """Thin client for the Toolforge Jobs API."""

    def __init__(
        self,
        tool_name: str | None = None,
        home_dir: str | None = None,
        verify: bool | None = None,
        timeout: int | None = None,
        http_client: HttpClient | None = None,
        token: str | None = None,
        internal: bool | None = None,
    ) -> None:
        super().__init__(
            api_route="jobs",
            tool_name=tool_name,
            home_dir=home_dir,
            verify=verify,
            timeout=timeout,
            http_client=http_client,
            token=token,
            internal=internal,
        )

    @staticmethod
    def _job_path(job_id: str | int) -> str:
        """Return the sub-path of a single job."""
        return f"/jobs/{quote(str(job_id), safe='')}"

    # ------------------------------------------------------------------
    # Endpoints
    # ------------------------------------------------------------------

    def images(self) -> Any:
        """GET /jobs/v1/tool/{tool}/images: list the available images."""
        return self._payload(self.request("GET", self._tool_path("/images")))

    def quotas(self) -> Any:
        """GET /jobs/v1/tool/{tool}/quotas: show the job quotas of the tool."""
        return self._payload(self.request("GET", self._tool_path("/quotas")))

    def list_jobs(self) -> Any:
        """GET /jobs/v1/tool/{tool}/jobs: list all jobs of the tool."""
        return self._payload(self.request("GET", self._tool_path("/jobs")))

    def show_job(self, job_id: str | int) -> Any:
        """GET /jobs/v1/tool/{tool}/jobs/{id}: show one job."""
        return self._payload(self.request("GET", self._tool_path(self._job_path(job_id))))

    def delete_job(self, job_id: str | int) -> Any:
        """DELETE /jobs/v1/tool/{tool}/jobs/{id}: delete one job."""
        return self._payload(self.request("DELETE", self._tool_path(self._job_path(job_id))))

    def get_logs(self, job_id: str | int, params: dict[str, Any] | None = None) -> Any:
        """GET /jobs/v1/tool/{tool}/jobs/{id}/logs: get the logs of one job.

        ``params`` is passed as the query string (for example ``{"lines": 100}``).
        """
        path = self._tool_path(f"{self._job_path(job_id)}/logs")
        return self._payload(self.request("GET", path, params=params))

    def create_job(self, data: dict[str, Any]) -> Any:
        """POST /jobs/v1/tool/{tool}/jobs: create a job."""
        return self._payload(self.request("POST", self._tool_path("/jobs"), json=data))

    def restart_job(self, job_id: str | int) -> Any:
        """POST /jobs/v1/tool/{tool}/jobs/{id}/restart: restart one job."""
        path = self._tool_path(f"{self._job_path(job_id)}/restart")
        return self._payload(self.request("POST", path))

    def update_job(self, data: dict[str, Any]) -> Any:
        """PATCH /jobs/v1/tool/{tool}/jobs: update a job."""
        return self._payload(self.request("PATCH", self._tool_path("/jobs"), json=data))

    def flush_jobs(self) -> Any:
        """DELETE /jobs/v1/tool/{tool}/jobs: delete ALL jobs of the tool."""
        return self._payload(self.request("DELETE", self._tool_path("/jobs")))


__all__ = [
    "ToolforgeJobsService",
]
