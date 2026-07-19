from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from crypto.key_generator import generate_crypto_id
from database.repositories.audit_repository import AuditRepository
from logger.logging_config import get_logger
from models.audit import (
    AuditLog,
    OperationStatus,
    SeverityLevel,
)
from services.session_manager import SessionManager

logger = get_logger(__name__)


class AuditService:
    """Provides audit event logging and log querying.

    Usage::

        svc = AuditService()
        svc.log_event("USER_LOGIN", "SESSION", status="SUCCESS")
        results = svc.query_logs(action="USER_LOGIN", page=1)
    """

    def __init__(self) -> None:
        self._audit_repo: AuditRepository = AuditRepository()
        self._session_mgr: SessionManager = SessionManager()

    def log_event(
        self,
        action: str,
        resource_type: str,
        resource_id: str = "",
        resource_name: str = "",
        status: str = OperationStatus.SUCCESS.value,
        message: str = "",
        severity: str = SeverityLevel.INFO.value,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Persist an audit log entry. Returns True on success."""
        try:
            audit_id: str = generate_crypto_id()
            now: datetime = datetime.now(timezone.utc)
            user_id, username, role, session_id = self._get_session_context()

            audit_log = AuditLog(
                audit_id=audit_id,
                timestamp=now,
                user_id=user_id,
                username=username,
                role=role,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name,
                status=status,
                message=message,
                severity=severity,
                session_id=session_id or audit_id,
                client_ip="",
                device_info="",
                metadata=metadata or {},
                created_at=now,
            )

            self._audit_repo.create_audit_log(audit_log)
            logger.debug(
                "Audit log created: action=%s, resource_type=%s, "
                "resource_id=%s, status=%s, severity=%s",
                action, resource_type, resource_id, status, severity,
            )
            return True

        except Exception as exc:
            logger.exception(
                "Failed to write audit log (action=%s, resource_type=%s): %s",
                action, resource_type, exc,
            )
            return False

    def query_logs(
        self,
        username: str | None = None,
        action: str | None = None,
        severity: str | None = None,
        resource_type: str | None = None,
        status: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        user_id: str | None = None,
        resource_id: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """Query audit logs with filtering and pagination."""
        try:
            skip: int = (page - 1) * per_page
            logs = self._audit_repo.find_logs(
                username=username, action=action, severity=severity,
                resource_type=resource_type, status=status,
                date_from=date_from, date_to=date_to,
                user_id=user_id, resource_id=resource_id,
                skip=skip, limit=per_page,
            )
            total: int = self._audit_repo.count_logs(
                username=username, action=action, severity=severity,
                resource_type=resource_type, status=status,
                date_from=date_from, date_to=date_to,
                user_id=user_id, resource_id=resource_id,
            )
            total_pages: int = max(1, (total + per_page - 1) // per_page)

            return {
                "success": True,
                "logs": [log.to_dict() for log in logs],
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            }
        except Exception as exc:
            logger.exception("Failed to query audit logs: %s", exc)
            return {
                "success": False,
                "error": f"Failed to query audit logs: {exc}",
                "logs": [],
                "total": 0,
                "page": page,
                "per_page": per_page,
                "total_pages": 0,
                "has_next": False,
                "has_previous": False,
            }

    def _get_session_context(self) -> tuple[str, str, str, str]:
        """Extract user context from the current session."""
        try:
            if self._session_mgr.is_authenticated:
                session = self._session_mgr.get_current_session()
                return (
                    session.user_id,
                    session.username,
                    session.role,
                    getattr(session, "session_id", ""),
                )
        except Exception:
            logger.debug("Could not enrich audit event with session data.", exc_info=True)
        return "", "", "", ""
