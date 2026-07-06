"""Unit tests for data models — validation and serialisation."""

from __future__ import annotations

import pytest

from exceptions.custom_exceptions import ValidationError
from models.document import Document, SharedUser
from models.user import User, VALID_ROLES


class TestUserModel:
    """User model validation and serialisation."""

    def test_valid_user_round_trip(self, sample_user: User) -> None:
        """A valid User survives to_dict → from_dict."""
        d = sample_user.to_dict()
        restored = User.from_dict(d)
        assert restored.user_id == sample_user.user_id
        assert restored.username == sample_user.username
        assert restored.role == sample_user.role
        assert restored.is_active is True

    def test_validate_passes_for_valid_user(self, sample_user: User) -> None:
        """No exception raised for a fully populated User."""
        sample_user.validate()

    def test_validate_fails_missing_user_id(self) -> None:
        u = User(username="x", password_hash="a" * 64)
        with pytest.raises(ValidationError, match="user_id"):
            u.validate()

    def test_validate_fails_missing_username(self) -> None:
        u = User(user_id="id1", password_hash="a" * 64)
        with pytest.raises(ValidationError, match="username"):
            u.validate()

    def test_validate_fails_missing_password_hash(self) -> None:
        u = User(user_id="id1", username="x")
        with pytest.raises(ValidationError, match="password_hash"):
            u.validate()

    @pytest.mark.parametrize("bad_role", ["superadmin", "", "user", None])
    def test_validate_fails_invalid_role(self, bad_role: str | None) -> None:
        u = User(
            user_id="id1",
            username="x",
            password_hash="a" * 64,
            role=bad_role,  # type: ignore[arg-type]
        )
        with pytest.raises(ValidationError, match="role"):
            u.validate()

    def test_all_valid_roles_accepted(self) -> None:
        for role in VALID_ROLES:
            u = User(
                user_id="id1",
                username="x",
                password_hash="a" * 64,
                role=role,
            )
            u.validate()

    def test_touch_updates_timestamp(self, sample_user: User) -> None:
        old = sample_user.updated_at
        sample_user.touch()
        assert sample_user.updated_at > old

    def test_from_dict_with_extra_fields(self) -> None:
        """Extra fields in the dict are silently ignored."""
        data = {
            "user_id": "id_x",
            "username": "extra",
            "password_hash": "d" * 64,
            "role": "viewer",
            "_id": "some_objectid",
            "unexpected": True,
        }
        u = User.from_dict(data)
        assert u.user_id == "id_x"
        assert u.username == "extra"
        assert u.is_active is True


class TestDocumentModel:
    """Document model validation and serialisation."""

    def test_valid_document_round_trip(self, sample_document: Document) -> None:
        d = sample_document.to_dict()
        restored = Document.from_dict(d)
        assert restored.document_id == sample_document.document_id
        assert restored.original_filename == "report.pdf"
        assert restored.owner_id == "usr_001_test"
        assert len(restored.shared_with) == 1
        assert restored.shared_with[0].user_id == "usr_002"
        assert restored.shared_with[0].permission == "view"

    def test_validate_passes_for_valid_document(
        self, sample_document: Document
    ) -> None:
        sample_document.validate()

    @pytest.mark.parametrize(
        "field",
        [
            "document_id",
            "original_filename",
            "encrypted_filename",
            "owner_id",
            "encrypted_aes_key",
            "iv",
            "sha256_hash",
        ],
    )
    def test_validate_fails_missing_field(self, field: str) -> None:
        doc = Document(
            document_id="d1",
            original_filename="a.txt",
            encrypted_filename="enc_a.txt",
            owner_id="u1",
            encrypted_aes_key="k",
            iv="iv",
            sha256_hash="h" * 64,
        )
        setattr(doc, field, "")
        with pytest.raises(ValidationError, match=field):
            doc.validate()

    def test_shared_user_round_trip(self) -> None:
        su = SharedUser(
            user_id="u1",
            permission="edit",
            encrypted_aes_key="base64_encrypted_key_value",
        )
        d = su.to_dict()
        restored = SharedUser.from_dict(d)
        assert restored.user_id == "u1"
        assert restored.permission == "edit"
        assert restored.encrypted_aes_key == "base64_encrypted_key_value"

    def test_add_share(self, sample_document: Document) -> None:
        sample_document.add_share("usr_003", permission="edit")
        assert len(sample_document.shared_with) == 2
        assert sample_document.shared_with[1].user_id == "usr_003"
        assert sample_document.shared_with[1].permission == "edit"

    def test_touch(self, sample_document: Document) -> None:
        old = sample_document.updated_at
        sample_document.touch()
        assert sample_document.updated_at > old

    def test_default_mime_type(self) -> None:
        doc = Document(
            document_id="d1",
            original_filename="f",
            encrypted_filename="ef",
            owner_id="u1",
            encrypted_aes_key="k",
            iv="iv",
            sha256_hash="h" * 64,
        )
        assert doc.mime_type == "application/octet-stream"
        assert doc.algorithm == "AES-256-CBC"
