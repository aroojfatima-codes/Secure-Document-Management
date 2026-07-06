"""Reusable logging configuration for the SDMS.

Provides a factory function that returns a configured logger instance.
All application modules should obtain their logger via this module to
ensure consistent formatting, rotation, and log-level handling.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config.settings import settings


def setup_logging() -> logging.Logger:
    """Configure and return the root application logger.

    Two handlers are registered:
        * Rotating file handler that writes to *logs/sdms.log*.
        * Stream handler that writes to stderr with a simpler format.

    Log level is driven by the ``LOG_LEVEL`` environment variable.
    """
    log_level: str = settings.LOG_LEVEL.upper()
    numeric_level: int = getattr(logging, log_level, logging.DEBUG)

    root_logger: logging.Logger = logging.getLogger("sdms")
    root_logger.setLevel(numeric_level)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    log_path: Path = settings.LOG_PATH
    log_path.mkdir(parents=True, exist_ok=True)
    log_file: Path = log_path / "sdms.log"

    file_handler = RotatingFileHandler(
        filename=str(log_file),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s.%(funcName)s:%(lineno)d — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)

    stream_handler = logging.StreamHandler(stream=sys.stderr)
    stream_handler.setLevel(numeric_level)
    stream_fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
    )
    stream_handler.setFormatter(stream_fmt)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Return a child logger of the ``sdms`` namespace.

    Example::

        logger = get_logger(__name__)
        logger.info("Document loaded successfully.")
    """
    return logging.getLogger(f"sdms.{name}")
