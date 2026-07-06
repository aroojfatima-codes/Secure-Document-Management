"""Document model representing an encrypted document and its metadata.

Stores everything needed to locate, decrypt, and verify the
integrity of a document.  The model itself is crypto-agnostic —
it only holds pre-computed strings and bytes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from exceptions.custom_exceptions import ValidationError
from models.base import BaseModel


@dataclass
class SharedUser:
    """Represents a user with whom a document has been shared.

    Attributes:
        user_id:           The target user's unique identifier.
        permission:        Access level — ``"view"`` or ``"edit"``.
        encrypted_aes_key: The AES-256 key encrypted with the
                           recipient's RSA public key (Base64 string).
        shared_at:         Timestamp when the share was created.
    """

    user_id: str
    permission: str = "view"
    encrypted_aes_key: str = ""
    shared_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dict for MongoDB embedding."""
        return {
            "user_id": self.user_id,
            "permission": self.permission,
            "encrypted_aes_key": self.encrypted_aes_key,
            "shared_at": self.shared_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SharedUser:
        """Construct from a MongoDB sub-document."""
        return cls(
            user_id=data.get("user_id", ""),
            permission=data.get("permission", "view"),
            encrypted_aes_key=data.get("encrypted_aes_key", ""),
            shared_at=data.get("shared_at", datetime.now(timezone.utc)),
        )


@dataclass
class Document(BaseModel):
    """An encrypted document with integrity and sharing metadata.

    Attributes:
        document_id:        Unique identifier (UUID4 hex).
        original_filename:  User-visible filename before encryption.
        encrypted_filename: Filename used on disk after encryption.
        owner_id:           ``user_id`` of the document owner.
        encrypted_aes_key:  RSA-wrapped AES-256 key (Base64 string).
        iv:                 AES-CBC initialisation vector (Base64 string).
        sha256_hash:        SHA-256 hex digest of the plaintext.
        file_size:          Original plaintext size in bytes.
        mime_type:          MIME type of the original file.
        algorithm:          Encryption algorithm identifier.
        created_at:         Upload timestamp (UTC).
        updated_at:         Last modification timestamp (UTC).
        is_deleted:         Soft-delete flag.
        shared_with:        List of :class:`SharedUser` entries.
    """

    document_id: str = ""
    original_filename: str = ""
    encrypted_filename: str = ""
    owner_id: str = ""
    encrypted_aes_key: str = ""
    iv: str = ""
    sha256_hash: str = ""
    file_size: int = 0
    mime_type: str = "application/octet-stream"
    algorithm: str = "AES-256-CBC"
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    is_deleted: bool = False
    shared_with: list[SharedUser] = field(default_factory=list)

    # ------------------------------------------------------------------
    # BaseModel interface
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a MongoDB document dict (without ``_id``)."""
        return {
            "document_id": self.document_id,
            "original_filename": self.original_filename,
            "encrypted_filename": self.encrypted_filename,
            "owner_id": self.owner_id,
            "encrypted_aes_key": self.encrypted_aes_key,
            "iv": self.iv,
            "sha256_hash": self.sha256_hash,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "algorithm": self.algorithm,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_deleted": self.is_deleted,
            "shared_with": [sw.to_dict() for sw in self.shared_with],
        }

    def validate(self) -> None:
        """Validate required fields.

        Raises:
            ValidationError: If any required field is missing.
        """
        errors: list[str] = []

        if not self.document_id:
            errors.append("document_id is required.")
        if not self.original_filename:
            errors.append("original_filename is required.")
        if not self.encrypted_filename:
            errors.append("encrypted_filename is required.")
        if not self.owner_id:
            errors.append("owner_id is required.")
        if not self.encrypted_aes_key:
            errors.append("encrypted_aes_key is required.")
        if not self.iv:
            errors.append("iv is required.")
        if not self.sha256_hash:
            errors.append("sha256_hash is required.")

        if errors:
            raise ValidationError("; ".join(errors))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Document:
        """Construct a Document from a MongoDB document dict."""
        shared_raw: list[dict[str, Any]] = data.get("shared_with", []) or []
        return cls(
            document_id=data.get("document_id", ""),
            original_filename=data.get("original_filename", ""),
            encrypted_filename=data.get("encrypted_filename", ""),
            owner_id=data.get("owner_id", ""),
            encrypted_aes_key=data.get("encrypted_aes_key", ""),
            iv=data.get("iv", ""),
            sha256_hash=data.get("sha256_hash", ""),
            file_size=data.get("file_size", 0),
            mime_type=data.get("mime_type", "application/octet-stream"),
            algorithm=data.get("algorithm", "AES-256-CBC"),
            created_at=data.get("created_at", datetime.now(timezone.utc)),
            updated_at=data.get("updated_at", datetime.now(timezone.utc)),
            is_deleted=data.get("is_deleted", False),
            shared_with=[
                SharedUser.from_dict(s) for s in shared_raw
            ],
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def touch(self) -> None:
        """Set ``updated_at`` to the current UTC time."""
        self.updated_at = datetime.now(timezone.utc)

    def add_share(
        self,
        user_id: str,
        permission: str = "view",
        encrypted_aes_key: str = "",
    ) -> None:
        """Append a sharing entry (no duplicate check).

        Args:
            user_id:           Target user ID.
            permission:        ``"view"`` or ``"edit"``.
            encrypted_aes_key: AES key encrypted with the recipient's
                               RSA public key (Base64).
        """
        self.shared_with.append(
            SharedUser(
                user_id=user_id,
                permission=permission,
                encrypted_aes_key=encrypted_aes_key,
            )
        )
        self.touch()
