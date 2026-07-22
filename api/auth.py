"""JWT token creation and verification utilities.

Uses PyJWT with HS256 algorithm. Tokens carry user_id, username,
and role in the payload. Secret key is loaded from environment or
falls back to a development default.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

JWT_SECRET: str = os.getenv("JWT_SECRET", "sdms-dev-secret-change-in-production")
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRY_HOURS: int = 24


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        data:           Payload claims (must include user_id, username, role).
        expires_delta:  Optional custom expiry duration.

    Returns:
        Encoded JWT string.
    """
    to_encode: dict[str, Any] = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=JWT_EXPIRY_HOURS)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict[str, Any] | None:
    """Decode and verify a JWT token.

    Args:
        token: The encoded JWT string.

    Returns:
        The decoded payload dict, or None if invalid/expired.
    """
    try:
        payload: dict[str, Any] = jwt.decode(
            token, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        if "user_id" not in payload:
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
