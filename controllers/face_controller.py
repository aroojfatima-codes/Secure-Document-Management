"""Face recognition controller -- handles face enrollment, login,
and enrollment removal.

This is the thin presentation-coordination layer for biometric
authentication workflows.
"""

from __future__ import annotations

from typing import Any

from exceptions.custom_exceptions import (
    AuthenticationError,
    AuthorizationError,
    SDMSException,
)
from logger.logging_config import get_logger
from models.audit import AuditAction, OperationStatus, ResourceType, SeverityLevel
from services.audit_service import AuditService
from services.face_recognition_service import FaceRecognitionService
from services.session_manager import SessionManager

logger = get_logger(__name__)


class FaceController:
    """Coordinates face-recognition workflows.

    Usage::

        ctrl = FaceController()
        ctrl.enroll("user_id", "alice")
        ctrl.login_face()
    """

    def __init__(self) -> None:
        self._face_service: FaceRecognitionService = FaceRecognitionService()
        self._audit_service: AuditService = AuditService()
        self._session_mgr: SessionManager = SessionManager()

    def is_available(self) -> bool:
        """Check whether face recognition is available."""
        return self._face_service.is_available()

    def enroll(self, user_id: str, username: str) -> dict[str, Any]:
        """Enroll a user's face for biometric login."""
        try:
            session = self._session_mgr.get_current_session()
            if session.user_id != user_id and session.role != "admin":
                raise AuthorizationError("You can only enroll your own face.")

            result = self._face_service.enroll_face(user_id, username)

            if result.get("success"):
                self._audit_service.log_event(
                    action=AuditAction.FACE_ENROLLMENT.value,
                    resource_type=ResourceType.USER.value,
                    resource_id=user_id,
                    resource_name=username,
                    status=OperationStatus.SUCCESS.value,
                    message=f"Face enrollment completed for user '{username}'.",
                    severity=SeverityLevel.INFO.value,
                    metadata={"samples": result.get("samples_captured", 0)},
                )
            else:
                self._audit_service.log_event(
                    action=AuditAction.FACE_ENROLLMENT_FAILED.value,
                    resource_type=ResourceType.USER.value,
                    resource_id=user_id,
                    resource_name=username,
                    status=OperationStatus.FAILURE.value,
                    message=f"Face enrollment failed for user '{username}': {result.get('error', '')}",
                    severity=SeverityLevel.WARNING.value,
                )

            return result

        except AuthenticationError as exc:
            logger.warning("Face enrollment denied -- not authenticated.")
            return {"success": False, "error": str(exc)}
        except SDMSException as exc:
            logger.error("Face enrollment failed: %s", exc)
            return {"success": False, "error": str(exc)}

    def login_face(self) -> dict[str, Any]:
        """Authenticate a user via face recognition."""
        try:
            result = self._face_service.recognize_user()

            if result.get("success"):
                self._audit_service.log_event(
                    action=AuditAction.FACE_LOGIN.value,
                    resource_type=ResourceType.SESSION.value,
                    resource_id=result["user_id"],
                    resource_name=result["username"],
                    status=OperationStatus.SUCCESS.value,
                    message=f"User '{result['username']}' logged in via face recognition.",
                    severity=SeverityLevel.INFO.value,
                    metadata={"match_distance": result.get("distance")},
                )
            else:
                self._audit_service.log_event(
                    action=AuditAction.FACE_LOGIN_FAILED.value,
                    resource_type=ResourceType.SESSION.value,
                    resource_id="",
                    resource_name="",
                    status=OperationStatus.FAILURE.value,
                    message=f"Face recognition login failed: {result.get('error', '')}",
                    severity=SeverityLevel.WARNING.value,
                )

            return result

        except SDMSException as exc:
            logger.error("Face login failed: %s", exc)
            return {"success": False, "error": str(exc)}

    def remove_enrollment(self, user_id: str, username: str) -> dict[str, Any]:
        """Remove a user's face enrollment."""
        try:
            session = self._session_mgr.get_current_session()
            if session.user_id != user_id and session.role != "admin":
                raise AuthorizationError("You can only remove your own face enrollment.")

            result = self._face_service.remove_enrollment(user_id)

            if result.get("success"):
                self._audit_service.log_event(
                    action=AuditAction.FACE_ENROLLMENT_REMOVED.value,
                    resource_type=ResourceType.USER.value,
                    resource_id=user_id,
                    resource_name=username,
                    status=OperationStatus.SUCCESS.value,
                    message=f"Face enrollment removed for user '{username}'.",
                    severity=SeverityLevel.INFO.value,
                )

            return result

        except AuthenticationError as exc:
            logger.warning("Remove enrollment denied -- not authenticated.")
            return {"success": False, "error": str(exc)}
        except AuthorizationError as exc:
            logger.warning("Remove enrollment denied -- insufficient permissions.")
            return {"success": False, "error": str(exc)}
        except SDMSException as exc:
            logger.error("Remove enrollment failed: %s", exc)
            return {"success": False, "error": str(exc)}

    def is_enrolled(self, user_id: str) -> bool:
        """Check whether a user has face enrollment data."""
        return self._face_service.is_enrolled(user_id)
