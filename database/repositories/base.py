"""Generic base repository providing common MongoDB CRUD operations.

Concrete repositories extend this class and supply the collection name
and document identifier field.
"""

from __future__ import annotations

from typing import Any

import pymongo
from pymongo.collection import Collection, ReturnDocument
from pymongo.errors import DuplicateKeyError as MongoDuplicateKeyError
from pymongo.errors import PyMongoError

from database.exceptions import DuplicateKeyError
from database.manager import DatabaseManager
from exceptions.custom_exceptions import DatabaseError, ValidationError
from logger.logging_config import get_logger

logger = get_logger(__name__)


class BaseRepository:
    """Abstract repository with reusable MongoDB CRUD helpers.

    Subclasses set :attr:`_collection_name` and :attr:`_id_field`.

    Usage::

        class UserRepository(BaseRepository):
            _collection_name = "users"
            _id_field = "user_id"
    """

    _collection_name: str = ""
    _id_field: str = ""

    def __init__(self) -> None:
        if not self._collection_name:
            raise NotImplementedError(
                f"{type(self).__name__} must define _collection_name."
            )
        self._db_mgr = DatabaseManager()

    # ------------------------------------------------------------------
    # Collection access
    # ------------------------------------------------------------------

    @property
    def _collection(self) -> Collection:
        """Return the PyMongo collection handle."""
        return self._db_mgr.get_collection(self._collection_name)

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------

    def create(self, document: dict[str, Any]) -> str:
        """Insert a new document and return its identifier.

        Args:
            document: The document dict to insert.  Must contain
                the field named by :attr:`_id_field`.

        Returns:
            The value of :attr:`_id_field` (e.g. ``user_id`` or
            ``document_id``).

        Raises:
            DuplicateKeyError: If the ``_id_field`` value already exists.
            ValidationError: If the document is empty.
            DatabaseError: On any other database failure.
        """
        if not document:
            raise ValidationError("Cannot create an empty document.")

        doc_id: str | None = document.get(self._id_field)
        if not doc_id:
            raise ValidationError(
                f"Document must contain a non-empty '{self._id_field}' field."
            )

        try:
            self._collection.insert_one(document)
            logger.debug(
                "Created %s %s='%s'.",
                self._collection_name,
                self._id_field,
                doc_id,
            )
            return doc_id
        except MongoDuplicateKeyError as exc:
            raise DuplicateKeyError(
                f"{self._collection_name} with {self._id_field}="
                f"'{doc_id}' already exists."
            ) from exc
        except PyMongoError as exc:
            raise DatabaseError(
                f"Failed to create {self._collection_name}: {exc}"
            ) from exc

    def get_by_id(self, doc_id: str) -> dict[str, Any] | None:
        """Retrieve a document by its identifier field.

        Args:
            doc_id: The value of :attr:`_id_field` to look up.

        Returns:
            The document dict, or ``None`` if not found.
        """
        try:
            return self._collection.find_one({self._id_field: doc_id})
        except PyMongoError as exc:
            raise DatabaseError(
                f"Failed to get {self._collection_name} by "
                f"{self._id_field}='{doc_id}': {exc}"
            ) from exc

    def update(
        self, doc_id: str, updates: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Update a document, returning the **updated** document.

        Args:
            doc_id:  The value of :attr:`_id_field` to update.
            updates: A dict of fields to set (``$set``).

        Returns:
            The updated document dict, or ``None`` if not found.

        Raises:
            DuplicateKeyError: If the update violates a unique index.
        """
        try:
            result = self._collection.find_one_and_update(
                {self._id_field: doc_id},
                {"$set": updates},
                return_document=ReturnDocument.AFTER,
            )
            if result is None:
                logger.warning(
                    "Update failed — %s %s='%s' not found.",
                    self._collection_name,
                    self._id_field,
                    doc_id,
                )
            return result
        except MongoDuplicateKeyError as exc:
            raise DuplicateKeyError(
                f"Update violates unique constraint on "
                f"{self._collection_name}: {exc}"
            ) from exc
        except PyMongoError as exc:
            raise DatabaseError(
                f"Failed to update {self._collection_name}: {exc}"
            ) from exc

    def delete(self, doc_id: str) -> bool:
        """Permanently delete a document.

        Prefer soft-delete (via :meth:`update`) when possible.

        Args:
            doc_id: The value of :attr:`_id_field` to delete.

        Returns:
            ``True`` if a document was deleted, ``False`` otherwise.
        """
        try:
            result = self._collection.delete_one(
                {self._id_field: doc_id}
            )
            if result.deleted_count:
                logger.debug(
                    "Deleted %s %s='%s'.",
                    self._collection_name,
                    self._id_field,
                    doc_id,
                )
            return result.deleted_count > 0
        except PyMongoError as exc:
            raise DatabaseError(
                f"Failed to delete {self._collection_name}: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def exists(self, filters: dict[str, Any]) -> bool:
        """Check whether at least one document matches *filters*.

        Args:
            filters: MongoDB query filter dict.

        Returns:
            ``True`` if a matching document exists.
        """
        try:
            return (
                self._collection.count_documents(filters, limit=1) > 0
            )
        except PyMongoError as exc:
            raise DatabaseError(
                f"Failed to check existence: {exc}"
            ) from exc

    def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count documents matching *filters*.

        Args:
            filters: Optional query filter (``None`` = count all).

        Returns:
            The number of matching documents.
        """
        try:
            return self._collection.count_documents(filters or {})
        except PyMongoError as exc:
            raise DatabaseError(
                f"Failed to count documents: {exc}"
            ) from exc

    def find(
        self,
        filters: dict[str, Any] | None = None,
        skip: int = 0,
        limit: int = 20,
        sort: list[tuple[str, int]] | None = None,
        projection: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search documents with pagination and sorting.

        Args:
            filters:    MongoDB query filter dict.
            skip:       Number of documents to skip (pagination offset).
            limit:      Maximum documents to return (page size).
            sort:       List of ``(field_name, direction)`` tuples, e.g.
                        ``[("created_at", pymongo.DESCENDING)]``.
            projection: Fields to include / exclude.

        Returns:
            A list of matching document dicts.
        """
        if sort is None:
            sort = [("_id", pymongo.DESCENDING)]
        try:
            cursor = (
                self._collection.find(
                    filters or {}, projection=projection
                )
                .sort(sort)
                .skip(skip)
                .limit(limit)
            )
            return list(cursor)
        except PyMongoError as exc:
            raise DatabaseError(
                f"Failed to query {self._collection_name}: {exc}"
            ) from exc

    def find_one(
        self, filters: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Find a single document matching *filters*.

        Args:
            filters: MongoDB query filter dict.

        Returns:
            The first matching document dict, or ``None``.
        """
        try:
            return self._collection.find_one(filters)
        except PyMongoError as exc:
            raise DatabaseError(
                f"Failed to find one document: {exc}"
            ) from exc
