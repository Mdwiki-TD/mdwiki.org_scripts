"""Named-parameter editor for medical infoboxes.

Provides :class:`NamedParamEditor` for migrating the ``eponym`` parameter
to ``named after`` in medical-condition infoboxes, plus backward-compatible
legacy functions.
"""

from __future__ import annotations

import logging
from typing import Any

import wikitextparser as wtp

logger = logging.getLogger(__name__)


class NamedParamEditor:
    """Edit named parameters in wikitext templates.

    Currently handles the migration of ``eponym`` → ``named after``
    in ``infobox medical condition`` templates.
    """

    _TARGET_INFOBOXES = [
        "infobox medical condition",
        "infobox medical condition (new)",
    ]

    _FALSE_PARAMS = [
        "named after",
        "eponym",
    ]

    @staticmethod
    def gt_arg(temp: wtp.Template, name: str) -> str | bool:
        """Return the stripped value of template parameter *name*, or ``False``."""
        if temp.has_arg(name):
            va = temp.get_arg(name)
            if va and va.value and va.value.strip():
                return va.value.strip()
        return False

    def add_param_named(self, text: str) -> str:
        """Migrate ``eponym`` to ``named after`` in medical-condition infoboxes.

        If the template already has ``named after`` or a non-empty ``eponym``,
        the text is returned unchanged. Otherwise ``eponym`` is removed and
        ``named after`` is set (possibly empty).
        """
        parsed = wtp.parse(text)

        param = "named after"
        false_params: list[Any] = list(self._FALSE_PARAMS)

        for temp in parsed.templates:
            name = str(temp.normal_name()).strip().lower().replace("_", " ")
            if name in self._TARGET_INFOBOXES:
                # Already has "named after" — skip
                if temp.has_arg(param):
                    arg = temp.get_arg(param)
                    value = arg.value if arg else ""
                    logger.info(f"page already had temp {name} with (|{param}={value}). ")
                    return text
                # Has one of the false params with a value — skip
                for x in false_params:
                    value = self.gt_arg(temp, x)
                    if value:
                        logger.info(f"page already had temp {name} with (|{x}={value}). ")
                        return text
                # Migrate eponym → named after
                t_value = ""
                if temp.has_arg("eponym"):
                    if self.gt_arg(temp, "eponym"):
                        t_value = self.gt_arg(temp, "eponym")
                    temp.del_arg("eponym")
                temp.set_arg(f" {param} ", f" {t_value}\n")

        return parsed.string


# ---------------------------------------------------------------------------
# Legacy compatibility layer — no business logic, delegates to NamedParamEditor
# ---------------------------------------------------------------------------

_default_editor = None


def _get_editor() -> NamedParamEditor:
    global _default_editor
    if _default_editor is None:
        _default_editor = NamedParamEditor()
    return _default_editor


def gt_arg(temp: wtp.Template, name: str) -> str | bool:
    """Legacy entry point. Use :meth:`NamedParamEditor.gt_arg` instead."""
    return NamedParamEditor.gt_arg(temp, name)


def add_param_named(text: str) -> str:
    """Legacy entry point. Use :meth:`NamedParamEditor.add_param_named` instead."""
    return _get_editor().add_param_named(text)


__all__ = [
    "NamedParamEditor",
    "gt_arg",
    "add_param_named",
]
