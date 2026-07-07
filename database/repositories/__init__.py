"""Repository layer — abstracts MongoDB CRUD behind clean interfaces.

Every repository inherits from :class:`BaseRepository` which provides
generic ``create``, ``get``, ``update``, ``delete``, ``find``, and
``exists`` helpers.  Concrete repositories add domain-specific methods.
"""

from __future__ import annotations

from database.repositories.audit_repository import AuditRepository
from database.repositories.base import BaseRepository
from database.repositories.document_repository import DocumentRepository
from database.repositories.user_repository import UserRepository

__all__: list[str] = [
    "AuditRepository",
    "BaseRepository",
    "DocumentRepository",
    "UserRepository",
]
