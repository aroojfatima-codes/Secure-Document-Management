"""Integration tests for document listing, detail, and search.

Tests cover the full metadata-retrieval pipeline:
authentication guards, pagination, safe-field exposure,
search and filtering, and error handling.
"""

from __future__ import annotations

import os
import tempfile
from typing import Any

import pytest

from controllers.document_controller import DocumentController
from database.repositories.document_repository import DocumentRepository
from exceptions.custom_exceptions import AuthenticationError
from services.document_listing_service import DocumentListingService
from services.document_service import DocumentUploadService
from services.session_manager import SessionManager


# ======================================================================
# Helpers
# ======================================================================


def _upload_doc(
    svc: DocumentUploadService, content: bytes = b"test"
) -> dict[str, Any]:
    """Upload a temporary document and return the result."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(content)
        tmp: str = f.name
    try:
        return svc.upload(tmp)
    finally:
        os.unlink(tmp)


def _cleanup_encrypted(result: dict[str, Any]) -> None:
    from storage.manager import StorageManager

    if "encrypted_filename" in result:
        StorageManager().delete_encrypted_file(result["encrypted_filename"])


# ======================================================================
# DocumentListingService
# ======================================================================


class TestDocumentListingServiceAuth:
    """Authentication guards on every listing method."""

    def test_list_my_documents_requires_auth(
        self,
        document_listing_service: DocumentListingService,
    ) -> None:
        SessionManager().logout()
        with pytest.raises(AuthenticationError, match="No active session"):
            document_listing_service.list_my_documents()

    def test_list_shared_with_me_requires_auth(
        self,
        document_listing_service: DocumentListingService,
    ) -> None:
        SessionManager().logout()
        with pytest.raises(AuthenticationError, match="No active session"):
            document_listing_service.list_shared_with_me()

    def test_get_document_detail_requires_auth(
        self,
        document_listing_service: DocumentListingService,
    ) -> None:
        SessionManager().logout()
        with pytest.raises(AuthenticationError, match="No active session"):
            document_listing_service.get_document_detail("doc_001")

    def test_search_my_documents_requires_auth(
        self,
        document_listing_service: DocumentListingService,
    ) -> None:
        SessionManager().logout()
        with pytest.raises(AuthenticationError, match="No active session"):
            document_listing_service.search_my_documents(query="test")


class TestDocumentListingServiceList:
    """Paginated listing of owned documents."""

    def test_list_empty_when_no_documents(
        self,
        document_listing_service: DocumentListingService,
        logged_in_user: dict,
    ) -> None:
        result = document_listing_service.list_my_documents()
        assert result["documents"] == []
        pag = result["pagination"]
        assert pag["total"] == 0
        assert pag["page"] == 1
        assert pag["total_pages"] == 1

    def test_list_returns_uploaded_documents(
        self,
        document_listing_service: DocumentListingService,
        logged_in_user: dict,
        uploaded_doc: dict,
    ) -> None:
        result = document_listing_service.list_my_documents()
        assert len(result["documents"]) == 1
        doc = result["documents"][0]
        assert doc["document_id"] == uploaded_doc["document_id"]
        assert doc["original_filename"] == uploaded_doc["original_filename"]
        assert doc["file_size"] == uploaded_doc["file_size"]
        assert doc["sha256_hash"] == uploaded_doc["sha256_hash"]

    def test_list_never_exposes_crypto_fields(
        self,
        document_listing_service: DocumentListingService,
        logged_in_user: dict,
        uploaded_doc: dict,
    ) -> None:
        result = document_listing_service.list_my_documents()
        doc = result["documents"][0]
        assert "encrypted_aes_key" not in doc
        assert "iv" not in doc
        assert "encrypted_filename" not in doc
        assert "algorithm" not in doc

    def test_list_includes_safe_fields(
        self,
        document_listing_service: DocumentListingService,
        logged_in_user: dict,
        uploaded_doc: dict,
    ) -> None:
        result = document_listing_service.list_my_documents()
        doc = result["documents"][0]
        assert "document_id" in doc
        assert "original_filename" in doc
        assert "file_extension" in doc
        assert "mime_type" in doc
        assert "file_size" in doc
        assert "file_size_display" in doc
        assert "sha256_hash" in doc
        assert "owner_id" in doc
        assert "is_deleted" in doc
        assert "status" in doc
        assert "created_at" in doc
        assert "updated_at" in doc
        assert "shared_with_count" in doc

    def test_list_pagination_defaults(
        self,
        document_listing_service: DocumentListingService,
        logged_in_user: dict,
        uploaded_doc: dict,
    ) -> None:
        result = document_listing_service.list_my_documents()
        pag = result["pagination"]
        assert pag["page"] == 1
        assert pag["per_page"] == 20
        assert pag["total"] == 1
        assert pag["total_pages"] == 1
        assert pag["has_next"] is False
        assert pag["has_previous"] is False

    def test_list_pagination_multi_page(
        self,
        document_listing_service: DocumentListingService,
        logged_in_user: dict,
        uploaded_doc: dict,
    ) -> None:
        result = document_listing_service.list_my_documents(page=1, per_page=1)
        pag = result["pagination"]
        assert pag["total"] == 1
        assert pag["total_pages"] == 1

    def test_list_page_out_of_range(
        self,
        document_listing_service: DocumentListingService,
        logged_in_user: dict,
        uploaded_doc: dict,
    ) -> None:
        result = document_listing_service.list_my_documents(page=99)
        assert result["documents"] == []
        assert result["pagination"]["page"] == 99
        assert result["pagination"]["total"] == 1

    def test_list_multiple_documents(
        self,
        document_listing_service: DocumentListingService,
        logged_in_user: dict,
    ) -> None:
        r1: dict = _upload_doc(
            DocumentUploadService(), b"List test doc A"
        )
        r2: dict = _upload_doc(
            DocumentUploadService(), b"List test doc B"
        )
        try:
            result = document_listing_service.list_my_documents()
            assert len(result["documents"]) == 2
            ids: list[str] = [d["document_id"] for d in result["documents"]]
            assert r1["document_id"] in ids
            assert r2["document_id"] in ids
        finally:
            _cleanup_encrypted(r1)
            _cleanup_encrypted(r2)

    def test_list_only_owned_documents(
        self,
        document_listing_service: DocumentListingService,
        logged_in_user: dict,
        uploaded_doc: dict,
        doc_repo: DocumentRepository,
    ) -> None:
        result = document_listing_service.list_my_documents()
        for d in result["documents"]:
            assert d["owner_id"] == logged_in_user["user_id"]


class TestDocumentListingServiceListShared:
    """Documents shared with the current user."""

    def test_list_shared_returns_empty_when_none(
        self,
        document_listing_service: DocumentListingService,
        logged_in_user: dict,
    ) -> None:
        result = document_listing_service.list_shared_with_me()
        assert result["documents"] == []
        assert result["pagination"]["total"] == 0

    def test_list_shared_shows_shared_docs(
        self,
        document_listing_service: DocumentListingService,
        logged_in_user: dict,
        recipient_user: dict,
        uploaded_doc: dict,
        document_sharing_service,
    ) -> None:
        document_sharing_service.share_document(
            uploaded_doc["document_id"], "share_recipient"
        )
        SessionManager().logout()

        from services.auth_service import AuthService

        AuthService().login("share_recipient", "RecipP@ss1")

        result = document_listing_service.list_shared_with_me()
        assert len(result["documents"]) == 1
        assert (
            result["documents"][0]["document_id"]
            == uploaded_doc["document_id"]
        )


class TestDocumentListingServiceDetail:
    """Single-document detail view."""

    def test_detail_shows_safe_metadata(
        self,
        document_listing_service: DocumentListingService,
        logged_in_user: dict,
        uploaded_doc: dict,
    ) -> None:
        doc = document_listing_service.get_document_detail(
            uploaded_doc["document_id"]
        )
        assert doc["document_id"] == uploaded_doc["document_id"]
        assert doc["original_filename"] == uploaded_doc["original_filename"]
        assert doc["file_size"] == uploaded_doc["file_size"]
        assert doc["sha256_hash"] == uploaded_doc["sha256_hash"]
        assert doc["status"] == "active"
        assert doc["is_deleted"] is False

    def test_detail_never_exposes_crypto_fields(
        self,
        document_listing_service: DocumentListingService,
        logged_in_user: dict,
        uploaded_doc: dict,
    ) -> None:
        doc = document_listing_service.get_document_detail(
            uploaded_doc["document_id"]
        )
        assert "encrypted_aes_key" not in doc
        assert "iv" not in doc
        assert "encrypted_filename" not in doc
        assert "algorithm" not in doc

    def test_detail_nonexistent_document(
        self,
        document_listing_service: DocumentListingService,
        logged_in_user: dict,
    ) -> None:
        from database.exceptions import DocumentNotFoundError

        with pytest.raises(DocumentNotFoundError, match="not found"):
            document_listing_service.get_document_detail(
                "nonexistent_doc_id"
            )

    def test_detail_empty_id(
        self,
        document_listing_service: DocumentListingService,
        logged_in_user: dict,
    ) -> None:
        from exceptions.custom_exceptions import ValidationError

        with pytest.raises(ValidationError, match="Document ID is required"):
            document_listing_service.get_document_detail("")

    def test_detail_different_owner_denied(
        self,
        document_listing_service: DocumentListingService,
        logged_in_user: dict,
        uploaded_doc: dict,
        auth_controller,
    ) -> None:
        auth_controller.register(
            "other_user", "OtherP@ss1", "viewer"
        )
        SessionManager().logout()
        auth_controller.login("other_user", "OtherP@ss1")

        from database.exceptions import DocumentNotFoundError

        with pytest.raises(DocumentNotFoundError, match="not found"):
            document_listing_service.get_document_detail(
                uploaded_doc["document_id"]
            )


class TestDocumentListingServiceSearch:
    """Search and filtering of owned documents."""

    def test_search_empty(
        self,
        document_listing_service: DocumentListingService,
        logged_in_user: dict,
    ) -> None:
        result = document_listing_service.search_my_documents()
        assert result["documents"] == []

    def test_search_by_filename(
        self,
        document_listing_service: DocumentListingService,
        logged_in_user: dict,
        uploaded_doc: dict,
    ) -> None:
        result = document_listing_service.search_my_documents(query="txt")
        assert len(result["documents"]) == 1
        assert (
            result["documents"][0]["document_id"]
            == uploaded_doc["document_id"]
        )

    def test_search_no_match(
        self,
        document_listing_service: DocumentListingService,
        logged_in_user: dict,
        uploaded_doc: dict,
    ) -> None:
        result = document_listing_service.search_my_documents(
            query="zzz_nonexistent"
        )
        assert result["documents"] == []

    def test_search_by_mime_type(
        self,
        document_listing_service: DocumentListingService,
        logged_in_user: dict,
        uploaded_doc: dict,
    ) -> None:
        result = document_listing_service.search_my_documents(
            mime_type="text/plain"
        )
        assert len(result["documents"]) == 1
        assert (
            result["documents"][0]["document_id"]
            == uploaded_doc["document_id"]
        )

    def test_search_by_mime_no_match(
        self,
        document_listing_service: DocumentListingService,
        logged_in_user: dict,
        uploaded_doc: dict,
    ) -> None:
        result = document_listing_service.search_my_documents(
            mime_type="application/pdf"
        )
        assert result["documents"] == []

    def test_search_pagination(
        self,
        document_listing_service: DocumentListingService,
        logged_in_user: dict,
        uploaded_doc: dict,
    ) -> None:
        result = document_listing_service.search_my_documents(
            page=1, per_page=1
        )
        assert len(result["documents"]) == 1
        assert result["pagination"]["total"] == 1


# ======================================================================
# DocumentController
# ======================================================================


class TestDocumentControllerListing:
    """Controller-level error handling for listing methods."""

    def test_list_my_documents_success(
        self,
        document_controller: DocumentController,
        logged_in_user: dict,
        uploaded_doc: dict,
    ) -> None:
        result = document_controller.list_my_documents()
        assert result["success"] is True
        assert len(result["documents"]) == 1

    def test_list_my_documents_not_authenticated(
        self,
        document_controller: DocumentController,
    ) -> None:
        SessionManager().logout()
        result = document_controller.list_my_documents()
        assert result["success"] is False
        assert "documents" in result

    def test_list_shared_not_authenticated(
        self,
        document_controller: DocumentController,
    ) -> None:
        SessionManager().logout()
        result = document_controller.list_shared_with_me()
        assert result["success"] is False
        assert "documents" in result

    def test_detail_success(
        self,
        document_controller: DocumentController,
        logged_in_user: dict,
        uploaded_doc: dict,
    ) -> None:
        result = document_controller.get_document_detail(
            uploaded_doc["document_id"]
        )
        assert result["success"] is True
        assert result["document"]["document_id"] == uploaded_doc["document_id"]

    def test_detail_not_authenticated(
        self,
        document_controller: DocumentController,
    ) -> None:
        SessionManager().logout()
        result = document_controller.get_document_detail("doc_001")
        assert result["success"] is False

    def test_detail_not_found(
        self,
        document_controller: DocumentController,
        logged_in_user: dict,
    ) -> None:
        result = document_controller.get_document_detail("nonexistent_id")
        assert result["success"] is False
        assert "not found" in result.get("error", "").lower()

    def test_detail_empty_id(
        self,
        document_controller: DocumentController,
        logged_in_user: dict,
    ) -> None:
        result = document_controller.get_document_detail("")
        assert result["success"] is False
        assert "required" in result.get("error", "").lower()

    def test_search_success(
        self,
        document_controller: DocumentController,
        logged_in_user: dict,
        uploaded_doc: dict,
    ) -> None:
        result = document_controller.search_my_documents(query="txt")
        assert result["success"] is True
        assert len(result["documents"]) == 1

    def test_search_not_authenticated(
        self,
        document_controller: DocumentController,
    ) -> None:
        SessionManager().logout()
        result = document_controller.search_my_documents(query="test")
        assert result["success"] is False
        assert "documents" in result

    def test_search_includes_metadata(
        self,
        document_controller: DocumentController,
        logged_in_user: dict,
        uploaded_doc: dict,
    ) -> None:
        result = document_controller.search_my_documents(query="txt")
        assert result["search_query"] == "txt"
        assert result["mime_filter"] is None


# ======================================================================
# Cleanup after all listing tests in this module
# ======================================================================


def teardown_module() -> None:
    """Remove any leftover encrypted files from storage."""
    from storage.manager import StorageManager

    storage = StorageManager()
    if storage.encrypted_dir.is_dir():
        for f in storage.encrypted_dir.iterdir():
            if f.suffix == ".enc":
                f.unlink()
