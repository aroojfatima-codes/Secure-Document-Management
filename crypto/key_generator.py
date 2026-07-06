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


def generate_aes_key() -> bytes:
    """Generate a cryptographically random 256-bit (32-byte) AES key.

    Returns:
        32 random bytes suitable as an AES-256 key.

    Raises:
        KeyGenerationError: If the OS entropy source fails.
    """
    try:
        return os.urandom(AES_KEY_LENGTH)
    except OSError as exc:
        raise KeyGenerationError(
            f"Failed to generate AES key: {exc}"
        ) from exc


def generate_iv() -> bytes:
    """Generate a cryptographically random 128-bit (16-byte) IV.

    Returns:
        16 random bytes suitable as an AES-CBC initialisation vector.

    Raises:
        KeyGenerationError: If the OS entropy source fails.
    """
    try:
        return os.urandom(AES_IV_LENGTH)
    except OSError as exc:
        raise KeyGenerationError(
            f"Failed to generate initialisation vector: {exc}"
        ) from exc


def generate_salt() -> bytes:
    """Generate a cryptographically random salt value (16 bytes).

    Returns:
        16 random bytes usable as a password salt.
    """
    try:
        return os.urandom(SALT_LENGTH)
    except OSError as exc:
        raise KeyGenerationError(
            f"Failed to generate salt: {exc}"
        ) from exc


def generate_secure_token(length: int = TOKEN_LENGTH) -> str:
    """Generate a URL-safe hex token suitable for session IDs or nonces.

    Args:
        length: Number of random bytes to draw (default 32 → 64 hex
            characters).  The returned hex string is twice this length.

    Returns:
        Lower-case hex-encoded secure token.

    Raises:
        KeyGenerationError: If the OS entropy source fails.
    """
    try:
        return os.urandom(length).hex()
    except OSError as exc:
        raise KeyGenerationError(
            f"Failed to generate secure token: {exc}"
        ) from exc


def generate_crypto_id() -> str:
    """Return a random UUID4 hex string for use as a cryptographic identifier.

    Returns:
        A 32-character hex string (UUID4 without hyphens).
    """
    return uuid.uuid4().hex
