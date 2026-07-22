"""FastAPI dependencies: JWT authentication, database access, and
session bridging for the existing singleton-based service layer.

The ``get_current_user`` dependency extracts and verifies the JWT
token, then fetches the full user record from MongoDB (including
RSA keys).  The ``set_session_for_request`` helper temporarily
populates the singleton ``SessionManager`` so that existing services
work without modification.
"""

from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.auth import verify_token
from database.repositories.user_repository import UserRepository
from exceptions.custom_exceptions import DatabaseError
from logger.logging_config import get_logger
from models.user import User
from services.session_manager import SessionManager

logger = get_logger(__name__)

security = HTTPBearer()
_session_mgr = SessionManager()
_user_repo = UserRepository()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    """FastAPI dependency that validates the JWT and returns user info.

    Returns:
        A dict with user_id, username, role, and the full User object
        stored under ``_user`` for downstream RSA key access.

    Raises:
        HTTPException 401: If the token is missing, invalid, or the
            user no longer exists in the database.
    """
    token: str = credentials.credentials
    payload: dict[str, Any] | None = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("user_id", "")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing user_id.",
        )

    try:
        user: User | None = _user_repo.get_by_user_id(user_id)
    except DatabaseError as exc:
        logger.error("Database error during token validation: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database unavailable.",
        ) from exc

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated.",
        )

    return {
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role,
        "_user": user,
    }


def set_session(user: User) -> None:
    """Populate the singleton SessionManager with user data.

    This bridges the gap between stateless JWT auth and the existing
    singleton-based service layer.  Call ``clear_session()`` in a
    ``finally`` block after the service call completes.

    WARNING: This is NOT thread-safe.  Suitable for the academic
    demo; production would use contextvars.
    """
    _session_mgr.create_session(
        user_id=user.user_id,
        username=user.username,
        role=user.role,
        rsa_public_key=user.rsa_public_key,
        rsa_private_key=user.rsa_private_key,
    )


def clear_session() -> None:
    """Tear down the singleton session after a request completes."""
    _session_mgr.logout()
