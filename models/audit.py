from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from exceptions.custom_exceptions import ValidationError
from models.base import BaseModel


class AuditAction(Enum):
    USER_REGISTRATION = "USER_REGISTRATION"
    USER_LOGIN = "USER_LOGIN"
    USER_LOGIN_FAILED = "USER_LOGIN_FAILED"
    USER_LOGOUT = "USER_LOGOUT"
    DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD"
    DOCUMENT_DOWNLOAD = "DOCUMENT_DOWNLOAD"
    DOCUMENT_SHARE = "DOCUMENT_SHARE"
    DOCUMENT_ACCESS_REQUEST = "DOCUMENT_ACCESS_REQUEST"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    AUDIT_LOG_VIEW = "AUDIT_LOG_VIEW"
    AUDIT_LOG_SEARCH = "AUDIT_LOG_SEARCH"
    FACE_ENROLLMENT = "FACE_ENROLLMENT"
    FACE_ENROLLMENT_FAILED = "FACE_ENROLLMENT_FAILED"
    FACE_LOGIN = "FACE_LOGIN"
    FACE_LOGIN_FAILED = "FACE_LOGIN_FAILED"
    FACE_ENROLLMENT_REMOVED = "FACE_ENROLLMENT_REMOVED"


class SeverityLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    SECURITY_ALERT = "SECURITY_ALERT"
    CRITICAL = "CRITICAL"


class ResourceType(Enum):
    USER = "USER"
    DOCUMENT = "DOCUMENT"
    SESSION = "SESSION"
    SHARING = "SHARING"
    SYSTEM = "SYSTEM"
    AUDIT_LOG = "AUDIT_LOG"


class OperationStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    DENIED = "DENIED"
    ERROR = "ERROR"


@dataclass
class AuditLog(BaseModel):
    audit_id: str = ""
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    user_id: str = ""
    username: str = ""
    role: str = ""
    action: str = ""
    resource_type: str = ""
    resource_id: str = ""
    resource_name: str = ""
    status: str = ""
    message: str = ""
    severity: str = SeverityLevel.INFO.value
    session_id: str = ""
    client_ip: str = ""
    device_info: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = self.timestamp

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "status": self.status,
            "message": self.message,
            "severity": self.severity,
            "session_id": self.session_id,
            "client_ip": self.client_ip,
            "device_info": self.device_info,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    def validate(self) -> None:
        errors: list[str] = []

        if not self.audit_id:
            errors.append("audit_id is required.")
        if not self.action:
            errors.append("action is required.")
        if not self.resource_type:
            errors.append("resource_type is required.")
        if not self.status:
            errors.append("status is required.")
        if self.severity not in {s.value for s in SeverityLevel}:
            errors.append(
                f"Invalid severity '{self.severity}'. "
                f"Must be one of {[s.value for s in SeverityLevel]}."
            )

        if errors:
            raise ValidationError("; ".join(errors))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditLog:
        return cls(
            audit_id=data.get("audit_id", ""),
            timestamp=data.get("timestamp", datetime.now(timezone.utc)),
            user_id=data.get("user_id", ""),
            username=data.get("username", ""),
            role=data.get("role", ""),
            action=data.get("action", ""),
            resource_type=data.get("resource_type", ""),
            resource_id=data.get("resource_id", ""),
            resource_name=data.get("resource_name", ""),
            status=data.get("status", ""),
            message=data.get("message", ""),
            severity=data.get("severity", SeverityLevel.INFO.value),
            session_id=data.get("session_id", ""),
            client_ip=data.get("client_ip", ""),
            device_info=data.get("device_info", ""),
            metadata=data.get("metadata", {}),
            created_at=data.get(
                "created_at",
                data.get("timestamp", datetime.now(timezone.utc)),
            ),
        )
