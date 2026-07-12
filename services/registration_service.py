"""Registration service — validates input, hashes passwords, generates
RSA key pairs, and persists new users via the repository layer.

This service sits between the controller and the database/crypto
modules.  It contains **no** database logic or cryptographic
implementation — it only orchestrates calls to the existing
crypto and repository abstractions.
"""

from __future__ import annotations

import re
from typing import Any

from crypto.hashing import SHA256Hasher
from crypto.key_generator import generate_crypto_id
from crypto.rsa_cipher import RSACipher
from database.repositories.user_repository import UserRepository
from exceptions.custom_exceptions import ValidationError
from logger.logging_config import get_logger
from models.user import User, VALID_ROLES

logger = get_logger(__name__)

USERNAME_PATTERN: re.Pattern[str] = re.compile(r"^[a-zA-Z0-9_]{3,30}$")

# Characters that will be replaced with underscores in usernames
USERNAME_REPLACE_CHARS: str = r"\s+"


class RegistrationService:
    """Coordinates the full user-registration workflow.

    Usage::

        service = RegistrationService()
        result = service.register("alice", "Str0ng!Pass", "editor")
    """

    def __init__(self) -> None:
        self._hasher: SHA256Hasher = SHA256Hasher()
        self._user_repo: UserRepository = UserRepository()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(self, username: str, password: str, role: str) -> dict[str, Any]:
        """Register a new user.

        The registration flow is:

        1. Normalize the username (spaces → underscores).
        2. Validate all input fields.
        3. Check that the username is not already taken.
        4. Hash the password with SHA-256 (plaintext is never stored).
        5. Generate an RSA-2048 key pair for the user.
        6. Build a :class:`~models.user.User` object.
        7. Persist the user via :class:`UserRepository`.
        8. Return a success summary (without secrets).

        Args:
            username: Desired login name (3–30 alphanumeric chars +
                      underscores). Spaces are auto-converted.
            password: Plaintext password (min 8 chars, must contain
                      uppercase, lowercase, a digit, and a special char).
            role:     ``"admin"``, ``"editor"``, or ``"viewer"``.

        Returns:
            A dict with registration metadata::

                {
                    "user_id": "...",
                    "username": "...",
                    "role": "...",
                    "created_at": "..."
                }

        Raises:
            ValidationError: If any input is invalid or the username
                is already taken.
            DuplicateKeyError: Propagated from the repository layer
                if a race condition causes a duplicate.
            CryptographicError: Propagated if key generation or
                hashing fails.
            DatabaseError: Propagated on storage failure.
        """
        normalized_username = self._normalize_username(username)
        if normalized_username != username:
            logger.info(
                "Username '%s' normalized to '%s'.", username, normalized_username
            )
        username = normalized_username

        self._validate_username(username)
        self._validate_password(password)
        self._validate_role(role)

        self._ensure_username_unique(username)

        password_hash: str = self._hash_password(password)
        rsa_public_key, rsa_private_key = self._generate_rsa_keys()
        user_id: str = generate_crypto_id()

        user = User(
            user_id=user_id,
            username=username,
            password_hash=password_hash,
            role=role,
            rsa_public_key=rsa_public_key,
            rsa_private_key=rsa_private_key,
        )

        self._user_repo.create_user(user)
        logger.info("User '%s' registered successfully (user_id=%s).", username, user_id)

        return {
            "user_id": user_id,
            "username": username,
            "role": role,
            "created_at": user.created_at.isoformat(),
        }

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_username(username: str) -> str:
        """Replace whitespace sequences with underscores."""
        normalized = re.sub(r"\s+", "_", username.strip())
        return normalized

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_username(username: str) -> None:
        """Check that *username* matches the required pattern."""
        if not username or not username.strip():
            raise ValidationError("Username is required.")
        if not USERNAME_PATTERN.match(username):
            raise ValidationError(
                "Username must be 3–30 characters long and may only "
                "contain letters, digits, and underscores. "
                "Spaces are automatically converted to underscores."
            )

    @staticmethod
    def _validate_password(password: str) -> None:
        """Enforce minimum password strength requirements.

        Displays ALL missing requirements at once rather than failing
        on the first one.
        """
        rules: list[tuple[str, str]] = [
            (r".{8,}", "At least 8 characters"),
            (r"[A-Z]", "One uppercase letter"),
            (r"[a-z]", "One lowercase letter"),
            (r"[0-9]", "One digit"),
            (r"[^a-zA-Z0-9]", "One special character"),
        ]
        missing: list[str] = []

        if not password:
            raise ValidationError("Password is required.")

        for pattern, label in rules:
            if not re.search(pattern, password):
                missing.append(label)

        if missing:
            detail = "\n  ".join(f"- {m}" for m in missing)
            raise ValidationError(
                f"Password does not meet requirements:\n  {detail}"
            )

    @staticmethod
    def _validate_role(role: str) -> None:
        """Check that *role* is a known RBAC role."""
        if not role:
            raise ValidationError("Role is required.")
        if role not in VALID_ROLES:
            raise ValidationError(
                f"Invalid role '{role}'. "
                f"Must be one of {sorted(VALID_ROLES)}."
            )

    def _ensure_username_unique(self, username: str) -> None:
        """Raise if *username* is already registered."""
        if self._user_repo.username_exists(username):
            raise ValidationError(
                f"The username '{username}' is already taken."
            )

    # ------------------------------------------------------------------
    # Cryptographic helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _hash_password(password: str) -> str:
        """Return the SHA-256 hex digest of *password*.

        The plaintext is never stored or logged.
        """
        hasher: SHA256Hasher = SHA256Hasher()
        return hasher.hash_string(password)

    @staticmethod
    def _generate_rsa_keys() -> tuple[str, str]:
        """Generate an RSA-2048 key pair and return PEM-encoded strings.

        Returns:
            ``(public_key_pem, private_key_pem)`` as text strings.
        """
        rsa_cipher: RSACipher = RSACipher()
        rsa_cipher.generate_keypair()
        pub_pem: str = rsa_cipher.export_public_key().decode("utf-8")
        priv_pem: str = rsa_cipher.export_private_key().decode("utf-8")
        return pub_pem, priv_pem
