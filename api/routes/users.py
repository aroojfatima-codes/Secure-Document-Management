"""User management API routes: list, get, update, delete, change role."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.deps import get_current_user
from api.models import (
    UpdateRoleRequest,
    UpdateUserRequest,
    UserListResponse,
    UserResponse,
)
from database.exceptions import UserNotFoundError
from database.repositories.user_repository import UserRepository
from exceptions.custom_exceptions import (
    DatabaseError,
    ValidationError,
)
from logger.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

_user_repo = UserRepository()


def _require_admin(current_user: dict[str, Any]) -> None:
    """Raise 403 if the current user is not an admin."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )


def _safe_user_dict(user: Any) -> dict[str, Any]:
    """Extract safe fields from a User model instance."""
    return {
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active,
        "face_enrolled": getattr(user, "face_enrolled", False),
        "created_at": user.created_at.isoformat() if user.created_at else "",
        "updated_at": user.updated_at.isoformat() if user.updated_at else "",
    }


# ------------------------------------------------------------------
# List users
# ------------------------------------------------------------------

@router.get("", response_model=UserListResponse)
def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """List all users (admin only)."""
    _require_admin(current_user)
    try:
        skip = (page - 1) * per_page
        users = _user_repo.get_all_users(skip=skip, limit=per_page)
        total = _user_repo.count({})
        return {
            "success": True,
            "users": [_safe_user_dict(u) for u in users],
            "total": total,
        }
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


# ------------------------------------------------------------------
# Get single user
# ------------------------------------------------------------------

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Get a user by ID. Users can view themselves; admins can view anyone."""
    if current_user["user_id"] != user_id and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile.",
        )
    try:
        user = _user_repo.get_by_user_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User '{user_id}' not found.")
        return _safe_user_dict(user)
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


# ------------------------------------------------------------------
# Update user
# ------------------------------------------------------------------

@router.put("/{user_id}")
def update_user(
    user_id: str,
    body: UpdateUserRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Update user fields. Users can update themselves; admins can update anyone."""
    if current_user["user_id"] != user_id and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile.",
        )
    try:
        updates: dict[str, Any] = {}
        if body.username is not None:
            updates["username"] = body.username.strip()
        if body.role is not None and current_user["role"] == "admin":
            updates["role"] = body.role
        if body.is_active is not None and current_user["role"] == "admin":
            updates["is_active"] = body.is_active

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update.",
            )

        user = _user_repo.update_user(user_id, updates)
        return _safe_user_dict(user)
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


# ------------------------------------------------------------------
# Delete user
# ------------------------------------------------------------------

@router.delete("/{user_id}")
def delete_user(
    user_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Permanently delete a user (admin only)."""
    _require_admin(current_user)
    try:
        _user_repo.delete_user(user_id)
        return {"success": True, "message": f"User '{user_id}' deleted."}
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


# ------------------------------------------------------------------
# Change role
# ------------------------------------------------------------------

@router.put("/{user_id}/role")
def change_role(
    user_id: str,
    body: UpdateRoleRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Change a user's role (admin only)."""
    _require_admin(current_user)
    try:
        user = _user_repo.update_user(user_id, {"role": body.role})
        return {
            "success": True,
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role,
            "message": f"Role updated to '{body.role}' for user '{user.username}'.",
        }
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
