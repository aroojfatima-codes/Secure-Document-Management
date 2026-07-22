"""Audit controller -- handles audit log viewing and searching.

RBAC enforcement: only admin users may query audit logs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from exceptions.custom_exceptions import (
    AuthenticationError,
    AuthorizationError,
    SDMSException,
)
from logger.logging_config import get_logger
from models.audit import AuditAction, OperationStatus, ResourceType, SeverityLevel
from services.audit_service import AuditService
from services.session_manager import SessionManager
from utilities.permissions import Permission

logger = get_logger(__name__)


class AuditController:
    """Coordinates audit log viewing workflows.

    Usage::

        ctrl = AuditController()
        result = ctrl.view_audit_logs(action="USER_LOGIN")
    """

    def __init__(self) -> None:
        self._audit_service: AuditService = AuditService()
        self._session_mgr: SessionManager = SessionManager()

    @staticmethod
    def _parse_date(date_str: str | None) -> tuple[datetime | None, str | None]:
        """Parse an ISO date string, returning (datetime, error_message)."""
        if not date_str:
            return None, None
        try:
            dt = datetime.fromisoformat(date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt, None
        except ValueError:
            return None, f"Invalid date format '{date_str}'. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS."

    def view_audit_logs(
        self,
        username: str | None = None,
        action: str | None = None,
        severity: str | None = None,
        resource_type: str | None = None,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """Query audit logs with optional filters and pagination.

        RBAC: Requires ``view_audit_logs`` permission (admin only).
        """
        try:
            self._session_mgr.require_permission(Permission.VIEW_AUDIT_LOGS)
            parsed_from, err = self._parse_date(date_from)
            if err:
                return {"success": False, "error": err}

            parsed_to, err = self._parse_date(date_to)
            if err:
                return {"success": False, "error": err}

            result = self._audit_service.query_logs(
                username=username, action=action, severity=severity,
                resource_type=resource_type, status=status,
                date_from=parsed_from, date_to=parsed_to,
                page=page, per_page=per_page,
            )

            if result.get("success"):
                self._audit_service.log_event(
                    action=AuditAction.AUDIT_LOG_VIEW.value,
                    resource_type=ResourceType.AUDIT_LOG.value,
                    status=OperationStatus.SUCCESS.value,
                    message="Administrator viewed audit logs.",
                    severity=SeverityLevel.INFO.value,
                )

            return result

        except AuthenticationError as exc:
            logger.warning("Audit log view denied -- not authenticated.")
            return {"success": False, "error": str(exc)}
        except AuthorizationError as exc:
            logger.warning("Audit log view denied -- insufficient permissions: %s", exc)
            return {"success": False, "error": str(exc)}
        except SDMSException as exc:
            logger.error("Audit log view failed: %s", exc)
            return {"success": False, "error": f"Audit log view failed: {exc}"}
