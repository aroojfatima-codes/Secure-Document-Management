"""Integration tests for secure document upload and encryption.

Tests the full upload flow: authentication check, file validation,
plaintext SHA-256 hashing, AES-256-CBC encryption, RSA key wrapping,
storage on disk, and metadata persistence.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from controllers.document_controller import DocumentController
from database.repositories.document_repository import DocumentRepository
from exceptions.custom_exceptions import AuthenticationError

from services.document_service import DocumentUploadService
from services.session_manager import SessionManager
from storage.manager import StorageManager


# ======================================================================
# Helpers
# ======================================================================


def create_temp_file(content: bytes = b"Hello, SDMS upload test!") -> str:
    """Create a temporary file and return its path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(content)
        return f.name


def create_large_file(size_bytes: int) -> str:
    """Create a temporary file with *size_bytes* of data."""
    content = b"X" * size_bytes
    return create_temp_file(content)


# ======================================================================
# DocumentUploadService
# ======================================================================


class TestDocumentUploadServiceValidation:
    """File-path validation before any crypto operations."""

    def test_upload_requires_authentication(
        self,
        document_upload_service: DocumentUploadService,
    ) -> None:
        SessionManager().logout()
        with pytest.raises(AuthenticationError, match="No active session"):
            document_upload_service.upload("/some/file.pdf")

    def test_upload_empty_path(
        self,
        document_upload_service: DocumentUploadService,
        logged_in_user: dict,
    ) -> None:
        from exceptions.custom_exceptions import ValidationError

        with pytest.raises(ValidationError, match="File path is required"):
            document_upload_service.upload("")

    def test_upload_whitespace_path(
        self,
        document_upload_service: DocumentUploadService,
        logged_in_user: dict,
    ) -> None:
        from exceptions.custom_exceptions import ValidationError

        with pytest.raises(ValidationError, match="File path is required"):
            document_upload_service.upload("   ")

    def test_upload_nonexistent_file(
        self,
        document_upload_service: DocumentUploadService,
        logged_in_user: dict,
    ) -> None:
        from exceptions.custom_exceptions import ValidationError

        with pytest.raises(ValidationError, match="File not found"):
            document_upload_service.upload(
                "C:\\does_not_exist_42.pdf"
            )

    def test_upload_directory_instead_of_file(
        self,
        document_upload_service: DocumentUploadService,
        logged_in_user: dict,
    ) -> None:
        from exceptions.custom_exceptions import ValidationError

        with pytest.raises(ValidationError, match="is not a file"):
            document_upload_service.upload(
                os.path.abspath(os.path.sep)
            )

    def test_upload_empty_file(
        self,
        document_upload_service: DocumentUploadService,
        logged_in_user: dict,
    ) -> None:
        from exceptions.custom_exceptions import ValidationError

        empty_path: str = create_temp_file(b"")
        try:
            with pytest.raises(ValidationError, match="File is empty"):
                document_upload_service.upload(empty_path)
        finally:
            os.unlink(empty_path)


class TestDocumentUploadServiceSuccess:
    """Successful upload — full encryption and persistence."""

    def _cleanup(self, encrypted_filename: str | None = None) -> None:
        if encrypted_filename:
            StorageManager().delete_encrypted_file(encrypted_filename)

    def test_upload_text_file(
        self,
        document_upload_service: DocumentUploadService,
        logged_in_user: dict,
    ) -> None:
        file_path: str = create_temp_file(
            b"Secure Document Management System upload test."
        )
        encrypted_filename: str | None = None

        try:
            result = document_upload_service.upload(file_path)

            assert "document_id" in result
            assert result["document_id"]
            assert len(result["document_id"]) == 32  # UUID4 hex

            assert result["original_filename"] == Path(file_path).name
            assert result["file_size"] == len(
                b"Secure Document Management System upload test."
            )
            assert result["sha256_hash"]
            assert len(result["sha256_hash"]) == 64

            # Persisted in MongoDB
            doc_repo = DocumentRepository()
            doc = doc_repo.get_by_document_id(result["document_id"])
            assert doc is not None
            assert doc.original_filename == result["original_filename"]
            assert doc.owner_id == logged_in_user["user_id"]
            assert doc.file_size == result["file_size"]
            assert doc.sha256_hash == result["sha256_hash"]
            assert doc.encrypted_aes_key  # AES key was RSA-wrapped
            assert doc.iv  # IV was stored

            # File encrypted on disk
            encrypted_filename = result["encrypted_filename"]
            storage = StorageManager()
            assert storage.encrypted_file_exists(encrypted_filename)
            ciphertext: bytes = storage.read_encrypted_file(
                encrypted_filename
            )
            assert len(ciphertext) > 0
            # Ciphertext must NOT equal plaintext
            assert ciphertext != b"Secure Document Management System upload test."

        finally:
            self._cleanup(encrypted_filename)
            os.unlink(file_path)

    def test_upload_binary_file(
        self,
        document_upload_service: DocumentUploadService,
        logged_in_user: dict,
    ) -> None:
        content: bytes = bytes(range(256))  # 256-byte binary
        file_path: str = create_temp_file(content)
        encrypted_filename: str | None = None

        try:
            result = document_upload_service.upload(file_path)
            assert result["file_size"] == 256
            assert result["sha256_hash"]

            doc_repo = DocumentRepository()
            doc = doc_repo.get_by_document_id(result["document_id"])
            assert doc is not None

            encrypted_filename = result["encrypted_filename"]
            storage = StorageManager()
            ciphertext = storage.read_encrypted_file(encrypted_filename)
            assert ciphertext != content  # Must be encrypted

        finally:
            self._cleanup(encrypted_filename)
            os.unlink(file_path)

    def test_upload_generates_unique_document_ids(
        self,
        document_upload_service: DocumentUploadService,
        logged_in_user: dict,
    ) -> None:
        file_path1: str = create_temp_file(b"First upload.")
        file_path2: str = create_temp_file(b"Second upload.")
        encrypted1: str | None = None
        encrypted2: str | None = None

        try:
            r1 = document_upload_service.upload(file_path1)
            encrypted1 = r1["encrypted_filename"]
            r2 = document_upload_service.upload(file_path2)
            encrypted2 = r2["encrypted_filename"]

            assert r1["document_id"] != r2["document_id"]
            assert r1["encrypted_filename"] != r2["encrypted_filename"]
        finally:
            self._cleanup(encrypted1)
            self._cleanup(encrypted2)
            os.unlink(file_path1)
            os.unlink(file_path2)


# ======================================================================
# DocumentController
# ======================================================================


class TestDocumentControllerUpload:
    """Controller-level error handling tests."""

    def test_upload_success_response(
        self,
        document_controller: DocumentController,
        logged_in_user: dict,
    ) -> None:
        file_path: str = create_temp_file(b"Controller upload test.")
        encrypted_filename: str | None = None

        try:
            result = document_controller.upload(file_path)

            assert result["success"] is True
            assert "message" in result
            assert "uploaded and encrypted" in result["message"]
            assert "document_id" in result
            assert "original_filename" in result
            assert "file_size" in result
            assert "sha256_hash" in result

            encrypted_filename = result["encrypted_filename"]

        finally:
            if encrypted_filename:
                StorageManager().delete_encrypted_file(encrypted_filename)
            os.unlink(file_path)

    def test_upload_not_authenticated(
        self,
        document_controller: DocumentController,
    ) -> None:
        SessionManager().logout()
        result = document_controller.upload("/some/file.pdf")
        assert result["success"] is False
        assert "no active session" in result.get("error", "").lower()

    def test_upload_invalid_file(
        self,
        document_controller: DocumentController,
        logged_in_user: dict,
    ) -> None:
        result = document_controller.upload("")
        assert result["success"] is False
        assert "File path is required" in result.get("error", "")


# ======================================================================
# Cleanup after all upload tests in this module
# ======================================================================


def teardown_module() -> None:
    """Remove any leftover encrypted files from storage."""
    storage = StorageManager()
    if storage.encrypted_dir.is_dir():
        for f in storage.encrypted_dir.iterdir():
            if f.suffix == ".enc":
                f.unlink()
