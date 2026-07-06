#!/usr/bin/env python3
"""SDMS — Secure Document Management System.

This is the application entry point. It loads configuration, initialises
the logging and database subsystems, verifies the storage directories,
displays a welcome banner, and exits gracefully.

Usage:
    python main.py
"""

from __future__ import annotations

import sys

from cli.main import display_welcome, run_cli
from config.settings import settings
from database.manager import DatabaseManager
from exceptions.custom_exceptions import DatabaseError
from logger.logging_config import setup_logging
from storage.manager import StorageManager


def main() -> None:
    """Application entry-point orchestrating startup and shutdown."""
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("%s v%s starting …", settings.APP_NAME, settings.APP_VERSION)
    logger.info("Environment: %s", settings.APP_ENVIRONMENT)

    db_manager = DatabaseManager()

    try:
        db_manager.connect()
    except DatabaseError:
        logger.error("Exiting due to database connection failure.")
        sys.exit(1)

    db_manager.create_indexes()

    storage_mgr = StorageManager()
    storage_mgr.initialise()

    display_welcome()
    run_cli()

    db_manager.disconnect()
    logger.info("%s shut down gracefully.", settings.APP_NAME)


if __name__ == "__main__":
    main()
