from __future__ import annotations

import logging

import wikitextparser as wtp

from .shared_wtp import ArchiveParamsUrlsData, WtpUtils

logger = logging.getLogger(__name__)


class Cs2ArchiveTodayRemover(ArchiveParamsUrlsData):
    """Remove archive.today-based ``webarchive`` urls from ``CS2`` templates."""

    def __init__(
        self,
        domains: list[str] | None = None,
    ) -> None:
        self.start_patterns = self._build_start_patterns(domains)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def remove(self, text: str) -> tuple[str, int]:
        """
        Remove archive.today links and their dates from templates in the given text.
        """
        parsed = wtp.parse(text)
        removed = 0

        for temp in parsed.templates:
            name = str(temp.normal_name()).strip()

            if not name.lower().startswith(("استشهاد", "cite")):
                continue

            logger.debug(f"template name: {name}")

            archive_urls = WtpUtils.get_args(temp, ArchiveParamsUrlsData.ARCHIVE_PARAMS)
            archive_dates = WtpUtils.get_args(temp, ArchiveParamsUrlsData.ARCHIVEDATE_PARAMS)

            # Identify archive URL parameters pointing to archive.today
            urls_to_delete = []
            for arg in archive_urls:
                name = arg.name.strip()
                value = arg.value.strip()
                logger.debug(f"arg name: {name}, {value=}")
                if any(
                    value.startswith((f"https://{site}", f"http://{site}"))
                    for site in ArchiveParamsUrlsData.ARCHIVEIS_SITES
                ):
                    urls_to_delete.append(name)

            if urls_to_delete:
                for arg_name in urls_to_delete:
                    temp.del_arg(arg_name)
                    removed += 1
                # Also delete associated date parameters
                for arg in archive_dates:
                    param_name = arg.name.strip()
                    temp.del_arg(param_name)
                    logger.info(
                        f"Removed parameter {param_name} from template {temp.name.strip()} because its archive URL was removed."
                    )

        return parsed.string, removed


class ArchiveTodayRemover(ArchiveParamsUrlsData):
    """Remove archive.today-based ``webarchive`` templates from wikitext."""

    def __init__(
        self,
        domains: list[str] | None = None,
        template_names: list[str] | tuple[str, ...] | None = None,
        url_param: str = "url",
    ) -> None:
        self.template_names = {n.strip().lower() for n in (template_names or self.DEFAULT_TEMPLATE_NAMES)}
        self.url_param = url_param
        self.start_patterns = self._build_start_patterns(domains)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_archive_template(self, template: wtp.Template) -> bool:
        name = str(template.normal_name()).strip().lower()
        return name in self.template_names

    def _is_archive_today_url(self, url: str) -> bool:
        return url.strip().lower().startswith(self.start_patterns)

    def _should_remove(self, template: wtp.Template) -> bool:
        if not self._is_archive_template(template):
            return False

        url_value = WtpUtils.get_arg_value(template, [self.url_param])
        if not url_value:
            return False

        return self._is_archive_today_url(url_value)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def remove(self, text: str) -> tuple[str, int]:
        """Return ``(new_text, removed_count)``."""
        parsed_text = wtp.parse(text)
        removed = 0

        # Reverse order so removing a template doesn't shift the others
        for temp in reversed(parsed_text.templates):
            if self._should_remove(temp):
                temp.string = ""
                removed += 1

        return parsed_text.string, removed

    def __call__(self, text: str) -> tuple[str, int]:
        return self.remove(text)


__all__ = [
    "Cs2ArchiveTodayRemover",
    "ArchiveTodayRemover",
]
