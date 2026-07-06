"""Integration tests for the repository layer against a real MongoDB.

These tests assume a MongoDB instance is running on localhost:27017.
"""

from __future__ import annotations

import pytest

from database.exceptions import (
    DocumentNotFoundError,
    DuplicateKeyError,
    UserNotFoundError,
)
from database.repositories.document_repository import DocumentRepository
from database.repositories.user_repository import UserRepository
from models.document import Document
from models.user import User


# ======================================================================
# UserRepository
# ======================================================================


class TestUserRepositoryCreate:
    def test_create_user(self, user_repo: UserRepository, sample_user: User) -> None:
        result = user_repo.create_user(sample_user)
        assert result == sample_user.user_id

    def test_create_duplicate_user_id(
        self, user_repo: UserRepository, sample_user: User
    ) -> None:
        user_repo.create_user(sample_user)
        dupe = User(
            user_id=sample_user.user_id,
            username="different",
            password_hash="x" * 64,
        )
        with pytest.raises(DuplicateKeyError):
            user_repo.create_user(dupe)

    def test_create_duplicate_username(
        self, user_repo: UserRepository, sample_user: User
    ) -> None:
        user_repo.create_user(sample_user)
        dupe = User(
            user_id="other_id",
            username=sample_user.username,
            password_hash="x" * 64,
        )
        with pytest.raises(DuplicateKeyError):
            user_repo.create_user(dupe)


class TestUserRepositoryRead:
    def test_get_by_username(
        self, user_repo: UserRepository, sample_user: User
    ) -> None:
        user_repo.create_user(sample_user)
        fetched = user_repo.get_by_username(sample_user.username)
        assert fetched is not None
        assert fetched.user_id == sample_user.user_id
        assert fetched.role == sample_user.role

    def test_get_by_username_not_found(
        self, user_repo: UserRepository
    ) -> None:
        assert user_repo.get_by_username("nobody") is None

    def test_get_by_user_id(
        self, user_repo: UserRepository, sample_user: User
    ) -> None:
        user_repo.create_user(sample_user)
        fetched = user_repo.get_by_user_id(sample_user.user_id)
        assert fetched is not None
        assert fetched.username == sample_user.username


class TestUserRepositoryUpdate:
    def test_update_role(
        self, user_repo: UserRepository, sample_user: User
    ) -> None:
        user_repo.create_user(sample_user)
        updated = user_repo.update_user(
            sample_user.user_id, {"role": "admin"}
        )
        assert updated.role == "admin"
        assert updated.username == sample_user.username  # unchanged

    def test_update_nonexistent_user(
        self, user_repo: UserRepository
    ) -> None:
        with pytest.raises(UserNotFoundError):
            user_repo.update_user("ghost", {"role": "admin"})


class TestUserRepositoryDelete:
    def test_soft_delete(
        self, user_repo: UserRepository, sample_user: User
    ) -> None:
        user_repo.create_user(sample_user)
        updated = user_repo.soft_delete_user(sample_user.user_id)
        assert updated.is_active is False

    def test_hard_delete(
        self, user_repo: UserRepository, sample_user: User
    ) -> None:
        user_repo.create_user(sample_user)
        user_repo.delete_user(sample_user.user_id)
        assert user_repo.get_by_user_id(sample_user.user_id) is None

    def test_delete_nonexistent(self, user_repo: UserRepository) -> None:
        with pytest.raises(UserNotFoundError):
            user_repo.delete_user("ghost")


class TestUserRepositoryQuery:
    def test_username_exists(
        self, user_repo: UserRepository, sample_user: User
    ) -> None:
        user_repo.create_user(sample_user)
        assert user_repo.username_exists(sample_user.username) is True
        assert user_repo.username_exists("unknown") is False

    def test_search_users_by_role(
        self, user_repo: UserRepository, sample_user: User
    ) -> None:
        user_repo.create_user(sample_user)
        # Create another user with a different role
        other = User(
            user_id="usr_002",
            username="admin_user",
            password_hash="b" * 64,
            role="admin",
        )
        user_repo.create_user(other)
        editors = user_repo.search_users(role="editor")
        assert len(editors) == 1
        assert editors[0].user_id == sample_user.user_id
        admins = user_repo.search_users(role="admin")
        assert len(admins) == 1

    def test_search_users_by_query(
        self, user_repo: UserRepository, sample_user: User
    ) -> None:
        user_repo.create_user(sample_user)
        results = user_repo.search_users(query="test")
        assert len(results) >= 1
        results = user_repo.search_users(query="nope")
        assert len(results) == 0

    def test_get_all_users(
        self, user_repo: UserRepository, sample_user: User
    ) -> None:
        user_repo.create_user(sample_user)
        all_users = user_repo.get_all_users()
        assert len(all_users) == 1


# ======================================================================
# DocumentRepository
# ======================================================================


class TestDocumentRepositoryCreate:
    def test_create_document(
        self, doc_repo: DocumentRepository, sample_document: Document
    ) -> None:
        result = doc_repo.create_document(sample_document)
        assert result == sample_document.document_id

    def test_create_duplicate_document_id(
        self, doc_repo: DocumentRepository, sample_document: Document
    ) -> None:
        doc_repo.create_document(sample_document)
        with pytest.raises(DuplicateKeyError):
            doc_repo.create_document(sample_document)


class TestDocumentRepositoryRead:
    def test_get_by_document_id(
        self, doc_repo: DocumentRepository, sample_document: Document
    ) -> None:
        doc_repo.create_document(sample_document)
        fetched = doc_repo.get_by_document_id(sample_document.document_id)
        assert fetched is not None
        assert fetched.original_filename == "report.pdf"
        assert len(fetched.shared_with) == 1

    def test_get_by_document_id_not_found(
        self, doc_repo: DocumentRepository
    ) -> None:
        assert doc_repo.get_by_document_id("ghost") is None

    def test_get_documents_by_owner(
        self, doc_repo: DocumentRepository, sample_document: Document
    ) -> None:
        doc_repo.create_document(sample_document)
        docs = doc_repo.get_documents_by_owner(sample_document.owner_id)
        assert len(docs) == 1
        assert docs[0].document_id == sample_document.document_id

    def test_get_documents_by_owner_empty(
        self, doc_repo: DocumentRepository
    ) -> None:
        docs = doc_repo.get_documents_by_owner("nobody")
        assert len(docs) == 0

    def test_get_shared_with_user(
        self, doc_repo: DocumentRepository, sample_document: Document
    ) -> None:
        doc_repo.create_document(sample_document)
        docs = doc_repo.get_shared_with_user("usr_002")
        assert len(docs) == 1


class TestDocumentRepositoryUpdate:
    def test_update_filename(
        self, doc_repo: DocumentRepository, sample_document: Document
    ) -> None:
        doc_repo.create_document(sample_document)
        updated = doc_repo.update_document(
            sample_document.document_id,
            {"original_filename": "new_report.pdf"},
        )
        assert updated.original_filename == "new_report.pdf"
        assert updated.sha256_hash == sample_document.sha256_hash  # unchanged

    def test_update_nonexistent(
        self, doc_repo: DocumentRepository
    ) -> None:
        with pytest.raises(DocumentNotFoundError):
            doc_repo.update_document("ghost", {"original_filename": "x"})


class TestDocumentRepositoryDelete:
    def test_soft_delete(
        self, doc_repo: DocumentRepository, sample_document: Document
    ) -> None:
        doc_repo.create_document(sample_document)
        updated = doc_repo.soft_delete_document(sample_document.document_id)
        assert updated.is_deleted is True

    def test_soft_delete_hides_from_owner_query(
        self, doc_repo: DocumentRepository, sample_document: Document
    ) -> None:
        doc_repo.create_document(sample_document)
        doc_repo.soft_delete_document(sample_document.document_id)
        docs = doc_repo.get_documents_by_owner(sample_document.owner_id)
        assert len(docs) == 0  # soft-deleted documents excluded by default

    def test_hard_delete(
        self, doc_repo: DocumentRepository, sample_document: Document
    ) -> None:
        doc_repo.create_document(sample_document)
        doc_repo.delete_document(sample_document.document_id)
        assert doc_repo.get_by_document_id(sample_document.document_id) is None

    def test_delete_nonexistent(self, doc_repo: DocumentRepository) -> None:
        with pytest.raises(DocumentNotFoundError):
            doc_repo.delete_document("ghost")


class TestDocumentRepositoryQuery:
    def test_document_id_exists(
        self, doc_repo: DocumentRepository, sample_document: Document
    ) -> None:
        doc_repo.create_document(sample_document)
        assert doc_repo.document_id_exists(sample_document.document_id) is True
        assert doc_repo.document_id_exists("ghost") is False

    def test_search_documents(
        self, doc_repo: DocumentRepository, sample_document: Document
    ) -> None:
        doc_repo.create_document(sample_document)
        results = doc_repo.search_documents(query="report")
        assert len(results) >= 1

    def test_search_documents_by_mime(
        self, doc_repo: DocumentRepository, sample_document: Document
    ) -> None:
        doc_repo.create_document(sample_document)
        results = doc_repo.search_documents(mime_type="application/pdf")
        assert len(results) == 1
        results = doc_repo.search_documents(mime_type="image/png")
        assert len(results) == 0
