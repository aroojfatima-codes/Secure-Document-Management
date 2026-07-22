"""Time-based One-Time Password (TOTP) utilities.

Implements standard RFC 6238 TOTP for two-factor authentication.
Uses HMAC-SHA256 and a time-based counter moving in 30-second windows.

Security note: The TOTP secret must be generated using a cryptographically
secure random source and stored securely. For production environments, consider
aiding users with backup codes and recovery options.
"""

from __future__ import annotations

import base64
import hmac
import time

from logger.logging_config import get_logger

logger = get_logger(__name__)
# --------------------------------------------------------------------------
# Internal math helpers
# --------------------------------------------------------------------------


def _generate_counter() -> int:
    """Get the current 30-second time window counter (UTC)."""
    return int(time.time() // 30)


def _hmac_sha256(key: bytes, msg: bytes) -> bytes:
    """Return HMAC-SHA256 of *msg* using *key*."""
    return hmac.new(key, msg, "sha256").digest()


def _dynamic_truncate(hmac_digest: bytes) -> int:
    """Extract a 31-bit integer from the HMAC using dynamic truncation.

    Per RFC 6238 section 5.2, we:
    1. Choose offset in [0, 15] as the lowest 4 bits of the HMAC
    2. Extract 4 bytes (little-endian) starting at that offset
    3. Mask with 0x7fffffff to get a positive 31-bit integer.
    """
    offset = hmac_digest[-1] & 0x0F
    value_bytes = hmac_digest[offset : offset + 4]
    code = int.from_bytes(value_bytes, byteorder="little") & 0x7FFFFFFF
    return code


def _generate_hotp(key: bytes, counter: int) -> int:
    """Generate a one-time password (HOTP) for a given counter.

    This is the underlying HOTP function that TOTP builds upon.
    """
    counter_bytes = counter.to_bytes(8, byteorder="big")
    hmac_result = _hmac_sha256(key, counter_bytes)
    return _dynamic_truncate(hmac_result)


# --------------------------------------------------------------------------
# Public TOTP API
# --------------------------------------------------------------------------


def generate_totp_secret(length: int = 20) -> str:
    """Generate a cryptographically secure TOTP secret key.

    Args:
        length: Number of bytes to generate (16-64, recommended 20 bytes = 160 bits).

    Returns:
        A base32-encoded string suitable for use as a TOTP secret.
        The returned key is 32 characters long after encoding (20 bytes = 32 base32 chars).
    """
    if not 16 <= length <= 64:
        raise ValueError("Secret length must be between 16 and 64 bytes")

    import secrets

    secret_bytes = secrets.token_bytes(length)
    try:
        return base64.b32encode(secret_bytes).decode("ascii")
    except Exception as exc:
        logger.error("Failed to encode base32 secret: %s", exc)
        raise


def verify_totp(secret: str, otp: str, window: int = 1) -> bool:
    """Verify a TOTP against a secret with optional time window tolerance.

    Args:
        secret: Base32-encoded TOTP secret key.
        otp: The one-time password to verify (typically 6 digits).
        window: How many past/future time windows to check (0 = exact match,
                1 = ±1 window = ±30 seconds, etc.).

    Returns:
        ``True`` if the OTP matches within the specified window.

    Raises:
        ValueError: If the secret is malformed.
    """
    if not secret or not isinstance(secret, str):
        logger.error("Invalid TOTP secret: %s", secret)
        return False

    if not otp or not otp.isdigit():
        logger.error("Invalid OTP format: %s", otp)
        return False

    try:
        secret_bytes = base64.b32decode(secret.upper())
    except Exception as exc:
        logger.error("Failed to decode base32 secret: %s", exc)
        raise ValueError(f"Invalid TOTP secret: {exc}")

    try:
        otp_int = int(otp)
        for offset in range(-window, window + 1):
            counter = _generate_counter() + offset
            generated = _generate_hotp(secret_bytes, counter)
            if generated % (10 ** len(otp)) == otp_int:
                logger.debug("TOTP verified successfully with offset=%d", offset)
                return True
        logger.warning("TOTP verification failed for secret")
        return False
    except Exception as exc:
        logger.exception("Error during TOTP verification: %s", exc)
        return False


def generate_totp(secret: str, timestamp: int | None = None) -> str:
    """Generate a TOTP for a given secret and optional timestamp.

    Args:
        secret: Base32-encoded TOTP secret key.
        timestamp: Optional Unix timestamp; if not provided, current time is used.

    Returns:
        The TOTP as a decimal string.

    Raises:
        ValueError: If the secret is malformed.
    """
    try:
        secret_bytes = base64.b32decode(secret.upper())
    except Exception as exc:
        logger.error("Invalid TOTP secret: %s", exc)
        raise ValueError(f"Invalid TOTP secret: {exc}")

    if timestamp is None:
        timestamp = int(time.time())
    counter = timestamp // 30
    hotp = _generate_hotp(secret_bytes, counter)
    return f"{hotp % (10 ** 10):010d}"[-6:]