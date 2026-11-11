from __future__ import annotations

import logging

import wikitextparser as wtp

logger = logging.getLogger(__name__)


class WtpUtils:
    """Utility class for parsing and extracting data from wikitext."""

    @staticmethod
    def is_value_valid(arg_in: wtp.Argument | None, check_values: bool = True) -> bool:
        """Check if a template argument has a valid non-empty value."""
        if not check_values:
            return True
        return bool(arg_in and arg_in.value and arg_in.value.strip())

    @staticmethod
    def find_templates(
        parsed: wtp.WikiText,
        template_names: list[str],
    ) -> list[wtp.Template]:
        """Find templates matching any of the specified names."""
        targets = {name.strip().lower() for name in template_names}
        templates = parsed.templates
        return [temp for temp in templates if temp and str(temp.normal_name()).strip().lower() in targets]

    @staticmethod
    def parse_templates(parsed: wtp.WikiText) -> dict[str, wtp.Template]:
        """Parse templates into a dictionary keyed by their normalized names."""
        named = {}
        for temp in parsed.templates:
            if not temp:
                continue
            temp_name = str(temp.normal_name()).strip()
            named[temp_name.replace("_", " ")] = temp
        return named

    @classmethod
    def get_args(
        cls,
        template: wtp.Template,
        args: list[str],
        check_values: bool = True,
    ) -> list[wtp.Argument]:
        """Get valid argument objects for a list of candidate argument names."""
        result: list[wtp.Argument] = []
        seen_names: set[str] = set()
        for arg in args:
            for candidate in (arg, arg.lower()):
                if candidate in seen_names:
                    continue
                seen_names.add(candidate)
                if template.has_arg(candidate):
                    arg_in = template.get_arg(candidate)
                    if arg_in and cls.is_value_valid(arg_in, check_values):
                        result.append(arg_in)
                        break
        return result

    @classmethod
    def get_args_values(
        cls,
        temp: wtp.Template,
        args: list[str],
        check_values: bool = True,
    ) -> list[str]:
        """Get stripped string values for a list of argument names."""
        return [arg_in.value.strip() for arg_in in cls.get_args(temp, args, check_values)]

    @classmethod
    def get_arg_value(cls, temp: wtp.Template, args: list[str]) -> str:
        """Return the stripped value of the first matching parameter, or ''."""
        values = cls.get_args_values(temp, args)
        return values[0] if values else ""

    @classmethod
    def get_text_templates_list(cls, text: str, template_names: list[str]) -> list[wtp.Template]:
        """Parse text and return a list of matching templates."""
        parsed = wtp.parse(text)
        return cls.find_templates(parsed, template_names)

    @classmethod
    def get_arg_value_from_text(cls, text: str, template_names: list[str], arg_name: str) -> str:
        """
        Return arg_name's value (stripped) from the first template in text
        whose name matches any of template_names. Empty string if no match or
        the argument isn't set.
        """
        templates = cls.get_text_templates_list(text, template_names)
        if not templates:
            return ""
        return cls.get_arg_value(templates[0], [arg_name])


class ArchiveParamsUrlsData:
    """Archive parameters and URL data for archive link handling."""

    ARCHIVEIS_SITES = [
        "archive.fo",
        "archive.is",
        "archive.li",
        "archive.md",
        "archive.ph",
        "archive.today",
        "archive.vn",
    ]

    TITLES_PARAMS = [
        "script-title",
        "ScriptTitle",
        "title",
        # "العنوان",
        # "عنوان أجنبي",
        # "عنوان",
    ]

    TITLE_PARAMS = [
        "title",
        # "العنوان",
        # "عنوان",
    ]

    URL_PARAMS = [
        "url",
        # "المسار",
        # "مسار",
        # "وصلة",
    ]

    ARCHIVE_PARAMS = [
        "archive-url",
        "archive_url",
        "archiveurl",
        # "مسار أرشيف",
        # "مسار الأرشيف",
        # "مسار-أرشيف",
        # "مسار-الأرشيف",
    ]

    URL_STATUS_PARAMS = [
        "url status",
        "url-status",
        "urlstatus",
        # "حالة المسار",
        # "حالة مسار",
    ]
    ACCESSDATE_PARAMS = [
        "accessDate",
        # "تاريخ الوصول",
        "accessdate",
        "access-date",
        # "تاريخ وصول",
    ]
    ARCHIVEDATE_PARAMS = [
        "archive-date",
        "archive_date",
        "archivedate",
        # "تاريخ أرشيف",
        # "تاريخ الأرشيف",
        # "تاريخ-أرشيف",
        # "تاريخ-الأرشيف",
    ]

    DEAD_URL_PARAMS = [
        # "وصلة مكسورة",
        "dead-url",
        "deadurl",
        # "رابط معطوب",
        # "وصلة ميتة",
    ]

    DEAD_URL_DATE_PARAMS = [
        # "تاريخ وصلة مكسورة",
        "dead-date",
        "deaddate",
    ]

    DEFAULT_TEMPLATE_NAMES = ("webarchive", "web-archive")

    def _build_start_patterns(self, domains: list[str] | None = None) -> tuple[str, ...]:
        """Build e.g. ``https://archive.today`` and ``http://archive.today``."""
        domains = domains or self.ARCHIVEIS_SITES

        patterns: list[str] = []
        for domain in domains:
            patterns.append(f"https://{domain}")
            patterns.append(f"http://{domain}")
        return tuple(patterns)

    def _is_archiveis_url(self, url: str) -> bool:
        return any(url.startswith((f"https://{site}", f"http://{site}")) for site in self.ARCHIVEIS_SITES)


__all__ = [
    "WtpUtils",
    "ArchiveParamsUrlsData",
]
