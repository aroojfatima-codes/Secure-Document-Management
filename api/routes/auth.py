"""Auth API routes: register, login, logout, current user."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import create_access_token
from api.deps import get_current_user
from api.models import (
    AuthResponse,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
)
from database.exceptions import DuplicateKeyError
from exceptions.custom_exceptions import (
    AuthenticationError,
    SDMSException,
    ValidationError,
)
from logger.logging_config import get_logger
from models.audit import (
    AuditAction,
    OperationStatus,
    ResourceType,
    SeverityLevel,
)
from services.audit_service import AuditService
from services.auth_service import AuthService
from services.registration_service import RegistrationService

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

_registration_svc = RegistrationService()
_auth_svc = AuthService()
_audit_svc = AuditService()


@router.post("/register", response_model=MessageResponse, status_code=201)
def register(body: RegisterRequest) -> dict[str, Any]:
    """Register a new user account."""
    if body.role.strip().lower() != "viewer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Self-registration is restricted to the 'viewer' role.",
        )
    try:
        result = _registration_svc.register(
            username=body.username.strip(),
            password=body.password,
            role=body.role.strip().lower(),
        )
        _audit_svc.log_event(
            action=AuditAction.USER_REGISTRATION.value,
            resource_type=ResourceType.USER.value,
            resource_id=result["user_id"],
            resource_name=result["username"],
            status=OperationStatus.SUCCESS.value,
            message=f"User '{result['username']}' registered via API.",
            severity=SeverityLevel.INFO.value,
        )
        return {
            "success": True,
            "message": f"User '{result['username']}' registered successfully.",
        }
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{body.username}' is already taken.",
        )
    except SDMSException as exc:
        logger.error("Registration failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed.",
        ) from exc


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest) -> dict[str, Any]:
    """Authenticate and return a JWT access token."""
    try:
        result: dict[str, Any] = _auth_svc.login(
            username=body.username.strip(), password=body.password
        )
        _audit_svc.log_event(
            action=AuditAction.USER_LOGIN.value,
            resource_type=ResourceType.SESSION.value,
            resource_id=result["user_id"],
            resource_name=result["username"],
            status=OperationStatus.SUCCESS.value,
            message=f"User '{result['username']}' logged in via API.",
            severity=SeverityLevel.INFO.value,
        )
        token: str = create_access_token(
            data={
                "user_id": result["user_id"],
                "username": result["username"],
                "role": result["role"],
            }
        )
        return {
            "success": True,
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "user_id": result["user_id"],
                "username": result["username"],
                "role": result["role"],
            },
        }
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except AuthenticationError as exc:
        _audit_svc.log_event(
            action=AuditAction.USER_LOGIN_FAILED.value,
            resource_type=ResourceType.SESSION.value,
            resource_id="",
            resource_name=body.username.strip(),
            status=OperationStatus.FAILURE.value,
            message=f"Login failed for '{body.username.strip()}'.",
            severity=SeverityLevel.WARNING.value,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        )
    except SDMSException as exc:
        logger.error("Login failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to a system error.",
        ) from exc


@router.post("/logout", response_model=MessageResponse)
def logout(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Terminate the current session (invalidate token client-side).

    The JWT itself remains valid until expiry. For a production
    system you would maintain a token blocklist.
    """
    _audit_svc.log_event(
        action=AuditAction.USER_LOGOUT.value,
        resource_type=ResourceType.SESSION.value,
        resource_id=current_user["user_id"],
        resource_name=current_user["username"],
        status=OperationStatus.SUCCESS.value,
        message=f"User '{current_user['username']}' logged out via API.",
        severity=SeverityLevel.INFO.value,
    )
    return {
        "success": True,
        "message": f"User '{current_user['username']}' logged out.",
    }


@router.get("/me")
def me(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Return the currently authenticated user's profile."""
    return {
        "success": True,
        "user": {
            "user_id": current_user["user_id"],
            "username": current_user["username"],
            "role": current_user["role"],
        },
    }
