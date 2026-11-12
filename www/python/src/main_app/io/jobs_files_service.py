"""Service for managing background job result files.

Provides :class:`JobFilesService` for saving and loading job result JSON files
and cancellation markers, plus backward-compatible legacy functions.
"""

from __future__ import annotations

import functools
import json
import logging
import os
from pathlib import Path
from typing import Any

from ..config import get_settings

logger = logging.getLogger(__name__)


class JobFilesService:
    """Manage job result files and cancellation markers on disk.

    The base directory is resolved from application settings and can be
    overridden for testing.
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        self._base_dir = base_dir

    @property
    def jobs_dir(self) -> Path:
        """Resolve and cache the jobs data directory."""
        if self._base_dir is not None:
            return self._base_dir
        app_settings = get_settings()
        jobs_dir = app_settings.paths.public_jobs_path
        if not jobs_dir:
            raise RuntimeError("public_jobs_path configuration is required for job result storage")
        path = Path(jobs_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _save_data(result_data: dict[str, Any], filepath: Path) -> None:
        """Write *result_data* as JSON to *filepath*."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, default=str, ensure_ascii=False)

    def save_result(self, filename: str, result_data: dict[str, Any]) -> Path:
        """Save job result to a JSON file and return the file path."""
        filepath = self.jobs_dir / filename
        self._save_data(result_data, filepath)
        return filepath

    def load_result(self, filename: str) -> dict[str, Any] | None:
        """Load job result from a JSON file."""
        filepath = self.jobs_dir / filename
        if not filepath or not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading job result from {filename}: {e}")
            return None

    def create_cancel_file(self, filename: str) -> Path | None:
        """Create a cancellation marker file."""
        filepath = self.jobs_dir / filename
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("cancelled")
            return filepath
        except OSError:
            logger.exception(f"Error creating job cancelled file {filepath}")
            return None

    def is_cancel_file_exist(self, filename: str) -> bool:
        """Check whether a cancellation marker file exists."""
        try:
            filepath = self.jobs_dir / filename
            return filepath.exists()
        except OSError:
            logger.exception(f"Error checking job cancelled file {filename}")
            return False


# ---------------------------------------------------------------------------
# Legacy compatibility layer — no business logic, delegates to JobFilesService
# ---------------------------------------------------------------------------

_default_service: JobFilesService | None = None


def _get_default_service() -> JobFilesService:
    global _default_service
    if _default_service is None:
        _default_service = JobFilesService()
    return _default_service


@functools.lru_cache(maxsize=1)
def get_jobs_data_dir() -> Path:
    """Legacy entry point. Returns the jobs data directory path."""
    return _get_default_service().jobs_dir


def save_data(result_data: dict[str, Any], filepath: Path) -> None:
    """Legacy entry point. Use :meth:`JobFilesService._save_data` instead."""
    JobFilesService._save_data(result_data, filepath)


def save_job_result_by_name(filename: str, result_data: dict[str, Any]) -> Path:
    """Legacy entry point. Use :meth:`JobFilesService.save_result` instead."""
    return _get_default_service().save_result(filename, result_data)


def load_job_result(filename: str) -> dict[str, Any] | None:
    """Legacy entry point. Use :meth:`JobFilesService.load_result` instead."""
    return _get_default_service().load_result(filename)


def create_job_cancelled_file(filename: str) -> Path | None:
    """Legacy entry point. Use :meth:`JobFilesService.create_cancel_file` instead."""
    return _get_default_service().create_cancel_file(filename)


def is_job_cancelled_file_exist(filename: str) -> bool:
    """Legacy entry point. Use :meth:`JobFilesService.is_cancel_file_exist` instead."""
    return _get_default_service().is_cancel_file_exist(filename)


__all__ = [
    "JobFilesService",
    "get_jobs_data_dir",
    "save_data",
    "save_job_result_by_name",
    "load_job_result",
    "create_job_cancelled_file",
    "is_job_cancelled_file_exist",
]
