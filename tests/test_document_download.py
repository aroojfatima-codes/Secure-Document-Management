"""Integration tests for secure document download and decryption.

Tests the full download flow: authentication, ownership verification,
RSA key unwrapping, AES-256-CBC decryption, SHA-256 integrity check,
and file output.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import pytest

from controllers.document_controller import DocumentController
from database.manager import DatabaseManager
from exceptions.custom_exceptions import (
    AuthenticationError,
    FileHandlingError,
    ValidationError,
)
from services.document_download_service import DocumentDownloadService
from services.document_service import DocumentUploadService
from services.session_manager import SessionManager
from storage.manager import StorageManager


# ======================================================================
# Helpers
# ======================================================================


def _upload_test_doc(
    content: bytes = b"SDMS download test content.",
) -> dict[str, Any]:
    """Upload a temp file and return the upload result."""
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
# DocumentDownloadService
# ======================================================================


class TestDocumentDownloadServiceAuth:
    """Authentication and ownership guards."""

    def test_download_requires_authentication(
        self,
        document_download_service: DocumentDownloadService,
    ) -> None:
        SessionManager().logout()
        dld = DocumentDownloadService()
        with pytest.raises(AuthenticationError, match="No active session"):
            dld.download("some_doc_id", tempfile.gettempdir())

    def test_download_requires_empty_id(
        self,
        document_download_service: DocumentDownloadService,
        logged_in_user: dict,
    ) -> None:
        with pytest.raises(ValidationError, match="Document ID is required"):
            document_download_service.download("", tempfile.gettempdir())

    def test_download_requires_output_dir(
        self,
        document_download_service: DocumentDownloadService,
        logged_in_user: dict,
    ) -> None:
        with pytest.raises(ValidationError, match="Output directory is required"):
            document_download_service.download("doc_001", "")

    def test_download_nonexistent_document(
        self,
        document_download_service: DocumentDownloadService,
        logged_in_user: dict,
    ) -> None:
        from database.exceptions import DocumentNotFoundError

        with pytest.raises(DocumentNotFoundError, match="not found"):
            document_download_service.download(
                "nonexistent_id", tempfile.gettempdir()
            )

    def test_download_other_owners_document_denied(
        self,
        document_download_service: DocumentDownloadService,
        logged_in_user: dict,
        second_user: dict,
        uploaded_doc: dict,
        auth_service,
    ) -> None:
        SessionManager().logout()
        auth_service.login("second_user_dl", "SecondP@ss1")

        from database.exceptions import DocumentNotFoundError

        with pytest.raises(DocumentNotFoundError, match="not found"):
            document_download_service.download(
                uploaded_doc["document_id"], tempfile.gettempdir()
            )


class TestDocumentDownloadServiceSuccess:
    """Successful download with full decryption and verification."""

    def test_download_restores_original_content(
        self,
        logged_in_user: dict,
    ) -> None:
        original_content: bytes = b"Hello, SDMS download verification!"
        upload_result: dict = _upload_test_doc(original_content)
        output_dir: str = tempfile.mkdtemp()

        try:
            dld = DocumentDownloadService()
            result = dld.download(
                upload_result["document_id"], output_dir
            )

            assert result["document_id"] == upload_result["document_id"]
            assert (
                result["original_filename"]
                == upload_result["original_filename"]
            )
            assert result["integrity_verified"] is True

            output_path: Path = Path(result["output_path"])
            assert output_path.is_file()
            restored: bytes = output_path.read_bytes()
            assert restored == original_content

        finally:
            _cleanup_encrypted(upload_result)

    def test_download_binary_content(
        self,
        logged_in_user: dict,
    ) -> None:
        original_content: bytes = bytes(range(256))
        upload_result: dict = _upload_test_doc(original_content)
        output_dir: str = tempfile.mkdtemp()

        try:
            dld = DocumentDownloadService()
            result = dld.download(
                upload_result["document_id"], output_dir
            )

            output_path = Path(result["output_path"])
            restored = output_path.read_bytes()
            assert restored == original_content
            assert result["file_size"] == 256

        finally:
            _cleanup_encrypted(upload_result)

    def test_download_large_content(
        self,
        logged_in_user: dict,
    ) -> None:
        original_content: bytes = b"A" * 100000
        upload_result: dict = _upload_test_doc(original_content)
        output_dir: str = tempfile.mkdtemp()

        try:
            dld = DocumentDownloadService()
            result = dld.download(
                upload_result["document_id"], output_dir
            )

            output_path = Path(result["output_path"])
            restored = output_path.read_bytes()
            assert restored == original_content
            assert result["file_size"] == 100000

        finally:
            _cleanup_encrypted(upload_result)

    def test_download_preserves_filename(
        self,
        logged_in_user: dict,
    ) -> None:
        original_content: bytes = b"Filename preservation test."
        upload_result: dict = _upload_test_doc(original_content)
        output_dir: str = tempfile.mkdtemp()

        try:
            dld = DocumentDownloadService()
            result = dld.download(
                upload_result["document_id"], output_dir
            )

            output_filename: str = Path(
                result["output_path"]
            ).name
            assert (
                output_filename == upload_result["original_filename"]
            )

        finally:
            _cleanup_encrypted(upload_result)

    def test_download_handles_filename_conflict(
        self,
        logged_in_user: dict,
    ) -> None:
        original_content: bytes = b"Conflict test."
        upload_result: dict = _upload_test_doc(original_content)
        output_dir: str = tempfile.mkdtemp()

        original_filename: str = upload_result["original_filename"]
        first_path: Path = Path(output_dir) / original_filename
        first_path.write_text("dummy file to cause conflict")

        try:
            dld = DocumentDownloadService()
            result = dld.download(
                upload_result["document_id"], output_dir
            )

            output_path: Path = Path(result["output_path"])
            assert output_path.is_file()
            assert output_path.name != original_filename
            assert "_1" in output_path.stem

            restored: bytes = output_path.read_bytes()
            assert restored == original_content

        finally:
            _cleanup_encrypted(upload_result)

    def test_download_creates_output_directory(
        self,
        logged_in_user: dict,
    ) -> None:
        original_content: bytes = b"Directory creation test."
        upload_result: dict = _upload_test_doc(original_content)
        base_dir: str = tempfile.mkdtemp()
        nested_dir: str = os.path.join(
            base_dir, "new_subdir", "deep"
        )

        try:
            dld = DocumentDownloadService()
            result = dld.download(
                upload_result["document_id"], nested_dir
            )

            output_path: Path = Path(result["output_path"])
            assert output_path.is_file()
            assert output_path.parent.exists()

        finally:
            _cleanup_encrypted(upload_result)


class TestDocumentDownloadServiceIntegrityFailure:
    """Integrity verification must reject tampered documents."""

    def test_download_fails_when_hash_mismatch(
        self,
        db_manager: DatabaseManager,
        logged_in_user: dict,
    ) -> None:
        original_content: bytes = (
            b"Tamper test - hash will be corrupted."
        )
        upload_result: dict = _upload_test_doc(original_content)
        output_dir: str = tempfile.mkdtemp()

        try:
            db_manager.get_collection("documents").update_one(
                {"document_id": upload_result["document_id"]},
                {"$set": {"sha256_hash": "a" * 64}},
            )

            dld = DocumentDownloadService()
            from crypto.exceptions import IntegrityCheckError

            with pytest.raises(
                IntegrityCheckError, match="Integrity verification failed"
            ):
                dld.download(
                    upload_result["document_id"], output_dir
                )

            output_path: Path = (
                Path(output_dir)
                / upload_result["original_filename"]
            )
            assert not output_path.exists()

        finally:
            _cleanup_encrypted(upload_result)


class TestDocumentDownloadServiceStorageFailure:
    """Missing / corrupted encrypted files on disk."""

    def test_download_fails_when_encrypted_file_missing(
        self,
        logged_in_user: dict,
        uploaded_doc: dict,
    ) -> None:
        StorageManager().delete_encrypted_file(
            uploaded_doc["encrypted_filename"]
        )
        output_dir: str = tempfile.mkdtemp()

        dld = DocumentDownloadService()
        with pytest.raises(FileHandlingError, match="not found"):
            dld.download(
                uploaded_doc["document_id"], output_dir
            )


# ======================================================================
# DocumentController
# ======================================================================


class TestDocumentControllerDownload:
    """Controller-level error handling for download."""

    def test_download_success_response(
        self,
        document_controller: DocumentController,
        logged_in_user: dict,
    ) -> None:
        original_content: bytes = b"Controller download test."
        upload_result: dict = _upload_test_doc(original_content)
        output_dir: str = tempfile.mkdtemp()

        try:
            result = document_controller.download(
                upload_result["document_id"], output_dir
            )

            assert result["success"] is True
            assert "message" in result
            assert "decrypted and saved" in result["message"]
            assert result["integrity_verified"] is True

            output_path: Path = Path(result["output_path"])
            assert output_path.is_file()
            assert output_path.read_bytes() == original_content

        finally:
            _cleanup_encrypted(upload_result)

    def test_download_not_authenticated(
        self,
        document_controller: DocumentController,
    ) -> None:
        SessionManager().logout()
        result = document_controller.download("doc_001", "/tmp")
        assert result["success"] is False
        assert "no active session" in result.get("error", "").lower()

    def test_download_empty_id(
        self,
        document_controller: DocumentController,
        logged_in_user: dict,
    ) -> None:
        result = document_controller.download("", "/tmp")
        assert result["success"] is False
        assert "required" in result.get("error", "").lower()

    def test_download_not_found(
        self,
        document_controller: DocumentController,
        logged_in_user: dict,
    ) -> None:
        result = document_controller.download(
            "nonexistent_doc", tempfile.gettempdir()
        )
        assert result["success"] is False
        assert "not found" in result.get("error", "").lower()

    def test_download_integrity_failure_response(
        self,
        document_controller: DocumentController,
        db_manager: DatabaseManager,
        logged_in_user: dict,
    ) -> None:
        original_content: bytes = b"Controller integrity fail test."
        upload_result: dict = _upload_test_doc(original_content)

        db_manager.get_collection("documents").update_one(
            {"document_id": upload_result["document_id"]},
            {"$set": {"sha256_hash": "b" * 64}},
        )

        output_dir: str = tempfile.mkdtemp()
        try:
            result = document_controller.download(
                upload_result["document_id"], output_dir
            )
            assert result["success"] is False
            assert "integrity" in result.get("error", "").lower()
        finally:
            _cleanup_encrypted(upload_result)


# ======================================================================
# Cleanup after all download tests in this module
# ======================================================================


def teardown_module() -> None:
    """Remove any leftover encrypted files from storage."""
    storage = StorageManager()
    if storage.encrypted_dir.is_dir():
        for f in storage.encrypted_dir.iterdir():
            if f.suffix == ".enc":
                f.unlink()
