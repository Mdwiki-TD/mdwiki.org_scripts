"""Standalone client for the Toolforge Jobs API. Flask-free.

Every method maps to one endpoint of ``/jobs/v1`` and returns the decoded
result of the HTTP request. Use ``request()`` directly to get the raw
``requests.Response`` (status code, headers, body).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from urllib.parse import quote, quote_plus, urlencode

import requests

from .http_client import HttpClient

API_URL = "https://api.svc.tools.eqiad1.wikimedia.cloud:30003"  # inside toolforge environment

EXTERNAL_API_URL = "https://api.svc.toolforge.org"  # external endpoint

TOKEN_ENV = "TOOLS_DEPLOY_TOKEN"

REQUEST_TIMEOUT = 15  # seconds


class ToolforgeJobsService:
    """Thin client for the Toolforge Jobs API.

    Two modes are supported:
    - internal: inside Toolforge, authenticated with the client certificate.
    - external: from anywhere else, authenticated with ``?token=$TOOLS_DEPLOY_TOKEN``.

    Note: in external mode the token is part of the request URL, so do not log
    ``response.url``; use ``redact()`` on any text that may contain it.
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

    # ------------------------------------------------------------------
    # URL / auth helpers
    # ------------------------------------------------------------------

    @property
    def client_cert(self) -> tuple[str, str]:
        """Return the (cert, key) paths used for client authentication."""
        base = f"{self.home_dir}/.toolskube"
        return f"{base}/client.crt", f"{base}/client.key"

    def _tool_path(self, path: str = "") -> str:
        """Return the path of a tool-scoped endpoint (``path`` starts with '/')."""
        return f"/jobs/v1/tool/{quote(self.tool_name, safe='')}{path}"

    @staticmethod
    def _job_path(job_id: str | int) -> str:
        """Return the sub-path of a single job."""
        return f"/jobs/{quote(str(job_id), safe='')}"

    def build_url(self, path: str, params: dict[str, Any] | None = None) -> str:
        """Build the full URL, appending the deploy token in external mode."""
        query: dict[str, Any] = {}
        for key, value in (params or {}).items():
            if value is None:
                continue
            query[key] = str(value).lower() if isinstance(value, bool) else value
        if not self.internal:
            query["token"] = self.token
        url = f"{self.api_url}{path}"
        return f"{url}?{urlencode(query)}" if query else url

    def redact(self, text: str) -> str:
        """Hide the deploy token, which requests puts in error messages (it is in the URL)."""
        if not self.token:
            return text
        variants = {self.token, quote(self.token), quote(self.token, safe=""), quote_plus(self.token)}
        for variant in sorted(variants, key=len, reverse=True):
            text = text.replace(variant, "***")
        return text

    # ------------------------------------------------------------------
    # Low-level request
    # ------------------------------------------------------------------

    def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: Any = None,
        check: bool = True,
    ) -> requests.Response:
        """Send a request and return the raw response.

        With ``check=True`` (default) HTTP error statuses raise
        ``requests.HTTPError``; pass ``check=False`` to inspect them yourself.
        """
        if not self.internal and not self.token:
            raise ValueError(f"{TOKEN_ENV} is not set")

        kwargs: dict[str, Any] = {"verify": self.verify, "timeout": self.timeout}
        if self.internal:
            # The client certificate is only used by the internal endpoint.
            kwargs["cert"] = self.client_cert
        if json is not None:
            kwargs["json"] = json

        # Relies on HttpClient exposing get/post/patch/delete.
        send = getattr(self.http_client, method.lower())
        response = send(self.build_url(path, params), **kwargs)
        if check:
            response.raise_for_status()
        return response

    @staticmethod
    def _payload(response: requests.Response) -> Any:
        """Return the JSON body, falling back to text (or {} for an empty body)."""
        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError:
            return response.text

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

    def create_job(self, data: dict[str, Any]) -> Any:
        """POST /jobs/v1/tool/{tool}/jobs: create a job."""
        return self._payload(self.request("POST", self._tool_path("/jobs"), json=data))

    def update_job(self, data: dict[str, Any]) -> Any:
        """PATCH /jobs/v1/tool/{tool}/jobs: update a job."""
        return self._payload(self.request("PATCH", self._tool_path("/jobs"), json=data))

    def flush_jobs(self) -> Any:
        """DELETE /jobs/v1/tool/{tool}/jobs: delete ALL jobs of the tool."""
        return self._payload(self.request("DELETE", self._tool_path("/jobs")))

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

    def restart_job(self, job_id: str | int) -> Any:
        """POST /jobs/v1/tool/{tool}/jobs/{id}/restart: restart one job."""
        path = self._tool_path(f"{self._job_path(job_id)}/restart")
        return self._payload(self.request("POST", path))

    def healthcheck(self) -> Any:
        """GET /jobs/v1/healthz: service health check (not tool-scoped)."""
        return self._payload(self.request("GET", "/jobs/v1/healthz"))

    def metrics(self) -> str:
        """GET /jobs/v1/metrics: Prometheus metrics as plain text (not tool-scoped)."""
        return self.request("GET", "/jobs/v1/metrics").text


__all__ = [
    "API_URL",
    "EXTERNAL_API_URL",
    "TOKEN_ENV",
    "ToolforgeJobsService",
]
