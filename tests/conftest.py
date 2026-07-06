"""Shared test fixtures for the SDMS test suite."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Generator

import pytest

from controllers.auth_controller import AuthController
from controllers.document_controller import DocumentController
from database.manager import DatabaseManager
from database.repositories.document_repository import DocumentRepository
from database.repositories.user_repository import UserRepository
from models.document import Document, SharedUser
from models.user import User
from services.auth_service import AuthService
from services.document_download_service import DocumentDownloadService
from services.document_listing_service import DocumentListingService
from services.document_service import DocumentUploadService
from services.document_sharing_service import DocumentSharingService
from services.registration_service import RegistrationService
from services.session_manager import SessionManager


@pytest.fixture(scope="session")
def db_manager() -> Generator[DatabaseManager, None, None]:
    """Provide a connected DatabaseManager for the test session."""
    mgr = DatabaseManager()
    mgr.connect()
    mgr.create_indexes()
    yield mgr
    mgr.get_collection("users").delete_many({})
    mgr.get_collection("documents").delete_many({})
    mgr.disconnect()


@pytest.fixture(autouse=True)
def _clean_collections_and_session(
    db_manager: DatabaseManager,
) -> Generator:
    """Clean collections and session state before every test."""
    db_manager.get_collection("users").delete_many({})
    db_manager.get_collection("documents").delete_many({})
    SessionManager().logout()
    yield


@pytest.fixture
def user_repo(db_manager: DatabaseManager) -> UserRepository:
    return UserRepository()


@pytest.fixture
def doc_repo(db_manager: DatabaseManager) -> DocumentRepository:
    return DocumentRepository()


@pytest.fixture
def registration_service() -> RegistrationService:
    return RegistrationService()


@pytest.fixture
def auth_service() -> AuthService:
    return AuthService()


@pytest.fixture
def auth_controller() -> AuthController:
    return AuthController()


@pytest.fixture
def session_mgr() -> SessionManager:
    return SessionManager()


@pytest.fixture
def sample_user() -> User:
    return User(
        user_id="usr_001_test",
        username="testuser",
        password_hash="a" * 64,
        role="editor",
        rsa_public_key="pub_key_placeholder",
        rsa_private_key="priv_key_placeholder",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        is_active=True,
    )


@pytest.fixture
def sample_document() -> Document:
    return Document(
        document_id="doc_001_test",
        original_filename="report.pdf",
        encrypted_filename="enc_report.pdf",
        owner_id="usr_001_test",
        encrypted_aes_key="base64_encrypted_key",
        iv="base64_iv_here",
        sha256_hash="b" * 64,
        file_size=1024,
        mime_type="application/pdf",
        algorithm="AES-256-CBC",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        is_deleted=False,
        shared_with=[
            SharedUser(
                user_id="usr_002",
                permission="view",
                encrypted_aes_key="recipient_encrypted_key",
                shared_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            )
        ],
    )


@pytest.fixture
def registered_user(auth_controller: AuthController) -> dict:
    """Register a user and return the result dict."""
    return auth_controller.register(
        "login_test", "TestP@ss123", "editor"
    )


@pytest.fixture
def document_upload_service() -> DocumentUploadService:
    return DocumentUploadService()


@pytest.fixture
def document_controller() -> DocumentController:
    return DocumentController()


@pytest.fixture
def logged_in_user(
    auth_service: AuthService,
    registered_user: dict,
) -> dict:
    """Register and log in a user. Returns login result."""
    return auth_service.login("login_test", "TestP@ss123")


@pytest.fixture
def document_listing_service() -> DocumentListingService:
    return DocumentListingService()


@pytest.fixture
def document_download_service() -> DocumentDownloadService:
    return DocumentDownloadService()


@pytest.fixture
def document_sharing_service() -> DocumentSharingService:
    return DocumentSharingService()


@pytest.fixture
def second_user(
    auth_controller: AuthController,
) -> dict:
    """Register a second user for ownership-denial tests."""
    return auth_controller.register(
        "second_user_dl", "SecondP@ss1", "viewer"
    )


@pytest.fixture
def recipient_user(
    auth_controller: AuthController,
) -> dict:
    """Register a recipient user for sharing tests."""
    return auth_controller.register(
        "share_recipient", "RecipP@ss1", "viewer"
    )


@pytest.fixture
def uploaded_doc(
    document_upload_service: DocumentUploadService,
    logged_in_user: dict,
) -> Generator[dict, None, None]:
    """Upload a small test document and return the upload result.
    Cleans up the encrypted file after the test.
    """
    import os
    import tempfile

    from storage.manager import StorageManager

    content: bytes = b"Listing service test document content."
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(content)
        tmp_path: str = f.name

    result: dict = document_upload_service.upload(tmp_path)
    os.unlink(tmp_path)

    yield result

    if "encrypted_filename" in result:
        StorageManager().delete_encrypted_file(result["encrypted_filename"])
