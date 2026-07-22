"""Authentication controller — handles user registration, login,
and logout.

This is the thin presentation-coordination layer.  It receives
input from the GUI, delegates to the service layer, formats results,
and handles errors for display.
"""

from __future__ import annotations

from typing import Any

from database.exceptions import DuplicateKeyError
from exceptions.custom_exceptions import (
    AuthenticationError,
    SDMSException,
    ValidationError,
)
from logger.logging_config import get_logger
from models.audit import AuditAction, OperationStatus, ResourceType, SeverityLevel
from services.audit_service import AuditService
from services.auth_service import AuthService
from services.registration_service import RegistrationService

logger = get_logger(__name__)


class AuthController:
    """Coordinates authentication workflows.

    Usage::

        ctrl = AuthController()
        ctrl.register("alice", "Str0ng!Pass", "editor")
        ctrl.login("alice", "Str0ng!Pass")
        ctrl.logout()
    """

    def __init__(self) -> None:
        self._registration_service: RegistrationService = RegistrationService()
        self._auth_service: AuthService = AuthService()
        self._audit_service: AuditService = AuditService()

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self, username: str, password: str, role: str
    ) -> dict[str, Any]:
        """Register a new user and return a success summary.

        Args:
            username: Desired login name.
            password: Plaintext password (validated for strength).
            role:     ``"admin"``, ``"editor"``, or ``"viewer"``.

        Returns:
            A dict with registration metadata::

                {
                    "success": True,
                    "user_id": "...",
                    "username": "...",
                    "role": "...",
                    "message": "User '...' registered successfully."
                }
        """
        try:
            result = self._registration_service.register(
                username=username.strip(),
                password=password,
                role=role.strip().lower(),
            )
            self._audit_service.log_event(
                action=AuditAction.USER_REGISTRATION.value,
                resource_type=ResourceType.USER.value,
                resource_id=result["user_id"],
                resource_name=result["username"],
                status=OperationStatus.SUCCESS.value,
                message=f"User '{result['username']}' registered successfully with role '{result['role']}'.",
                severity=SeverityLevel.INFO.value,
            )
            return {
                "success": True,
                **result,
                "message": (
                    f"User '{result['username']}' registered "
                    f"successfully."
                ),
            }
        except ValidationError as exc:
            logger.warning("Registration validation failed: %s", exc)
            return {"success": False, "error": str(exc)}
        except DuplicateKeyError:
            msg = f"The username '{username.strip()}' is already taken."
            logger.warning(msg)
            return {"success": False, "error": msg}
        except SDMSException as exc:
            logger.error("Registration failed: %s", exc)
            return {"success": False, "error": f"Registration failed: {exc}"}

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    def login(self, username: str, password: str) -> dict[str, Any]:
        """Authenticate a user and create a session.

        Args:
            username: The user's login name.
            password: The plaintext password.

        Returns:
            A dict::

                {
                    "success": True,
                    "user_id": "...",
                    "username": "...",
                    "role": "...",
                    "message": "Login successful."
                }
        """
        try:
            result = self._auth_service.login(
                username=username.strip(), password=password
            )
            self._audit_service.log_event(
                action=AuditAction.USER_LOGIN.value,
                resource_type=ResourceType.SESSION.value,
                resource_id=result["user_id"],
                resource_name=result["username"],
                status=OperationStatus.SUCCESS.value,
                message=f"User '{result['username']}' logged in successfully.",
                severity=SeverityLevel.INFO.value,
            )
            return {
                "success": True,
                **result,
                "message": (
                    f"Welcome back, {result['username']}!"
                ),
            }
        except ValidationError as exc:
            logger.warning("Login validation failed: %s", exc)
            self._audit_service.log_event(
                action=AuditAction.USER_LOGIN_FAILED.value,
                resource_type=ResourceType.SESSION.value,
                resource_id="",
                resource_name=username.strip(),
                status=OperationStatus.FAILURE.value,
                message=f"Login validation failed for '{username.strip()}': {exc}",
                severity=SeverityLevel.WARNING.value,
            )
            return {"success": False, "error": str(exc)}
        except AuthenticationError as exc:
            logger.warning("Authentication failed: %s", exc)
            self._audit_service.log_event(
                action=AuditAction.USER_LOGIN_FAILED.value,
                resource_type=ResourceType.SESSION.value,
                resource_id="",
                resource_name=username.strip(),
                status=OperationStatus.FAILURE.value,
                message=f"Authentication failed for '{username.strip()}': {exc}",
                severity=SeverityLevel.WARNING.value,
            )
            return {"success": False, "error": str(exc)}
        except SDMSException as exc:
            logger.error("Login failed due to system error: %s", exc)
            return {
                "success": False,
                "error": "A system error occurred. Please try again.",
            }

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    def logout(self) -> dict[str, Any]:
        """Terminate the current session.

        Returns:
            A dict indicating the result.
        """
        try:
            session = self._auth_service.get_current_user()
            result = self._auth_service.logout()
            if result.get("success") and session:
                self._audit_service.log_event(
                    action=AuditAction.USER_LOGOUT.value,
                    resource_type=ResourceType.SESSION.value,
                    resource_id=session.get("user_id", ""),
                    resource_name=session.get("username", ""),
                    status=OperationStatus.SUCCESS.value,
                    message=f"User '{session.get('username', '')}' logged out.",
                    severity=SeverityLevel.INFO.value,
                )
            return result
        except SDMSException as exc:
            logger.error("Logout failed: %s", exc)
            return {"success": False, "error": f"Logout failed: {exc}"}

    # ------------------------------------------------------------------
    # Session queries
    # ------------------------------------------------------------------

    def is_authenticated(self) -> bool:
        """Check whether a session is active."""
        return self._auth_service.is_authenticated()

    def get_current_user(self) -> dict[str, Any] | None:
        """Return current session info (without RSA keys)."""
        return self._auth_service.get_current_user()
