"""Centralized configuration management for the SDMS.

Loads environment variables from the .env file and provides a singleton
Settings object that all modules consume. This avoids hard-coded
configuration values throughout the codebase.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import ClassVar

from dotenv import load_dotenv


class Settings:
    """Application settings loaded from environment variables.

    Usage::

        from config.settings import settings
        mongo_uri = settings.MONGODB_URI
    """

    _instance: ClassVar[Settings | None] = None

    def __new__(cls) -> Settings:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        env_path = Path(__file__).resolve().parent.parent / ".env"
        load_dotenv(dotenv_path=env_path, override=True)

        self.APP_NAME: str = os.getenv("APP_NAME", "Secure Document Management System")
        self.APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
        self.APP_ENVIRONMENT: str = os.getenv("APP_ENVIRONMENT", "development")
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG")
        self.LOG_DIR: str = os.getenv("LOG_DIR", "logs")

        self.MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "secure_document_db")
        self.MONGODB_CONNECT_TIMEOUT_MS: int = int(
            os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "5000")
        )
        self.MONGODB_SERVER_SELECTION_TIMEOUT_MS: int = int(
            os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000")
        )

        self.STORAGE_ENCRYPTED_DIR: str = os.getenv(
            "STORAGE_ENCRYPTED_DIR", "storage/encrypted_documents"
        )
        self.STORAGE_TEMP_DIR: str = os.getenv(
            "STORAGE_TEMP_DIR", "storage/temp"
        )
        self.STORAGE_MAX_FILE_SIZE_MB: int = int(
            os.getenv("STORAGE_MAX_FILE_SIZE_MB", "50")
        )

    @property
    def STORAGE_ENCRYPTED_PATH(self) -> Path:
        """Return the absolute path for encrypted document storage."""
        return Path(self.STORAGE_ENCRYPTED_DIR).resolve()

    @property
    def STORAGE_TEMP_PATH(self) -> Path:
        """Return the absolute path for temporary storage."""
        return Path(self.STORAGE_TEMP_DIR).resolve()

    @property
    def LOG_PATH(self) -> Path:
        """Return the absolute path for log files."""
        return Path(self.LOG_DIR).resolve()


settings = Settings()
