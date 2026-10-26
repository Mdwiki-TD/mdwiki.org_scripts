"""
Template renaming configurations for owidpopup_all worker.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TemplateRename:
    old_names: list[str]
    new_name: str
    arguments: dict[str, str]


OWID_POPUP_RENAME = TemplateRename(
    old_names=["OWIDPopup", "OWID_popup"],
    new_name="OWID",
    arguments={
        "owid": "chart",
    },
)


__all__ = [
    "TemplateRename",
    "OWID_POPUP_RENAME",
]
