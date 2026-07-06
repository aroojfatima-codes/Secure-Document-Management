"""Authentication service — validates credentials, verifies password
hashes, and manages session lifecycle.

This service sits between the controller and the lower-level
crypto / database / session modules.  It contains **no** direct
cryptographic implementation or database queries.
"""

from __future__ import annotations

from typing import Any

from crypto.hashing import SHA256Hasher
from database.repositories.user_repository import UserRepository
from exceptions.custom_exceptions import AuthenticationError, ValidationError
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
        2. Retrieve the user record from the database.
        3. Verify the account is active.
        4. Hash the supplied password and compare with stored hash.
        5. Create a session containing user identity + RSA keys.
        6. Return a success summary (without secrets).

        Args:
            username: The user's login name.
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
        """
        self._validate_input(username, password)

        user: User | None = self._user_repo.get_by_username(username.strip())
        if user is None:
            logger.warning("Login attempt for unknown user '%s'.", username)
            raise AuthenticationError("Invalid username or password.")

        if not user.is_active:
            logger.warning("Login attempt for inactive user '%s'.", username)
            raise AuthenticationError(
                "This account has been deactivated. Contact an administrator."
            )

        if not self._verify_password(password, user.password_hash):
            logger.warning("Incorrect password for user '%s'.", username)
            raise AuthenticationError("Invalid username or password.")

        self._session_mgr.create_session(
            user_id=user.user_id,
            username=user.username,
            role=user.role,
            rsa_public_key=user.rsa_public_key,
            rsa_private_key=user.rsa_private_key,
        )

        logger.info("User '%s' logged in successfully.", username)
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

    @staticmethod
    def _verify_password(plaintext: str, stored_hash: str) -> bool:
        """Hash *plaintext* with SHA-256 and compare to *stored_hash*.

        The plaintext is discarded immediately after the comparison.
        """
        hasher: SHA256Hasher = SHA256Hasher()
        return hasher.verify(plaintext.encode("utf-8"), stored_hash)
