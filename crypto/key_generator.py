"""Cryptographically secure random generation for keys, IVs, salts, and tokens.

Uses :mod:`os.urandom` as the source of entropy so that all generated
values are suitable for security-sensitive operations.
"""

from __future__ import annotations

import os
import uuid

from crypto.exceptions import KeyGenerationError

AES_KEY_LENGTH: int = 32
AES_IV_LENGTH: int = 16
SALT_LENGTH: int = 16
TOKEN_LENGTH: int = 32


def _random_bytes(length: int, purpose: str) -> bytes:
    """Generate *length* cryptographically random bytes.

    Args:
        length: Number of random bytes to produce.
        purpose: Human-readable description used in error messages.

    Raises:
        KeyGenerationError: If the OS entropy source fails.
    """
    try:
        return os.urandom(length)
    except OSError as exc:
        raise KeyGenerationError(
            f"Failed to generate {purpose}: {exc}"
        ) from exc


def generate_aes_key() -> bytes:
    """Generate a cryptographically random 256-bit (32-byte) AES key."""
    return _random_bytes(AES_KEY_LENGTH, "AES key")


def generate_iv() -> bytes:
    """Generate a cryptographically random 128-bit (16-byte) IV."""
    return _random_bytes(AES_IV_LENGTH, "initialisation vector")


def generate_salt() -> bytes:
    """Generate a cryptographically random salt value (16 bytes)."""
    return _random_bytes(SALT_LENGTH, "salt")


def generate_secure_token(length: int = TOKEN_LENGTH) -> str:
    """Generate a hex token suitable for session IDs or nonces.

    Args:
        length: Number of random bytes (default 32 -> 64 hex chars).

    Returns:
        Lower-case hex-encoded secure token.
    """
    return _random_bytes(length, "secure token").hex()


def generate_crypto_id() -> str:
    """Return a random UUID4 hex string for use as a cryptographic identifier."""
    return uuid.uuid4().hex
