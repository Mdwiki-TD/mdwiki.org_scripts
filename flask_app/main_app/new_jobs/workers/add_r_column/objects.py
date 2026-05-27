"""
"""

from __future__ import annotations

import logging
from typing import Optional
from dataclasses import dataclass, field
from ....new_jobs.base_worker_object import WorkerObject

logger = logging.getLogger(__name__)


@dataclass
class StepDetail:
    status: str = "pending"  # ["pending", "running", "completed", "failed", "skipped", "cancelled"]
    title: str = ""
    message: str = ""
    newrevid: Optional[int] = None  # Kept optional as some steps don't require this field


@dataclass
class Steps:
    load_page: StepDetail = field(default_factory=lambda: StepDetail(title="get page"))
    load_text: StepDetail = field(default_factory=lambda: StepDetail(title="Load page text"))
    add_empty_r_column: StepDetail = field(default_factory=lambda: StepDetail(title="Add empty R column"))
    first_save: StepDetail = field(default_factory=lambda: StepDetail(title="Save page", newrevid=0))
    add_r_column: StepDetail = field(default_factory=lambda: StepDetail(title="Add R column"))
    final_save: StepDetail = field(default_factory=lambda: StepDetail(title="Save page", newrevid=0))


@dataclass
class AddRColumnWorkerObject(WorkerObject):
    steps: Steps = field(default_factory=Steps)
    new_text: str = ""


__all__ = [
    "AddRColumnWorkerObject",
]
