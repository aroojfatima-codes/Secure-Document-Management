from __future__ import annotations

from datetime import datetime
from typing import Any

import pymongo

from database.repositories.base import BaseRepository
from exceptions.custom_exceptions import ValidationError
from logger.logging_config import get_logger
from models.audit import AuditLog

logger = get_logger(__name__)


class AuditRepository(BaseRepository):
    """CRUD operations for the ``audit_logs`` collection."""

    _collection_name: str = "audit_logs"
    _id_field: str = "audit_id"

    def create_audit_log(self, audit_log: AuditLog) -> str:
        """Persist a validated audit log entry."""
        audit_log.validate()
        if not audit_log.audit_id:
            raise ValidationError(
                "audit_id must be set before calling create_audit_log."
            )
        return self.create(audit_log.to_dict())

    def get_by_audit_id(self, audit_id: str) -> AuditLog | None:
        """Retrieve a single audit log by its ID."""
        doc = self.get_by_id(audit_id)
        return AuditLog.from_dict(doc) if doc else None

    # ------------------------------------------------------------------
    # Internal filter builder (DRY for find_logs / count_logs)
    # ------------------------------------------------------------------

    @staticmethod
    def _build_filters(
        username: str | None = None,
        action: str | None = None,
        severity: str | None = None,
        resource_type: str | None = None,
        status: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        user_id: str | None = None,
        resource_id: str | None = None,
    ) -> dict[str, Any]:
        """Build a MongoDB filter dict from optional query parameters."""
        filters: dict[str, Any] = {}
        if username:
            filters["username"] = {"$regex": username, "$options": "i"}
        if action:
            filters["action"] = action
        if severity:
            filters["severity"] = severity
        if resource_type:
            filters["resource_type"] = resource_type
        if status:
            filters["status"] = status
        if user_id:
            filters["user_id"] = user_id
        if resource_id:
            filters["resource_id"] = resource_id
        if date_from or date_to:
            time_filter: dict[str, Any] = {}
            if date_from:
                time_filter["$gte"] = date_from
            if date_to:
                time_filter["$lte"] = date_to
            if time_filter:
                filters["timestamp"] = time_filter
        return filters

    def find_logs(
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
        skip: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        """Search audit logs with optional filters and pagination."""
        filters = self._build_filters(
            username=username, action=action, severity=severity,
            resource_type=resource_type, status=status,
            date_from=date_from, date_to=date_to,
            user_id=user_id, resource_id=resource_id,
        )
        docs = self.find(
            filters=filters, skip=skip, limit=limit,
            sort=[("timestamp", pymongo.DESCENDING)],
        )
        return [AuditLog.from_dict(d) for d in docs]

    def count_logs(
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
    ) -> int:
        """Count audit logs matching the given filters."""
        filters = self._build_filters(
            username=username, action=action, severity=severity,
            resource_type=resource_type, status=status,
            date_from=date_from, date_to=date_to,
            user_id=user_id, resource_id=resource_id,
        )
        return self.count(filters=filters)

    def get_logs_by_user(
        self, user_id: str, skip: int = 0, limit: int = 50,
    ) -> list[AuditLog]:
        """Retrieve logs for a specific user."""
        return self.find_logs(user_id=user_id, skip=skip, limit=limit)

    def get_logs_by_action(
        self, action: str, skip: int = 0, limit: int = 50,
    ) -> list[AuditLog]:
        """Retrieve logs for a specific action type."""
        return self.find_logs(action=action, skip=skip, limit=limit)

    def get_logs_by_date_range(
        self, date_from: datetime, date_to: datetime,
        skip: int = 0, limit: int = 50,
    ) -> list[AuditLog]:
        """Retrieve logs within a date range."""
        return self.find_logs(
            date_from=date_from, date_to=date_to, skip=skip, limit=limit,
        )

    def get_logs_by_severity(
        self, severity: str, skip: int = 0, limit: int = 50,
    ) -> list[AuditLog]:
        """Retrieve logs at a specific severity level."""
        return self.find_logs(severity=severity, skip=skip, limit=limit)
