"""Session manager — maintains the currently authenticated user's session.

Only one active session exists at a time.  Higher-level modules
(controllers, CLI) use this manager to check authentication status
and retrieve the current user's cryptographic keys.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, ClassVar

from crypto.key_generator import generate_crypto_id
from exceptions.custom_exceptions import AuthenticationError
from logger.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class Session:
    """Represents an authenticated user session.

    Attributes:
        session_id:      Unique session identifier.
        user_id:         Unique user identifier.
        username:        Login name.
        role:            RBAC role.
        rsa_public_key:  PEM-encoded RSA public key.
        rsa_private_key: PEM-encoded RSA private key.
        login_timestamp: When the session was created.
    """

    session_id: str = ""
    user_id: str = ""
    username: str = ""
    role: str = ""
    rsa_public_key: str = ""
    rsa_private_key: str = ""
    login_timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict[str, Any]:
        """Return session data as a plain dict (safe for logging)."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role,
            "login_timestamp": self.login_timestamp.isoformat(),
        }


class SessionManager:
    """Singleton session manager.

    Usage::

        mgr = SessionManager()
        mgr.create_session(user_obj)
        assert mgr.is_authenticated
        session = mgr.get_current_session()
        mgr.logout()
    """

    _instance: ClassVar[SessionManager | None] = None
    _session: Session | None = None

    def __new__(cls) -> SessionManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def create_session(
        self,
        user_id: str,
        username: str,
        role: str,
        rsa_public_key: str,
        rsa_private_key: str,
    ) -> Session:
        """Create a new authenticated session.

        Any existing session is implicitly replaced.

        Args:
            user_id:         Unique user identifier.
            username:        Login name.
            role:            RBAC role.
            rsa_public_key:  PEM-encoded RSA public key.
            rsa_private_key: PEM-encoded RSA private key.

        Returns:
            The newly created :class:`Session`.

        Raises:
            AuthenticationError: If required fields are missing.
        """
        if not user_id or not username:
            raise AuthenticationError(
                "Cannot create session — missing user identity."
            )

        session_id: str = generate_crypto_id()
        self._session = Session(
            session_id=session_id,
            user_id=user_id,
            username=username,
            role=role,
            rsa_public_key=rsa_public_key,
            rsa_private_key=rsa_private_key,
        )
        logger.info(
            "Session created for user '%s' (role=%s).",
            username,
            role,
        )
        return self._session

    def logout(self) -> None:
        """Destroy the current session, clearing all sensitive data."""
        if self._session is not None:
            username: str = self._session.username
            self._session = None
            logger.info("Session terminated for user '%s'.", username)

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def is_authenticated(self) -> bool:
        """Check whether a valid session currently exists."""
        return self._session is not None

    def get_current_session(self) -> Session:
        """Return the active session.

        Raises:
            AuthenticationError: If no session exists.
        """
        if self._session is None:
            raise AuthenticationError(
                "No active session. Please log in first."
            )
        return self._session

    def get_current_user_id(self) -> str:
        """Return the currently authenticated user's ID.

        Raises:
            AuthenticationError: If no session exists.
        """
        return self.get_current_session().user_id

    def require_role(self, *roles: str) -> None:
        """Check that the current user has one of the given roles.

        Args:
            *roles: Allowed role names (e.g. ``"admin"``, ``"editor"``).

        Raises:
            AuthenticationError: If no session exists.
            AuthorizationError: If the user's role is not in *roles*.
        """
        from exceptions.custom_exceptions import AuthorizationError

        session = self.get_current_session()
        if session.role not in roles:
            raise AuthorizationError(
                f"User '{session.username}' with role "
                f"'{session.role}' is not authorised for this "
                f"operation. Required: {roles}."
            )
