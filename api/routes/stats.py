"""Dashboard stats API route: aggregated statistics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_current_user
from api.models import DashboardStatsResponse
from database.manager import DatabaseManager
from exceptions.custom_exceptions import DatabaseError
from logger.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/stats", tags=["stats"])

_db_mgr = DatabaseManager()


def _format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    size: float = float(size_bytes)
    for unit in ("KB", "MB", "GB"):
        size /= 1024.0
        if size < 1024:
            return f"{size:.1f} {unit}"
    return f"{size:.1f} TB"


@router.get("/dashboard", response_model=DashboardStatsResponse)
def dashboard_stats(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Return aggregated dashboard statistics."""
    try:
        users_col = _db_mgr.get_collection("users")
        docs_col = _db_mgr.get_collection("documents")
        logs_col = _db_mgr.get_collection("audit_logs")

        total_users = users_col.count_documents({})
        active_users = users_col.count_documents({"is_active": True})

        total_documents = docs_col.count_documents({"is_deleted": False})

        pipeline = [
            {"$match": {"is_deleted": False}},
            {"$group": {"_id": None, "total": {"$sum": "$file_size"}}},
        ]
        storage_result = list(docs_col.aggregate(pipeline))
        total_storage = (
            storage_result[0]["total"] if storage_result else 0
        )

        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        documents_today = docs_col.count_documents(
            {"created_at": {"$gte": today_start}}
        )

        logins_today = logs_col.count_documents(
            {
                "action": "USER_LOGIN",
                "timestamp": {"$gte": today_start},
            }
        )

        recent_cursor = (
            logs_col.find()
            .sort("timestamp", -1)
            .limit(10)
        )
        recent_logs = []
        for log in recent_cursor:
            recent_logs.append({
                "audit_id": log.get("audit_id", ""),
                "timestamp": (
                    log["timestamp"].isoformat()
                    if hasattr(log.get("timestamp"), "isoformat")
                    else str(log.get("timestamp", ""))
                ),
                "user_id": log.get("user_id", ""),
                "username": log.get("username", ""),
                "role": log.get("role", ""),
                "action": log.get("action", ""),
                "resource_type": log.get("resource_type", ""),
                "resource_id": log.get("resource_id", ""),
                "resource_name": log.get("resource_name", ""),
                "status": log.get("status", ""),
                "message": log.get("message", ""),
                "severity": log.get("severity", ""),
                "session_id": log.get("session_id", ""),
                "client_ip": log.get("client_ip", ""),
                "device_info": log.get("device_info", ""),
                "metadata": log.get("metadata", {}),
                "created_at": (
                    log["created_at"].isoformat()
                    if hasattr(log.get("created_at"), "isoformat")
                    else str(log.get("created_at", ""))
                ),
            })

        return {
            "success": True,
            "total_users": total_users,
            "active_users": active_users,
            "total_documents": total_documents,
            "total_storage_bytes": total_storage,
            "total_storage_display": _format_file_size(total_storage),
            "documents_today": documents_today,
            "logins_today": logins_today,
            "recent_logs": recent_logs,
        }
    except DatabaseError as exc:
        logger.error("Dashboard stats query failed: %s", exc)
        raise HTTPException(
            status_code=500, detail="Failed to load dashboard statistics."
        ) from exc
    except Exception as exc:
        logger.error("Unexpected dashboard stats error: %s", exc)
        raise HTTPException(
            status_code=500, detail="Internal error loading statistics."
        ) from exc
