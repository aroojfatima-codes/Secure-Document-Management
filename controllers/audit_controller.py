from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from exceptions.custom_exceptions import AuthenticationError
from logger.logging_config import get_logger
from models.audit import AuditAction, OperationStatus, ResourceType, SeverityLevel
from services.audit_service import AuditService

logger = get_logger(__name__)


class AuditController:
    def __init__(self) -> None:
        self._audit_service: AuditService = AuditService()

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
        try:
            parsed_date_from: datetime | None = None
            parsed_date_to: datetime | None = None

            if date_from:
                try:
                    parsed_date_from = datetime.fromisoformat(date_from)
                    if parsed_date_from.tzinfo is None:
                        parsed_date_from = parsed_date_from.replace(tzinfo=timezone.utc)
                except ValueError:
                    return {
                        "success": False,
                        "error": "Invalid date_from format. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS.",
                    }

            if date_to:
                try:
                    parsed_date_to = datetime.fromisoformat(date_to)
                    if parsed_date_to.tzinfo is None:
                        parsed_date_to = parsed_date_to.replace(tzinfo=timezone.utc)
                except ValueError:
                    return {
                        "success": False,
                        "error": "Invalid date_to format. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS.",
                    }

            result = self._audit_service.query_logs(
                username=username,
                action=action,
                severity=severity,
                resource_type=resource_type,
                status=status,
                date_from=parsed_date_from,
                date_to=parsed_date_to,
                page=page,
                per_page=per_page,
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
            logger.warning("Audit log view denied — not authenticated.")
            return {"success": False, "error": str(exc)}
        except Exception as exc:
            logger.error("Audit log view failed: %s", exc)
            return {"success": False, "error": f"Audit log view failed: {exc}"}
