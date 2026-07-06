"""User model representing an authenticated system user.

Encapsulates credentials, RSA key material, role assignment, and
account status.  All cryptographic fields are stored as pre-encoded
strings — the model does not perform any crypto operations itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from exceptions.custom_exceptions import ValidationError
from models.base import BaseModel

VALID_ROLES: frozenset[str] = frozenset({"admin", "editor", "viewer"})


@dataclass
class User(BaseModel):
    """A system user with role-based access and RSA key material.

    Attributes:
        user_id:         Unique identifier (UUID4 hex).
        username:        Unique login name.
        password_hash:   SHA-256 hex digest of the user's password.
        role:            RBAC role — ``"admin"``, ``"editor"``, or ``"viewer"``.
        rsa_public_key:  PEM-encoded RSA-2048 public key (Base64 string).
        rsa_private_key: PEM-encoded encrypted RSA-2048 private key (Base64).
        created_at:      Account creation timestamp (UTC).
        updated_at:      Last modification timestamp (UTC).
        is_active:       Whether the account is enabled.
    """

    user_id: str = ""
    username: str = ""
    password_hash: str = ""
    role: str = "viewer"
    rsa_public_key: str = ""
    rsa_private_key: str = ""
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    is_active: bool = True

    # ------------------------------------------------------------------
    # BaseModel interface
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a MongoDB document dict (without ``_id``)."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "password_hash": self.password_hash,
            "role": self.role,
            "rsa_public_key": self.rsa_public_key,
            "rsa_private_key": self.rsa_private_key,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_active": self.is_active,
        }

    def validate(self) -> None:
        """Validate required fields and role value.

        Raises:
            ValidationError: If any field is invalid.
        """
        errors: list[str] = []

        if not self.user_id:
            errors.append("user_id is required.")
        if not self.username:
            errors.append("username is required.")
        if not self.password_hash:
            errors.append("password_hash is required.")
        if self.role not in VALID_ROLES:
            errors.append(
                f"Invalid role '{self.role}'. "
                f"Must be one of {sorted(VALID_ROLES)}."
            )
        if not self.created_at:
            errors.append("created_at is required.")

        if errors:
            raise ValidationError("; ".join(errors))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> User:
        """Construct a User from a MongoDB document dict.

        Handles both raw MongoDB documents (with ``_id``)
        and the dicts produced by :meth:`to_dict`.
        """
        return cls(
            user_id=data.get("user_id", ""),
            username=data.get("username", ""),
            password_hash=data.get("password_hash", ""),
            role=data.get("role", "viewer"),
            rsa_public_key=data.get("rsa_public_key", ""),
            rsa_private_key=data.get("rsa_private_key", ""),
            created_at=data.get("created_at", datetime.now(timezone.utc)),
            updated_at=data.get(
                "updated_at", datetime.now(timezone.utc)
            ),
            is_active=data.get("is_active", True),
        )

    # ------------------------------------------------------------------
    # Domain helpers (no business logic — pure data transformations)
    # ------------------------------------------------------------------

    def touch(self) -> None:
        """Set ``updated_at`` to the current UTC time."""
        self.updated_at = datetime.now(timezone.utc)
