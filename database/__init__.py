"""SDMS Database Layer.

Provides MongoDB connection management via a singleton
:class:`DatabaseManager` and a collection of repository classes that
abstract CRUD operations behind clean, model-oriented interfaces.
"""

from __future__ import annotations

from database.exceptions import (
    CollectionNotInitialisedError,
    DocumentNotFoundError,
    DuplicateKeyError,
    IndexCreationError,
    UserNotFoundError,
)
from database.manager import DatabaseManager
from database.repositories.document_repository import DocumentRepository
from database.repositories.user_repository import UserRepository

__all__: list[str] = [
    "CollectionNotInitialisedError",
    "DatabaseManager",
    "DocumentNotFoundError",
    "DocumentRepository",
    "DuplicateKeyError",
    "IndexCreationError",
    "UserNotFoundError",
    "UserRepository",
]
