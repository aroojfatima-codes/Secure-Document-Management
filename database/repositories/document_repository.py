"""Repository for Document CRUD operations.

Translates between :class:`~models.document.Document` objects and
MongoDB documents.  No encryption, decryption, or business logic
lives here.
"""

from __future__ import annotations

from typing import Any

import pymongo

from database.exceptions import DocumentNotFoundError
from database.repositories.base import BaseRepository
from exceptions.custom_exceptions import ValidationError
from logger.logging_config import get_logger
from models.document import Document

logger = get_logger(__name__)


class DocumentRepository(BaseRepository):
    """CRUD operations for the ``documents`` collection.

    Usage::

        repo = DocumentRepository()
        doc = Document(document_id="...", original_filename="report.pdf", ...)
        doc_id = repo.create_document(doc)
    """

    _collection_name: str = "documents"
    _id_field: str = "document_id"

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_document(self, document: Document) -> str:
        """Persist a new Document and return its ``document_id``.

        Args:
            document: A validated Document instance.

        Returns:
            The assigned ``document_id``.

        Raises:
            ValidationError: If the document data is invalid.
            DuplicateKeyError: If the ``document_id`` already exists.
        """
        document.validate()
        if not document.document_id:
            raise ValidationError(
                "document_id must be set before calling create_document."
            )

        doc = document.to_dict()
        return self.create(doc)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_document_id(self, document_id: str) -> Document | None:
        """Look up a document by its unique identifier.

        Args:
            document_id: The UUID4 hex document identifier.

        Returns:
            A Document instance, or ``None``.
        """
        doc = self.get_by_id(document_id)
        return Document.from_dict(doc) if doc else None

    def get_documents_by_owner(
        self,
        owner_id: str,
        include_deleted: bool = False,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Document]:
        """Retrieve documents owned by a specific user.

        Args:
            owner_id:       The owner's ``user_id``.
            include_deleted: If ``True``, include soft-deleted documents.
            skip:           Pagination offset.
            limit:          Page size.

        Returns:
            A list of Document instances.
        """
        filters: dict[str, Any] = {"owner_id": owner_id}
        if not include_deleted:
            filters["is_deleted"] = False

        docs = self.find(
            filters=filters,
            skip=skip,
            limit=limit,
            sort=[("created_at", pymongo.DESCENDING)],
        )
        return [Document.from_dict(d) for d in docs]

    def get_shared_with_user(
        self,
        user_id: str,
        include_deleted: bool = False,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Document]:
        """Retrieve documents shared with a specific user.

        Args:
            user_id:         The target user's identifier.
            include_deleted: If ``True``, include soft-deleted documents.
            skip:            Pagination offset.
            limit:           Page size.

        Returns:
            A list of Document instances.
        """
        filters: dict[str, Any] = {
            "shared_with.user_id": user_id,
        }
        if not include_deleted:
            filters["is_deleted"] = False

        docs = self.find(
            filters=filters,
            skip=skip,
            limit=limit,
            sort=[("created_at", pymongo.DESCENDING)],
        )
        return [Document.from_dict(d) for d in docs]

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_document(
        self, document_id: str, updates: dict[str, Any]
    ) -> Document:
        """Update fields on an existing document.

        Args:
            document_id: The target document's identifier.
            updates:     A dict of fields to change.

        Returns:
            The updated Document instance.

        Raises:
            DocumentNotFoundError: If the document does not exist.
        """
        result = self.update(document_id, updates)
        if result is None:
            raise DocumentNotFoundError(
                f"Cannot update — document '{document_id}' not found."
            )
        return Document.from_dict(result)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_document(self, document_id: str) -> None:
        """Permanently remove a document from the database.

        Raises:
            DocumentNotFoundError: If the document does not exist.
        """
        deleted = self.delete(document_id)
        if not deleted:
            raise DocumentNotFoundError(
                f"Cannot delete — document '{document_id}' not found."
            )

    def soft_delete_document(self, document_id: str) -> Document:
        """Mark a document as deleted (preferred).

        Returns:
            The updated Document instance.
        """
        return self.update_document(
            document_id, {"is_deleted": True}
        )

    # ------------------------------------------------------------------
    # Existence helpers
    # ------------------------------------------------------------------

    def document_id_exists(self, document_id: str) -> bool:
        """Check whether a document identifier already exists.

        Returns:
            ``True`` if the document_id exists.
        """
        return self.exists({"document_id": document_id})

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_documents(
        self,
        query: str = "",
        owner_id: str | None = None,
        mime_type: str | None = None,
        include_deleted: bool = False,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Document]:
        """Search documents with optional filters.

        Args:
            query:           Search term matched against
                             ``original_filename`` (text index).
            owner_id:        Optional owner filter.
            mime_type:       Optional MIME type filter (e.g.
                             ``"application/pdf"``).
            include_deleted: If ``True``, include soft-deleted documents.
            skip:            Pagination offset.
            limit:           Page size.

        Returns:
            A list of matching Document instances.
        """
        filters: dict[str, Any] = {}

        if query:
            filters["$text"] = {"$search": query}
        if owner_id:
            filters["owner_id"] = owner_id
        if mime_type:
            filters["mime_type"] = mime_type
        if not include_deleted:
            filters["is_deleted"] = False

        docs = self.find(
            filters=filters,
            skip=skip,
            limit=limit,
            sort=[("created_at", pymongo.DESCENDING)],
        )
        return [Document.from_dict(d) for d in docs]
