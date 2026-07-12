#!/usr/bin/env python3
"""SDMS — Secure Document Management System.

This is the application entry point. It loads configuration, initialises
the logging and database subsystems, verifies the storage directories,
and launches the modern GUI.

Usage:
    python main.py          Launch the GUI (default)
    python main.py --cli    Launch the CLI (legacy)
"""

from __future__ import annotations

import sys

from config.settings import settings
from database.manager import DatabaseManager
from exceptions.custom_exceptions import DatabaseError
from logger.logging_config import setup_logging
from storage.manager import StorageManager


def main() -> None:
    """Application entry-point orchestrating startup and shutdown."""
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("%s v%s starting ...", settings.APP_NAME, settings.APP_VERSION)
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

    if "--cli" in sys.argv:
        from cli.main import display_welcome, run_cli
        display_welcome()
        run_cli()
    else:
        from controllers.auth_controller import AuthController
        from controllers.document_controller import DocumentController
        from controllers.audit_controller import AuditController
        from controllers.face_controller import FaceController
        from gui.app import SDMSApp

        auth_ctrl = AuthController()
        doc_ctrl = DocumentController()
        audit_ctrl = AuditController()
        face_ctrl = FaceController()

        app = SDMSApp(controller={
            "auth": auth_ctrl,
            "document": doc_ctrl,
            "audit": audit_ctrl,
            "face": face_ctrl,
        })
        app.mainloop()

    db_manager.disconnect()
    logger.info("%s shut down gracefully.", settings.APP_NAME)


if __name__ == "__main__":
    main()
