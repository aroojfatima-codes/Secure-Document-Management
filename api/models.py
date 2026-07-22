"""Pydantic models for all API request/response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared sub-models
# ---------------------------------------------------------------------------

class UserSummary(BaseModel):
    user_id: str
    username: str
    role: str


# ---------------------------------------------------------------------------
# Auth schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=8)
    role: str = Field(default="viewer", pattern=r"^(admin|editor|viewer)$")


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    success: bool = True
    access_token: str
    token_type: str = "bearer"
    user: UserSummary


class MessageResponse(BaseModel):
    success: bool = True
    message: str


# ---------------------------------------------------------------------------
# Document schemas
# ---------------------------------------------------------------------------

class DocumentInfo(BaseModel):
    document_id: str
    original_filename: str
    file_extension: str = ""
    mime_type: str = "application/octet-stream"
    file_size: int = 0
    file_size_display: str = ""
    sha256_hash: str = ""
    owner_id: str
    is_deleted: bool = False
    status: str = "active"
    created_at: str = ""
    updated_at: str = ""
    shared_with_count: int = 0


class PaginationMeta(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool


class DocumentListResponse(BaseModel):
    success: bool = True
    documents: list[DocumentInfo]
    pagination: PaginationMeta


class UploadResponse(BaseModel):
    success: bool = True
    document_id: str
    original_filename: str
    file_size: int
    sha256_hash: str
    message: str


class ShareRequest(BaseModel):
    recipient_username: str = Field(..., min_length=1)


class RevokeShareRequest(BaseModel):
    recipient_user_id: str = Field(..., min_length=1)


class ShareResponse(BaseModel):
    success: bool = True
    document_id: str
    recipient_user_id: str
    recipient_username: str
    permission: str
    message: str


class DocumentDetailResponse(BaseModel):
    success: bool = True
    document: DocumentInfo


# ---------------------------------------------------------------------------
# User schemas
# ---------------------------------------------------------------------------

class UserResponse(BaseModel):
    user_id: str
    username: str
    role: str
    is_active: bool
    face_enrolled: bool = False
    created_at: str = ""
    updated_at: str = ""


class UserListResponse(BaseModel):
    success: bool = True
    users: list[UserResponse]
    total: int


class UpdateRoleRequest(BaseModel):
    role: str = Field(..., pattern=r"^(admin|editor|viewer)$")


class UpdateUserRequest(BaseModel):
    username: str | None = None
    role: str | None = Field(default=None, pattern=r"^(admin|editor|viewer)$")
    is_active: bool | None = None


# ---------------------------------------------------------------------------
# Audit log schemas
# ---------------------------------------------------------------------------

class AuditLogEntry(BaseModel):
    audit_id: str
    timestamp: str = ""
    user_id: str
    username: str
    role: str
    action: str
    resource_type: str
    resource_id: str
    resource_name: str
    status: str
    message: str
    severity: str
    session_id: str = ""
    client_ip: str = ""
    device_info: str = ""
    metadata: dict[str, Any] = {}
    created_at: str = ""


class AuditLogListResponse(BaseModel):
    success: bool = True
    logs: list[AuditLogEntry]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_previous: bool


# ---------------------------------------------------------------------------
# Dashboard stats schemas
# ---------------------------------------------------------------------------

class DashboardStatsResponse(BaseModel):
    success: bool = True
    total_users: int = 0
    active_users: int = 0
    total_documents: int = 0
    total_storage_bytes: int = 0
    total_storage_display: str = ""
    documents_today: int = 0
    logins_today: int = 0
    recent_logs: list[AuditLogEntry] = []
