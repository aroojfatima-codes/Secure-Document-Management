"""Authentication service — validates credentials, verifies password
hashes, and manages session lifecycle.

This service sits between the controller and the lower-level
crypto / database / session modules.  It contains **no** direct
cryptographic implementation or database queries.

Security note: Password hashing uses SHA-256. Both the registration
and login paths must use the exact same hashing algorithm so that
hashes match.  The ``_verify_password`` and ``_hash_password``
implementations are kept in lock-step for this reason.
"""

from __future__ import annotations

import re
from typing import Any

from crypto.hashing import SHA256Hasher
from database.repositories.user_repository import UserRepository
from exceptions.custom_exceptions import AuthenticationError, DatabaseError, ValidationError
from logger.logging_config import get_logger
from models.user import User
from services.session_manager import SessionManager

logger = get_logger(__name__)


class AuthService:
    """Coordinates login and logout workflows.

    Usage::

        service = AuthService()
        result = service.login("alice", "Str0ng!Pass")
        service.logout()
    """

    def __init__(self) -> None:
        self._hasher: SHA256Hasher = SHA256Hasher()
        self._user_repo: UserRepository = UserRepository()
        self._session_mgr: SessionManager = SessionManager()

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    def login(self, username: str, password: str) -> dict[str, Any]:
        """Authenticate a user and create an active session.

        The login flow:

        1. Validate that both fields are provided.
        2. Normalize the username (spaces → underscores).
        3. Retrieve the user record from the database.
        4. Verify the account is active.
        5. Hash the supplied password and compare with stored hash.
        6. Create a session containing user identity + RSA keys.
        7. Return a success summary (without secrets).

        Args:
            username: The user's login name (spaces auto-converted).
            password: The plaintext password to verify.

        Returns:
            A dict with login metadata::

                {
                    "user_id": "...",
                    "username": "...",
                    "role": "...",
                    "message": "Login successful."
                }

        Raises:
            ValidationError: If username or password is empty.
            AuthenticationError: If credentials are invalid or the
                account is inactive.
            DatabaseError: If the database cannot be queried.
        """
        self._validate_input(username, password)

        normalized_username = re.sub(r"\s+", "_", username.strip())
        if normalized_username != username.strip():
            logger.debug(
                "Username '%s' normalized to '%s' for lookup.",
                username, normalized_username,
            )

        try:
            user: User | None = self._user_repo.get_by_username(normalized_username)
        except DatabaseError as exc:
            logger.error("Database unavailable during login for '%s'.", normalized_username)
            raise DatabaseError(
                "Database is unavailable. Please try again later."
            ) from exc

        if user is None:
            logger.warning(
                "Login attempt for unknown user '%s' (normalized='%s').",
                username, normalized_username,
            )
            raise AuthenticationError(
                f"User '{normalized_username}' does not exist. "
                "Please check the username or register first."
            )

        if not user.is_active:
            logger.warning("Login attempt for inactive user '%s'.", normalized_username)
            raise AuthenticationError(
                "This account has been deactivated. Contact an administrator."
            )

        # Debug: log the stored hash length/prefix (safe - not full hash)
        logger.debug(
            "Verifying password for '%s' (hash prefix=%s...)",
            normalized_username,
            user.password_hash[:12] if user.password_hash else "EMPTY",
        )

        if not self._verify_password(password, user.password_hash):
            logger.warning("Incorrect password for user '%s'.", normalized_username)
            raise AuthenticationError(
                "Password incorrect. Please try again or reset your password."
            )

        self._session_mgr.create_session(
            user_id=user.user_id,
            username=user.username,
            role=user.role,
            rsa_public_key=user.rsa_public_key,
            rsa_private_key=user.rsa_private_key,
        )

        logger.info("User '%s' logged in successfully.", normalized_username)
        return {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role,
        }

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    def logout(self) -> dict[str, Any]:
        """Terminate the current session.

        Returns:
            A dict indicating success::

                {
                    "success": True,
                    "message": "Logged out successfully."
                }
        """
        if self._session_mgr.is_authenticated:
            username: str = self._session_mgr.get_current_session().username
            self._session_mgr.logout()
            return {
                "success": True,
                "message": f"User '{username}' logged out successfully.",
            }
        return {
            "success": False,
            "message": "No active session to log out from.",
        }

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------

    def is_authenticated(self) -> bool:
        """Check whether a session is currently active."""
        return self._session_mgr.is_authenticated

    def get_current_user(self) -> dict[str, Any] | None:
        """Return the current session info (without RSA keys).

        Returns:
            A dict with ``user_id``, ``username``, ``role``, and
            ``login_timestamp``, or ``None`` if not authenticated.
        """
        if not self._session_mgr.is_authenticated:
            return None
        session = self._session_mgr.get_current_session()
        return session.to_dict()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_input(username: str, password: str) -> None:
        """Check that both fields are non-empty."""
        errors: list[str] = []
        if not username or not username.strip():
            errors.append("Username is required.")
        if not password:
            errors.append("Password is required.")
        if errors:
            raise ValidationError(" ".join(errors))

    def _verify_password(self, plaintext: str, stored_hash: str) -> bool:
        """Hash *plaintext* with SHA-256 and compare to *stored_hash*.

        The plaintext is discarded immediately after the comparison.
        """
        return self._hasher.verify(plaintext.encode("utf-8"), stored_hash)
