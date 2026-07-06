"""Document listing service — retrieves document metadata for display.

Provides paginated listings, single-document detail, and search
for the currently authenticated user.  No decryption or file I/O
occurs in this module — only MongoDB metadata queries.

The service distinguishes between documents *owned* by the user and
documents *shared* with them, preparing the architecture for the
secure sharing milestone.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from database.exceptions import DocumentNotFoundError
from database.repositories.document_repository import DocumentRepository
from exceptions.custom_exceptions import ValidationError
from logger.logging_config import get_logger
from services.session_manager import SessionManager

logger = get_logger(__name__)

# Maximum page size to prevent abuse
MAX_PER_PAGE: int = 100
DEFAULT_PER_PAGE: int = 20


def _format_file_size(size_bytes: int) -> str:
    """Return a human-readable file-size string.

    Examples:
        ``"512 B"``, ``"12.3 KB"``, ``"1.5 MB"``, ``"2.1 GB"``
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    size: float = float(size_bytes)
    for unit in ("KB", "MB", "GB"):
        size /= 1024.0
        if size < 1024:
            return f"{size:.1f} {unit}"
    return f"{size:.1f} TB"


def _get_file_extension(filename: str) -> str:
    """Return the lowercase file extension including the dot.

    Returns ``""`` if there is no extension.
    """
    return Path(filename).suffix.lower()


def _safe_document_info(doc: dict[str, Any]) -> dict[str, Any]:
    """Extract only safe metadata fields from a raw document dict.

    Sensitive fields (``encrypted_aes_key``, ``iv``,
    ``encrypted_filename``, ``algorithm``) are **never** included.
    """
    created: datetime | None = doc.get("created_at")
    updated: datetime | None = doc.get("updated_at")
    is_deleted: bool = doc.get("is_deleted", False)
    file_size: int = doc.get("file_size", 0)
    original_filename: str = doc.get("original_filename", "")
    shared_raw: list[dict[str, Any]] = doc.get("shared_with", []) or []

    return {
        "document_id": doc.get("document_id", ""),
        "original_filename": original_filename,
        "file_extension": _get_file_extension(original_filename),
        "mime_type": doc.get("mime_type", "application/octet-stream"),
        "file_size": file_size,
        "file_size_display": _format_file_size(file_size),
        "sha256_hash": doc.get("sha256_hash", ""),
        "owner_id": doc.get("owner_id", ""),
        "is_deleted": is_deleted,
        "status": "deleted" if is_deleted else "active",
        "created_at": created.isoformat() if created else "",
        "updated_at": updated.isoformat() if updated else "",
        "shared_with_count": len(shared_raw),
    }


def _build_pagination_meta(
    total: int, page: int, per_page: int
) -> dict[str, Any]:
    """Return pagination metadata for the response."""
    total_pages: int = max(1, (total + per_page - 1) // per_page)
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }


class DocumentListingService:
    """Queries document metadata for the authenticated user.

    Usage::

        svc = DocumentListingService()
        my_docs = svc.list_my_documents(page=1)
        detail = svc.get_document_detail("abc123...")
        results = svc.search_my_documents(query="report", mime_type="application/pdf")
    """

    def __init__(self) -> None:
        self._session_mgr: SessionManager = SessionManager()
        self._doc_repo: DocumentRepository = DocumentRepository()

    # ------------------------------------------------------------------
    # Public listing methods
    # ------------------------------------------------------------------

    def list_my_documents(
        self, page: int = 1, per_page: int = DEFAULT_PER_PAGE
    ) -> dict[str, Any]:
        """Paginated list of documents owned by the current user.

        Args:
            page:     Page number (1-indexed).
            per_page: Items per page (capped at :const:`MAX_PER_PAGE`).

        Returns:
            ``{"success": True, "documents": [...], "pagination": {...}}``
        """
        session = self._session_mgr.get_current_session()
        page, per_page = self._validate_pagination(page, per_page)
        skip: int = (page - 1) * per_page

        total: int = self._doc_repo.count(
            {"owner_id": session.user_id, "is_deleted": False}
        )
        docs: list[dict[str, Any]] = self._doc_repo.find(
            filters={"owner_id": session.user_id, "is_deleted": False},
            skip=skip,
            limit=per_page,
            sort=[("created_at", -1)],
        )

        return {
            "documents": [_safe_document_info(d) for d in docs],
            "pagination": _build_pagination_meta(total, page, per_page),
        }

    def list_shared_with_me(
        self, page: int = 1, per_page: int = DEFAULT_PER_PAGE
    ) -> dict[str, Any]:
        """Paginated list of documents shared with the current user."""
        session = self._session_mgr.get_current_session()
        page, per_page = self._validate_pagination(page, per_page)
        skip: int = (page - 1) * per_page

        filters: dict[str, Any] = {
            "shared_with.user_id": session.user_id,
            "is_deleted": False,
        }
        total: int = self._doc_repo.count(filters)
        docs: list[dict[str, Any]] = self._doc_repo.find(
            filters=filters,
            skip=skip,
            limit=per_page,
            sort=[("created_at", -1)],
        )

        return {
            "documents": [_safe_document_info(d) for d in docs],
            "pagination": _build_pagination_meta(total, page, per_page),
        }

    def get_document_detail(self, document_id: str) -> dict[str, Any]:
        """Return safe metadata for a single document.

        The user must either own the document or have it shared with
        them (sharing check prepared for future milestone).

        Args:
            document_id: The UUID4 hex document identifier.

        Returns:
            Safe metadata dict (never exposes crypto fields).

        Raises:
            AuthenticationError: If no active session.
            DocumentNotFoundError: If the document does not exist or
                the user has no access.
        """
        session = self._session_mgr.get_current_session()

        if not document_id or not document_id.strip():
            raise ValidationError("Document ID is required.")

        doc_raw: dict[str, Any] | None = self._doc_repo.get_by_id(
            document_id
        )
        if doc_raw is None:
            raise DocumentNotFoundError(
                f"Document '{document_id}' not found."
            )

        if doc_raw.get("owner_id") != session.user_id:
            shared_users: list = doc_raw.get("shared_with", []) or []
            has_access: bool = any(
                su.get("user_id") == session.user_id for su in shared_users
            )
            if not has_access:
                raise DocumentNotFoundError(
                    f"Document '{document_id}' not found."
                )

        return _safe_document_info(doc_raw)

    def search_my_documents(
        self,
        query: str = "",
        mime_type: str | None = None,
        page: int = 1,
        per_page: int = DEFAULT_PER_PAGE,
    ) -> dict[str, Any]:
        """Search and filter documents owned by the current user.

        Args:
            query:     Search term matched against filename (text search).
            mime_type: Optional MIME type filter.
            page:      Page number (1-indexed).
            per_page:  Items per page.

        Returns:
            ``{"success": True, "documents": [...], "pagination": {...}}``
        """
        session = self._session_mgr.get_current_session()
        page, per_page = self._validate_pagination(page, per_page)
        skip: int = (page - 1) * per_page

        filters: dict[str, Any] = {
            "owner_id": session.user_id,
            "is_deleted": False,
        }
        if query and query.strip():
            filters["$text"] = {"$search": query.strip()}
        if mime_type:
            filters["mime_type"] = mime_type

        total: int = self._doc_repo.count(filters)
        docs: list[dict[str, Any]] = self._doc_repo.find(
            filters=filters,
            skip=skip,
            limit=per_page,
            sort=[("created_at", -1)],
        )

        return {
            "documents": [_safe_document_info(d) for d in docs],
            "pagination": _build_pagination_meta(total, page, per_page),
        }

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_pagination(
        page: int, per_page: int
    ) -> tuple[int, int]:
        """Validate and clamp pagination parameters.

        Args:
            page:     Requested page (1-indexed).
            per_page: Requested items per page.

        Returns:
            ``(page, per_page)`` with safe defaults applied.
        """
        if not isinstance(page, int) or page < 1:
            page = 1
        if not isinstance(per_page, int) or per_page < 1:
            per_page = DEFAULT_PER_PAGE
        if per_page > MAX_PER_PAGE:
            per_page = MAX_PER_PAGE
        return page, per_page
