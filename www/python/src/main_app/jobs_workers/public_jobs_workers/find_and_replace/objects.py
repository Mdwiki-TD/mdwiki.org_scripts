""" """

from __future__ import annotations

import logging
from dataclasses import dataclass

from ...shared_objects import SharedworkerObject

logger = logging.getLogger(__name__)


@dataclass
class FindAndReplaceWorkerObject(SharedworkerObject):
    text_find: str = ""
    text_replace: str = ""
    stopped: bool = False
    cap: int | None = None


__all__ = [
    "FindAndReplaceWorkerObject",
]
