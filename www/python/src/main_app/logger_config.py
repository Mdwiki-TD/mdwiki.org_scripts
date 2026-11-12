"""Logging configuration with colored output.

Provides :class:`LoggingConfigurator` for setting up console and file handlers,
plus backward-compatible legacy functions.

Handlers and their levels:
    - console   -> `level` (default DEBUG: everything)
    - <name>.log          -> `file_level` (default INFO: INFO/WARNING/ERROR/CRITICAL)
    - <name>_errors.log   -> `error_level` (default ERROR: ERROR/CRITICAL only)
"""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler, WatchedFileHandler
from pathlib import Path

import colorlog

logger = logging.getLogger(__name__)


def _daily_log_namer(default_name: str) -> str:
    """Rename rotated log from 'errors.log.2024-01-15' to 'errors.2024-01-15.log'."""
    directory = os.path.dirname(default_name)
    basename = os.path.basename(default_name)
    # default format: "<stem>.log.YYYY-MM-DD"
    parts = basename.rsplit(".", 1)
    if len(parts) == 2:
        date_part = parts[1]
        stem = Path(parts[0]).stem  # 'errors.log' -> 'errors'
        return os.path.join(directory, f"{stem}.{date_part}.log")
    return default_name


def _to_level(value: str | int, default: int = logging.INFO) -> int:
    """Convert a level name or number to a numeric logging level."""
    if isinstance(value, str):
        return getattr(logging, value.upper(), default)
    return value


class LoggingConfigurator:
    """Configure logging for the project namespace.

    Sets up console, file, and error-file handlers with appropriate
    formatters and rotation policies.
    """

    @staticmethod
    def prepare_log_file(
        log_file: str | None,
        project_logger: logging.Logger,
    ) -> Path | None:
        """Prepare the log file path and create parent directories if needed."""
        if not log_file:
            return None
        log_file_path = os.path.expandvars(str(log_file))
        log_file_path = Path(log_file_path).expanduser()

        try:
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            project_logger.error("Failed to create log directory: %s", e)
            log_file_path = None
        return log_file_path

    @staticmethod
    def setup_file_handler(
        project_logger: logging.Logger,
        log_file: Path,
        level: int,
        daily_rotation: bool = False,
    ) -> None:
        """Attach a file handler to the logger, optionally rotating daily at midnight (UTC)."""
        file_formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)-8s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        if daily_rotation:
            file_handler = TimedRotatingFileHandler(
                log_file,
                when="midnight",
                interval=1,
                backupCount=90,
                encoding="utf-8",
                utc=True,
            )
            file_handler.namer = _daily_log_namer
        else:
            file_handler = WatchedFileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(level)
        project_logger.addHandler(file_handler)

    @classmethod
    def setup_logging(
        cls,
        level: str | int = "DEBUG",
        name: str = "main_app",
        log_file: str | None = None,
        error_log_file: str | None = None,
        use_colorlog: None | bool = None,
        daily_rotation: bool = False,
        file_level: str | int = "INFO",
        error_level: str | int = "ERROR",
    ) -> None:
        """Configure logging for the project namespace only.

        Args:
            level: console handler level.
            name: Logger name.
            log_file: Path to the main log file.
            error_log_file: Path to the error log file.
            use_colorlog: Force color on/off (None = auto-detect).
            daily_rotation: Rotate log files daily at midnight.
            file_level: Main log file level.
            error_level: Error log file level.
        """
        project_logger = logging.getLogger(name)

        if project_logger.handlers:
            return

        if use_colorlog is None:
            use_colorlog = sys.stderr.isatty()

        console_level = _to_level(level)
        app_file_level = _to_level(file_level)
        errors_file_level = _to_level(error_level, default=logging.ERROR)

        project_logger.setLevel(min(console_level, app_file_level, errors_file_level))
        project_logger.propagate = False

        if use_colorlog:
            console_formatter = colorlog.ColoredFormatter(
                fmt="%(asctime)s - %(name)s - %(log_color)s%(levelname)-s %(reset)s- [%(funcName)s:%(lineno)d] - %(message)s",
                datefmt="%H:%M:%S",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red,bg_white",
                },
            )
        else:
            console_formatter = logging.Formatter(
                fmt="%(asctime)s - %(name)s - %(levelname)-s - [%(funcName)s:%(lineno)d] - %(message)s",
                datefmt="%H:%M:%S",
            )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(console_level)
        project_logger.addHandler(console_handler)

        project_logger.debug("Setting up logging for '%s' with level '%s'", name, level)

        if log_file:
            log_file_path = cls.prepare_log_file(log_file, project_logger)
            if log_file_path:
                cls.setup_file_handler(
                    project_logger,
                    log_file_path,
                    app_file_level,
                    daily_rotation=daily_rotation,
                )

        if error_log_file:
            error_log_file_path = cls.prepare_log_file(error_log_file, project_logger)
            if error_log_file_path:
                cls.setup_file_handler(
                    project_logger,
                    error_log_file_path,
                    errors_file_level,
                    daily_rotation=daily_rotation,
                )

    @staticmethod
    def get_log_dir() -> Path:
        """Get the log directory path.

        NOTE: Don't use settings.paths.log_dir here, logger must initialize before the app/config is created.
        """
        main_dir = os.getenv("MAIN_DIR", "~/data")
        main_dir = Path(os.path.expandvars(main_dir)).expanduser()
        log_dir = Path(main_dir) / "logs"

        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)

        return log_dir

    @classmethod
    def configure_logging(
        cls,
        level: str | int = "DEBUG",
        use_colorlog: None | bool = None,
        name: str = "main_app",
        daily_rotation: bool = False,
        file_level: str | int = "INFO",
        error_level: str | int = "ERROR",
    ) -> None:
        """Configure console + per-logger files: <name>.log and <name>_errors.log."""
        try:
            log_dir = cls.get_log_dir()
        except OSError as exc:
            cls.setup_logging(level=level, name=name, use_colorlog=use_colorlog)
            logging.getLogger(name).warning("Falling back to console logging; could not create log directory %s", exc)
            return

        all_log_path = str(log_dir / "app.log")
        error_log_path = str(log_dir / "errors.log")

        # Call the module-level setup_logging so it can be patched in tests
        setup_logging(
            level=level,
            name=name,
            log_file=all_log_path,
            error_log_file=error_log_path,
            use_colorlog=use_colorlog,
            daily_rotation=daily_rotation,
            file_level=file_level,
            error_level=error_level,
        )


# ---------------------------------------------------------------------------
# Legacy compatibility layer — no business logic, delegates to LoggingConfigurator
# ---------------------------------------------------------------------------


def prepare_log_file(
    log_file: str | None,
    project_logger: logging.Logger,
) -> Path | None:
    """Legacy entry point. Use :meth:`LoggingConfigurator.prepare_log_file` instead."""
    return LoggingConfigurator.prepare_log_file(log_file, project_logger)


def setup_file_handler(
    project_logger: logging.Logger,
    log_file: Path,
    level: int,
    daily_rotation: bool = False,
) -> None:
    """Legacy entry point. Use :meth:`LoggingConfigurator.setup_file_handler` instead."""
    return LoggingConfigurator.setup_file_handler(project_logger, log_file, level, daily_rotation)


def setup_logging(
    level: str | int = "DEBUG",
    name: str = "main_app",
    log_file: str | None = None,
    error_log_file: str | None = None,
    use_colorlog: None | bool = None,
    daily_rotation: bool = False,
    file_level: str | int = "INFO",
    error_level: str | int = "ERROR",
) -> None:
    """Legacy entry point. Use :meth:`LoggingConfigurator.setup_logging` instead."""
    return LoggingConfigurator.setup_logging(
        level=level,
        name=name,
        log_file=log_file,
        error_log_file=error_log_file,
        use_colorlog=use_colorlog,
        daily_rotation=daily_rotation,
        file_level=file_level,
        error_level=error_level,
    )


def get_log_dir() -> Path:
    """Legacy entry point. Use :meth:`LoggingConfigurator.get_log_dir` instead."""
    return LoggingConfigurator.get_log_dir()


def configure_logging(
    level: str | int = "DEBUG",
    use_colorlog: None | bool = None,
    name: str = "main_app",
    daily_rotation: bool = False,
    file_level: str | int = "INFO",
    error_level: str | int = "ERROR",
) -> None:
    """Legacy entry point. Use :meth:`LoggingConfigurator.configure_logging` instead."""
    # This legacy wrapper preserves the original call pattern (calling module-level
    # setup_logging directly) so that tests can patch setup_logging at the module level.
    try:
        log_dir = LoggingConfigurator.get_log_dir()
    except OSError as exc:
        setup_logging(level=level, name=name, use_colorlog=use_colorlog)
        logging.getLogger(name).warning("Falling back to console logging; could not create log directory %s", exc)
        return

    all_log_path = str(log_dir / "app.log")
    error_log_path = str(log_dir / "errors.log")

    setup_logging(
        level=level,
        name=name,
        log_file=all_log_path,
        error_log_file=error_log_path,
        use_colorlog=use_colorlog,
        daily_rotation=daily_rotation,
        file_level=file_level,
        error_level=error_level,
    )


__all__ = [
    "LoggingConfigurator",
    "prepare_log_file",
    "setup_file_handler",
    "setup_logging",
    "get_log_dir",
    "configure_logging",
]
