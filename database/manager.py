"""Database connection manager for MongoDB.

Provides a singleton :class:`DatabaseManager` that manages the
MongoDB client connection pool, validates connectivity, and exposes
collection objects for use by the repository layer.
"""

from __future__ import annotations

from typing import ClassVar

import pymongo
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import (
    ConnectionFailure,
    OperationFailure,
    PyMongoError,
)

from config.settings import settings
from database.exceptions import IndexCreationError
from exceptions.custom_exceptions import DatabaseError
from logger.logging_config import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Manages the MongoDB connection and provides access to the database.

    Usage::

        db_mgr = DatabaseManager()
        db_mgr.connect()
        users_coll = db_mgr.get_collection("users")
    """

    _instance: ClassVar[DatabaseManager | None] = None
    _client: pymongo.MongoClient | None = None
    _database: Database | None = None

    def __new__(cls) -> DatabaseManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Establish the MongoDB connection with a connection pool.

        Raises:
            DatabaseError: If the connection cannot be established.
        """
        if self.is_connected:
            logger.debug("Already connected to MongoDB.")
            return

        try:
            logger.info(
                "Connecting to MongoDB at %s ...", settings.MONGODB_URI
            )
            self._client = pymongo.MongoClient(
                settings.MONGODB_URI,
                connectTimeoutMS=settings.MONGODB_CONNECT_TIMEOUT_MS,
                serverSelectionTimeoutMS=(
                    settings.MONGODB_SERVER_SELECTION_TIMEOUT_MS
                ),
                maxPoolSize=10,
                minPoolSize=1,
            )
            self._client.admin.command("ping")
            self._database = self._client[settings.MONGODB_DATABASE]
            logger.info(
                "Connected to database '%s' (pool size=10).",
                settings.MONGODB_DATABASE,
            )
        except ConnectionFailure as exc:
            logger.critical("MongoDB connection failed: %s", exc)
            self._client = None
            self._database = None
            raise DatabaseError(
                f"Could not connect to MongoDB: {exc}"
            ) from exc
        except PyMongoError as exc:
            logger.critical("MongoDB error during connect: %s", exc)
            self._client = None
            self._database = None
            raise DatabaseError(
                f"Unexpected database error: {exc}"
            ) from exc

    def disconnect(self) -> None:
        """Close the MongoDB connection pool gracefully."""
        if self._client is not None:
            self._client.close()
            logger.info("MongoDB connection closed.")
            self._client = None
            self._database = None

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_database(self) -> Database:
        """Return the active :class:`~pymongo.database.Database` instance.

        Raises:
            DatabaseError: If the database has not been initialised.
        """
        if self._database is None:
            raise DatabaseError(
                "Database not initialised. Call connect() first."
            )
        return self._database

    def get_collection(self, name: str) -> Collection:
        """Return a :class:`~pymongo.collection.Collection` by name.

        Args:
            name: The collection name (e.g. ``"users"``, ``"documents"``).

        Returns:
            A PyMongo Collection handle ready for CRUD operations.

        Raises:
            DatabaseError: If the database is not connected.
        """
        db = self.get_database()
        return db[name]

    @property
    def is_connected(self) -> bool:
        """Check whether the MongoDB client is currently connected."""
        if self._client is None:
            return False
        try:
            self._client.admin.command("ping")
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Index management
    # ------------------------------------------------------------------

    def create_indexes(self) -> None:
        """Create all required indexes for the application collections.

        Idempotent — MongoDB skips index creation if the index
        already exists (``create_index`` uses ``ensureIndex``
        semantics).

        Raises:
            IndexCreationError: If any index creation fails.
        """
        try:
            users: Collection = self.get_collection("users")
            documents: Collection = self.get_collection("documents")

            # Users indexes
            users.create_index("user_id", unique=True, name="idx_user_id")
            users.create_index(
                "username", unique=True, name="idx_username"
            )
            users.create_index("role", name="idx_user_role")
            users.create_index("is_active", name="idx_user_is_active")

            # Documents indexes
            documents.create_index(
                "document_id", unique=True, name="idx_document_id"
            )
            documents.create_index("owner_id", name="idx_doc_owner")
            documents.create_index("created_at", name="idx_doc_created_at")
            documents.create_index(
                [("original_filename", pymongo.TEXT)],
                name="idx_doc_filename_text",
                default_language="none",
            )
            documents.create_index(
                [("shared_with.user_id", pymongo.ASCENDING)],
                name="idx_doc_shared_with",
            )
            documents.create_index("is_deleted", name="idx_doc_is_deleted")

            logger.info("All database indexes created / verified.")
        except OperationFailure as exc:
            logger.error("Index creation failed: %s", exc)
            raise IndexCreationError(
                f"Failed to create indexes: {exc}"
            ) from exc
        except PyMongoError as exc:
            logger.error("Database error during index creation: %s", exc)
            raise IndexCreationError(
                f"Unexpected error during index creation: {exc}"
            ) from exc
