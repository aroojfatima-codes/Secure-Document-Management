"""Audit log API routes: query and view audit logs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_current_user
from api.models import AuditLogListResponse
from exceptions.custom_exceptions import SDMSException
from logger.logging_config import get_logger
from models.audit import (
    AuditAction,
    OperationStatus,
    ResourceType,
    SeverityLevel,
)
from services.audit_service import AuditService

logger = get_logger(__name__)

router = APIRouter(prefix="/audit-logs", tags=["audit"])

_audit_svc = AuditService()


@router.get("", response_model=AuditLogListResponse)
def get_audit_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    username: str | None = Query(None),
    action: str | None = Query(None),
    severity: str | None = Query(None),
    resource_type: str | None = Query(None),
    status: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Query audit logs with optional filters (admin only)."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Audit log access requires admin role.",
        )

    try:
        parsed_from, err = _parse_date(date_from)
        if err:
            raise HTTPException(status_code=400, detail=err)
        parsed_to, err = _parse_date(date_to)
        if err:
            raise HTTPException(status_code=400, detail=err)

        result = _audit_svc.query_logs(
            username=username,
            action=action,
            severity=severity,
            resource_type=resource_type,
            status=status,
            date_from=parsed_from,
            date_to=parsed_to,
            page=page,
            per_page=per_page,
        )

        if result.get("success"):
            _audit_svc.log_event(
                action=AuditAction.AUDIT_LOG_VIEW.value,
                resource_type=ResourceType.AUDIT_LOG.value,
                status=OperationStatus.SUCCESS.value,
                message="Audit logs viewed via API.",
                severity=SeverityLevel.INFO.value,
            )

        return {
            "success": result.get("success", True),
            "logs": [_serialize_log(entry) for entry in result.get("logs", [])],
            "total": result.get("total", 0),
            "page": result.get("page", page),
            "per_page": result.get("per_page", per_page),
            "total_pages": result.get("total_pages", 0),
            "has_next": result.get("has_next", False),
            "has_previous": result.get("has_previous", False),
        }
    except HTTPException:
        raise
    except SDMSException as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

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


def _serialize_log(log: Any) -> dict[str, Any]:
    """Convert an AuditLog model or dict to a serializable dict."""
    if hasattr(log, "to_dict"):
        raw = log.to_dict()
    elif isinstance(log, dict):
        raw = log
    else:
        raw = {}

    def _to_iso(val: Any) -> str:
        if isinstance(val, datetime):
            return val.isoformat()
        if hasattr(val, "isoformat"):
            return val.isoformat()
        return str(val) if val else ""

    return {
        "audit_id": raw.get("audit_id", ""),
        "timestamp": _to_iso(raw.get("timestamp")),
        "user_id": raw.get("user_id", ""),
        "username": raw.get("username", ""),
        "role": raw.get("role", ""),
        "action": raw.get("action", ""),
        "resource_type": raw.get("resource_type", ""),
        "resource_id": raw.get("resource_id", ""),
        "resource_name": raw.get("resource_name", ""),
        "status": raw.get("status", ""),
        "message": raw.get("message", ""),
        "severity": raw.get("severity", ""),
        "session_id": raw.get("session_id", ""),
        "client_ip": raw.get("client_ip", ""),
        "device_info": raw.get("device_info", ""),
        "metadata": raw.get("metadata", {}),
        "created_at": _to_iso(raw.get("created_at")),
    }
