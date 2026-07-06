"""Database-layer exception classes.

All exceptions inherit from
:class:`exceptions.custom_exceptions.DatabaseError` so they are
caught by the existing SDMS exception framework.
"""

from __future__ import annotations

from exceptions.custom_exceptions import DatabaseError


class DuplicateKeyError(DatabaseError):
    """Raised when an insert or update violates a unique index."""


class DocumentNotFoundError(DatabaseError):
    """Raised when a requested document does not exist."""


class UserNotFoundError(DatabaseError):
    """Raised when a requested user does not exist."""


class CollectionNotInitialisedError(DatabaseError):
    """Raised when a repository method is called before the collection exists."""


class IndexCreationError(DatabaseError):
    """Raised when index creation in MongoDB fails."""
