"""
Template renaming configurations for owidpopup_all worker.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import wikitextparser as wtp


def _norm_template_name(name: str) -> str:
    return name.strip().lower().replace("_", " ")


@dataclass
class TemplateRename:
    old_names: list[str]
    new_name: str
    arguments: dict[str, str] = field(default_factory=dict)

    _old_names_norm: frozenset[str] = field(init=False, repr=False)
    _args_map: dict[str, str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._old_names_norm = frozenset(_norm_template_name(n) for n in self.old_names)
        self._args_map = {k.strip().lower(): v for k, v in self.arguments.items()}

    def rename_temp(self, temp: wtp.Template) -> None:
        """Rename the template and its arguments in place."""
        temp.name = self.new_name

        for arg in temp.arguments:
            new_arg_name = self._args_map.get(arg.name.strip().lower())
            if new_arg_name:
                arg.name = new_arg_name


OWID_POPUP_RENAME = TemplateRename(
    old_names=["OWIDPopup", "OWID_popup"],
    new_name="OWID",
    arguments={
        "owid": "chart",
    },
)


__all__ = [
    "_norm_template_name",
    "TemplateRename",
    "OWID_POPUP_RENAME",
]
