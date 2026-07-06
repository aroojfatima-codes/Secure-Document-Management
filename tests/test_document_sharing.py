"""Integration tests for secure document sharing and access control.

Tests the key re-encryption sharing flow, ownership verification,
duplicate and self-share prevention, recipient validation, and
shared-user document download.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import pytest

from controllers.document_controller import DocumentController
from database.repositories.document_repository import DocumentRepository
from exceptions.custom_exceptions import (
    AuthenticationError,
    ValidationError,
)
from services.document_download_service import DocumentDownloadService
from services.document_service import DocumentUploadService
from services.document_sharing_service import DocumentSharingService
from services.session_manager import SessionManager
from storage.manager import StorageManager


# ======================================================================
# Helpers
# ======================================================================


def _upload_doc(content: bytes = b"Sharing test content.") -> dict[str, Any]:
    """Upload a temp file and return the upload result.  Caller must
    log in first.
    """
    svc: DocumentUploadService = DocumentUploadService()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(content)
        tmp: str = f.name
    try:
        return svc.upload(tmp)
    finally:
        os.unlink(tmp)


def _cleanup_encrypted(result: dict[str, Any]) -> None:
    if "encrypted_filename" in result:
        StorageManager().delete_encrypted_file(result["encrypted_filename"])


# ======================================================================
# DocumentSharingService
# ======================================================================


class TestDocumentSharingServiceAuth:
    """Authentication and ownership guards."""

    def test_share_requires_authentication(
        self,
    ) -> None:
        SessionManager().logout()
        svc = DocumentSharingService()
        with pytest.raises(AuthenticationError, match="No active session"):
            svc.share_document("doc_001", "someone")

    def test_share_requires_document_id(
        self,
        document_sharing_service: DocumentSharingService,
        logged_in_user: dict,
    ) -> None:
        with pytest.raises(ValidationError, match="Document ID is required"):
            document_sharing_service.share_document("", "someone")

    def test_share_requires_recipient_username(
        self,
        document_sharing_service: DocumentSharingService,
        logged_in_user: dict,
    ) -> None:
        with pytest.raises(
            ValidationError, match="Recipient username is required"
        ):
            document_sharing_service.share_document("doc_001", "")

    def test_share_nonexistent_document(
        self,
        document_sharing_service: DocumentSharingService,
        logged_in_user: dict,
    ) -> None:
        from database.exceptions import DocumentNotFoundError

        with pytest.raises(DocumentNotFoundError, match="not found"):
            document_sharing_service.share_document(
                "nonexistent_id", "someone"
            )

    def test_share_non_owner_denied(
        self,
        document_sharing_service: DocumentSharingService,
        logged_in_user: dict,
        second_user: dict,
        uploaded_doc: dict,
        auth_service,
    ) -> None:
        SessionManager().logout()
        auth_service.login("second_user_dl", "SecondP@ss1")

        from database.exceptions import DocumentNotFoundError

        with pytest.raises(DocumentNotFoundError, match="not found"):
            document_sharing_service.share_document(
                uploaded_doc["document_id"], "some_user"
            )

    def test_share_nonexistent_recipient(
        self,
        document_sharing_service: DocumentSharingService,
        logged_in_user: dict,
        uploaded_doc: dict,
    ) -> None:
        from database.exceptions import UserNotFoundError

        with pytest.raises(UserNotFoundError, match="not found"):
            document_sharing_service.share_document(
                uploaded_doc["document_id"], "nonexistent_user"
            )

    def test_share_self_denied(
        self,
        document_sharing_service: DocumentSharingService,
        logged_in_user: dict,
        uploaded_doc: dict,
    ) -> None:
        with pytest.raises(
            ValidationError, match="Cannot share a document with yourself"
        ):
            document_sharing_service.share_document(
                uploaded_doc["document_id"], "login_test"
            )


class TestDocumentSharingServiceSuccess:
    """Successful sharing — key re-encryption and ACL update."""

    def test_share_adds_acl_entry(
        self,
        document_sharing_service: DocumentSharingService,
        logged_in_user: dict,
        recipient_user: dict,
        uploaded_doc: dict,
        doc_repo: DocumentRepository,
    ) -> None:
        result = document_sharing_service.share_document(
            uploaded_doc["document_id"], "share_recipient"
        )

        assert result["document_id"] == uploaded_doc["document_id"]
        assert result["recipient_username"] == "share_recipient"
        assert result["permission"] == "view"

        doc = doc_repo.get_by_document_id(uploaded_doc["document_id"])
        assert doc is not None
        assert len(doc.shared_with) == 1
        assert doc.shared_with[0].user_id == result["recipient_user_id"]
        assert doc.shared_with[0].encrypted_aes_key != ""

    def test_share_re_encrypts_key_for_recipient(
        self,
        document_sharing_service: DocumentSharingService,
        logged_in_user: dict,
        recipient_user: dict,
        uploaded_doc: dict,
        doc_repo: DocumentRepository,
    ) -> None:
        document_sharing_service.share_document(
            uploaded_doc["document_id"], "share_recipient"
        )

        doc = doc_repo.get_by_document_id(uploaded_doc["document_id"])
        assert doc is not None

        owner_encrypted = doc.encrypted_aes_key
        recipient_encrypted = doc.shared_with[0].encrypted_aes_key
        assert recipient_encrypted != owner_encrypted
        assert recipient_encrypted != ""

    def test_share_duplicate_denied(
        self,
        document_sharing_service: DocumentSharingService,
        logged_in_user: dict,
        recipient_user: dict,
        uploaded_doc: dict,
    ) -> None:
        document_sharing_service.share_document(
            uploaded_doc["document_id"], "share_recipient"
        )

        with pytest.raises(
            ValidationError, match="already shared"
        ):
            document_sharing_service.share_document(
                uploaded_doc["document_id"], "share_recipient"
            )

    def test_share_multiple_recipients(
        self,
        document_sharing_service: DocumentSharingService,
        logged_in_user: dict,
        recipient_user: dict,
        uploaded_doc: dict,
        auth_controller,
    ) -> None:
        auth_controller.register(
            "third_user_share", "ThirdP@ss1", "viewer"
        )

        r1 = document_sharing_service.share_document(
            uploaded_doc["document_id"], "share_recipient"
        )
        r2 = document_sharing_service.share_document(
            uploaded_doc["document_id"], "third_user_share"
        )

        assert r1["recipient_username"] != r2["recipient_username"]

        doc_repo = DocumentRepository()
        doc = doc_repo.get_by_document_id(uploaded_doc["document_id"])
        assert doc is not None
        assert len(doc.shared_with) == 2


# ======================================================================
# Shared-user document download
# ======================================================================


class TestSharedUserDownload:
    """Shared users must be able to download and decrypt documents."""

    def _setup_shared_doc(
        self,
        logged_in_user: dict,
        recipient_user: dict,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Upload a doc as logged_in_user, share with recipient,
        switch session to recipient, return (upload_result, share_result).
        """
        upload_result: dict = _upload_doc(
            b"Shared download verification content."
        )
        svc = DocumentSharingService()
        share_result = svc.share_document(
            upload_result["document_id"], "share_recipient"
        )
        SessionManager().logout()

        from services.auth_service import AuthService

        AuthService().login("share_recipient", "RecipP@ss1")
        return upload_result, share_result

    def test_shared_user_can_download(
        self,
        logged_in_user: dict,
        recipient_user: dict,
    ) -> None:
        upload_result, _ = self._setup_shared_doc(
            logged_in_user, recipient_user
        )
        output_dir: str = tempfile.mkdtemp()

        try:
            dld = DocumentDownloadService()
            result = dld.download(
                upload_result["document_id"], output_dir
            )

            assert result["document_id"] == upload_result["document_id"]
            assert result["integrity_verified"] is True

            output_path: Path = Path(result["output_path"])
            assert output_path.is_file()
            assert (
                output_path.read_bytes()
                == b"Shared download verification content."
            )

        finally:
            SessionManager().logout()
            _cleanup_encrypted(upload_result)

    def test_shared_user_restores_original_content(
        self,
        logged_in_user: dict,
        recipient_user: dict,
    ) -> None:
        original: bytes = (
            b"Different shared content for binary check."
        )
        upload_result = _upload_doc(original)
        svc = DocumentSharingService()
        svc.share_document(
            upload_result["document_id"], "share_recipient"
        )

        SessionManager().logout()

        from services.auth_service import AuthService

        AuthService().login("share_recipient", "RecipP@ss1")

        output_dir = tempfile.mkdtemp()
        try:
            dld = DocumentDownloadService()
            result = dld.download(
                upload_result["document_id"], output_dir
            )

            output_path = Path(result["output_path"])
            assert output_path.read_bytes() == original
        finally:
            SessionManager().logout()
            _cleanup_encrypted(upload_result)

    def test_shared_user_cannot_share(
        self,
        logged_in_user: dict,
        recipient_user: dict,
    ) -> None:
        upload_result, _ = self._setup_shared_doc(
            logged_in_user, recipient_user
        )

        svc = DocumentSharingService()

        from database.exceptions import DocumentNotFoundError

        with pytest.raises(DocumentNotFoundError, match="not found"):
            svc.share_document(
                upload_result["document_id"], "some_other_user"
            )


# ======================================================================
# DocumentController
# ======================================================================


class TestDocumentControllerShare:
    """Controller-level error handling for share."""

    def test_share_success_response(
        self,
        document_controller: DocumentController,
        logged_in_user: dict,
        recipient_user: dict,
        uploaded_doc: dict,
    ) -> None:
        result = document_controller.share_document(
            uploaded_doc["document_id"], "share_recipient"
        )
        assert result["success"] is True
        assert "message" in result
        assert "Document shared" in result["message"]

    def test_share_not_authenticated(
        self,
        document_controller: DocumentController,
    ) -> None:
        SessionManager().logout()
        result = document_controller.share_document("doc_001", "user")
        assert result["success"] is False
        assert "No active session" in result.get("error", "")

    def test_share_empty_id(
        self,
        document_controller: DocumentController,
        logged_in_user: dict,
    ) -> None:
        result = document_controller.share_document("", "user")
        assert result["success"] is False
        assert "required" in result.get("error", "").lower()

    def test_share_self_response(
        self,
        document_controller: DocumentController,
        logged_in_user: dict,
        uploaded_doc: dict,
    ) -> None:
        result = document_controller.share_document(
            uploaded_doc["document_id"], "login_test"
        )
        assert result["success"] is False
        assert "Cannot share" in result.get("error", "")


# ======================================================================
# Cleanup
# ======================================================================


def teardown_module() -> None:
    """Remove any leftover encrypted files from storage."""
    storage = StorageManager()
    if storage.encrypted_dir.is_dir():
        for f in storage.encrypted_dir.iterdir():
            if f.suffix == ".enc":
                f.unlink()
