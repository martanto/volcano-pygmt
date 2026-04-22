import os
import sys

from volcano_plot.utils import ensure_dir

from loguru import logger


# Retention periods for log files.
_GENERAL_LOG_RETENTION = "30 days"
_ERROR_LOG_RETENTION = "90 days"

# Tracks whether logging is currently enabled.
_logging_enabled: bool = True

DEFAULT_LOG_DIR = ensure_dir(os.path.join(os.getcwd(), "logs"))

_FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

_CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

logger.remove()


def _configure_handlers(log_dir: str, console_level: str = "INFO") -> None:
    """Remove all existing handlers and re-add console + file handlers.

    Centralises handler configuration so that module-level setup,
    :func:`set_log_level`, and :func:`set_log_directory` all use identical
    retention periods and formats.

    Three handlers are registered:

    * **stderr** — colourised, at ``console_level``.
    * **plot_<date>.log** — all DEBUG+ messages, rotated daily, kept 30 days.
    * **errors_<date>.log** — ERROR+ messages only, rotated daily, kept 90 days.

    Args:
        log_dir (str): Directory path for log file output.  Created by the
            caller before this function is invoked.
        console_level (str): Log level for the stderr handler.  One of
            ``"DEBUG"``, ``"INFO"``, ``"WARNING"``, ``"ERROR"``, or
            ``"CRITICAL"``.  Case-insensitive.  Defaults to ``"INFO"``.

    Returns:
        None
    """
    logger.remove()

    logger.add(
        sys.stderr,
        format=_CONSOLE_FORMAT,
        level=console_level.upper(),
        colorize=True,
    )

    logger.add(
        os.path.join(log_dir, "plot_{time:YYYY-MM-DD}.log"),
        rotation="00:00",
        retention=_GENERAL_LOG_RETENTION,
        compression="zip",
        format=_FILE_FORMAT,
        level="DEBUG",
        enqueue=True,
    )

    logger.add(
        os.path.join(log_dir, "errors_{time:YYYY-MM-DD}.log"),
        rotation="00:00",
        retention=_ERROR_LOG_RETENTION,
        compression="zip",
        format=_FILE_FORMAT,
        level="ERROR",
        enqueue=True,
    )


# Skip if the parent process disabled logging (env var is inherited by workers).
if os.environ.get("DISABLE_LOGGING") != "1":
    _configure_handlers(DEFAULT_LOG_DIR)


def get_logger():
    """Return the package-wide loguru logger instance.

    Returns:
        loguru.Logger: The shared logger instance with console and file handlers
            already attached (unless logging has been disabled via
            :func:`disable_logging`).

    Examples:
        >>> from volcano_plot.logger import get_logger
        >>> log = get_logger()
        >>> log.info("Map rendered successfully.")
    """
    return logger


def set_log_level(level: str) -> None:
    """Change the console log level dynamically.

    Removes all existing handlers and re-adds them with the new console level.
    File handlers always retain ``DEBUG`` / ``ERROR`` as their minimum levels.

    Args:
        level (str): Desired log level for the console handler.  One of
            ``"DEBUG"``, ``"INFO"``, ``"WARNING"``, ``"ERROR"``, or
            ``"CRITICAL"``.  Case-insensitive.

    Returns:
        None

    Examples:
        >>> from volcano_plot.logger import set_log_level
        >>> set_log_level("DEBUG")   # show all messages on the console
        >>> set_log_level("WARNING") # suppress INFO and DEBUG on the console
    """
    _configure_handlers(DEFAULT_LOG_DIR, console_level=level)


def set_log_directory(log_dir: str) -> None:
    """Change the log file directory dynamically.

    Updates the module-level ``DEFAULT_LOG_DIR``, creates the directory if it
    does not yet exist, then reconfigures all handlers to write to the new
    location.

    Args:
        log_dir (str): Absolute or relative path to the new log directory.
            Created automatically (including any missing parents) if it does not
            exist.

    Returns:
        None

    Raises:
        PermissionError: If the process lacks write permission for the specified
            directory or one of its parents.

    Examples:
        >>> from volcano_plot.logger import set_log_directory
        >>> set_log_directory("/var/log/volcano_plot")
    """
    global DEFAULT_LOG_DIR
    DEFAULT_LOG_DIR = ensure_dir(os.path.abspath(log_dir))
    _configure_handlers(DEFAULT_LOG_DIR)
    logger.info(f"Log directory changed to: {DEFAULT_LOG_DIR}")


def disable_logging() -> None:
    """Disable all logging output globally.

    Removes all active loguru handlers so no messages are written to the
    console or log files, and sets the ``DISABLE_LOGGING=1`` environment
    variable so that child processes inherit the same behaviour.  Call
    :func:`enable_logging` to restore handlers.

    Returns:
        None

    Examples:
        >>> from volcano_plot.logger import disable_logging, enable_logging
        >>> disable_logging()
        >>> # ... do work without any log output ...
        >>> enable_logging()
    """
    global _logging_enabled
    _logging_enabled = False
    os.environ["DISABLE_LOGGING"] = "1"
    logger.remove()


def enable_logging() -> None:
    """Re-enable logging after a previous :func:`disable_logging` call.

    Restores console and file handlers using the current ``DEFAULT_LOG_DIR``
    and clears the ``DISABLE_LOGGING`` environment variable.  Has no effect if
    logging is already enabled.

    Returns:
        None

    Examples:
        >>> from volcano_plot.logger import disable_logging, enable_logging
        >>> disable_logging()
        >>> enable_logging()  # handlers are restored
    """
    global _logging_enabled
    if not _logging_enabled:
        _logging_enabled = True
        os.environ.pop("DISABLE_LOGGING", None)
        _configure_handlers(DEFAULT_LOG_DIR)
