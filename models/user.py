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
        face_encoding:   Facial recognition encoding (list of floats) or empty.
        face_enrolled:   Whether the user has enrolled facial biometrics.
        is_2fa_enabled:  Whether 2FA (Two-Factor Authentication) is enabled for this user.
        two_factor_secret: Base32-encoded 2FA TOTP secret key, if 2FA is enabled.
        two_factor_backup_codes: List of backup codes for 2FA recovery, if 2FA is enabled.
        two_factor_last_verification: Timestamp of last 2FA verification, if 2FA is enabled.
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
    face_encoding: list[float] = field(default_factory=list)
    face_enrolled: bool = False
    is_2fa_enabled: bool = False
    two_factor_secret: str = ""
    two_factor_backup_codes: list[str] = field(default_factory=list)
    two_factor_last_verification: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    two_factor_attempts: int = 0
    two_factor_lockout_until: datetime | None = None

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
            "face_encoding": self.face_encoding,
            "face_enrolled": self.face_enrolled,
            "is_2fa_enabled": self.is_2fa_enabled,
            "two_factor_secret": self.two_factor_secret,
            "two_factor_backup_codes": self.two_factor_backup_codes,
            "two_factor_last_verification": self.two_factor_last_verification,
            "two_factor_attempts": self.two_factor_attempts,
            "two_factor_lockout_until": self.two_factor_lockout_until,
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
                f"Invalid role \'{self.role}\'. "
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
        raw_encoding: Any = data.get("face_encoding", [])
        face_encoding: list[float] = (
            list(raw_encoding) if raw_encoding else []
        )
        backup_codes: Any = data.get("two_factor_backup_codes", [])
        backup_codes_list: list[str] = (
            list(backup_codes) if backup_codes else []
        )

        try:
            last_verification = datetime.fromisoformat(
                data.get("two_factor_last_verification", "")
            ) if data.get("two_factor_last_verification") else datetime.now(timezone.utc)
        except (ValueError, TypeError):
            last_verification = datetime.now(timezone.utc)

        try:
            lockout_until = datetime.fromisoformat(
                data.get("two_factor_lockout_until", "")
            ) if data.get("two_factor_lockout_until") else None
        except (ValueError, TypeError):
            lockout_until = None

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
            face_encoding=face_encoding,
            face_enrolled=data.get("face_enrolled", False),
            is_2fa_enabled=data.get("is_2fa_enabled", False),
            two_factor_secret=data.get("two_factor_secret", ""),
            two_factor_backup_codes=backup_codes_list,
            two_factor_last_verification=last_verification,
            two_factor_attempts=data.get("two_factor_attempts", 0),
            two_factor_lockout_until=lockout_until,
        )

    # ------------------------------------------------------------------
    # Domain helpers (no business logic — pure data transformations)
    # ------------------------------------------------------------------

    def touch(self) -> None:
        """Set ``updated_at`` to the current UTC time."""
        self.updated_at = datetime.now(timezone.utc)

    def generate_2fa_secret(self) -> str:
        """Generate a new 2FA secret key.

        Returns:
            A base32-encoded 2FA secret key.
        """
        import base64
        import secrets

        secret = secrets.token_bytes(20)
        return base64.b32encode(secret).decode('utf-8')

    def generate_2fa_backup_codes(self) -> list[str]:
        """Generate backup codes for 2FA recovery.

        Returns:
            A list of 10 backup codes (8 characters each).
        """
        import secrets
        import string

        backup_codes = []
        for _ in range(10):
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            backup_codes.append(code)
        return backup_codes

    def enable_2fa(self, secret: str, backup_codes: list[str]) -> None:
        """Enable 2FA for this user.

        Args:
            secret: Base32-encoded 2FA TOTP secret key.
            backup_codes: List of backup codes for 2FA recovery.
        """
        self.is_2fa_enabled = True
        self.two_factor_secret = secret
        self.two_factor_backup_codes = backup_codes
        self.two_factor_last_verification = datetime.now(timezone.utc)

    def disable_2fa(self) -> None:
        """Disable 2FA for this user."""
        self.is_2fa_enabled = False
        self.two_factor_secret = ""
        self.two_factor_backup_codes = []
        self.two_factor_last_verification = datetime.now(timezone.utc)