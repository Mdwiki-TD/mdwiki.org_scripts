"""
Worker module for Add unlinkedwikibase.

(TODO: import logic from https://github.com/Mdwiki-TD/mdwiki-python-files/blob/main/src/md_core/unlinked_wb/bot.py)
"""

from __future__ import annotations

import logging

from ...base_worker import BaseObjectsJobWorker, JobsRunner
from ...shared_objects import SharedworkerObject

logger = logging.getLogger(__name__)


class AddUnlinkedWikibaseWorker(BaseObjectsJobWorker):
    """Add unlinkedwikibase tag to pages."""

    def __init__(self, data: JobsRunner) -> None:
        self.args = data.args or {}

        super().__init__(data)

        self.result: SharedworkerObject = SharedworkerObject()

    def get_job_type(self) -> str:
        return "add_unlinkedwikibase"

    def process(self) -> SharedworkerObject:
        """
        Placeholder process method.
        """
        logger.info(f"Job {self.job_id}: Placeholder for Add unlinkedwikibase processing")

        # In a real scenario, we might scan all pages.
        # For placeholder, we'll just do nothing.

        if self.result.status in ("pending", "running"):
            self.result.status = "completed"

        return self.result


__all__ = [
    "AddUnlinkedWikibaseWorker",
]
