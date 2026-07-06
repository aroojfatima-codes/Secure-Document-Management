"""Base64 encoding and decoding utilities for binary data.

Encrypted ciphertext, initialisation vectors, RSA keys, and other
binary values need to be stored as text inside MongoDB. This module
provides a single pair of helpers so the rest of the codebase never
has to reason about Base64 directly.
"""

from __future__ import annotations

import base64
import binascii

from crypto.exceptions import Base64Error


def b64_encode(data: bytes) -> str:
    """Encode *data* to a Base64-encoded UTF-8 string.

    Args:
        data: Arbitrary binary data to encode.

    Returns:
        Base64-encoded string (standard alphabet, with padding).

    Raises:
        Base64Error: If encoding fails for any reason.
    """
    try:
        return base64.b64encode(data).decode("utf-8")
    except (ValueError, TypeError) as exc:
        raise Base64Error(f"Base64 encoding failed: {exc}") from exc


def b64_decode(encoded: str) -> bytes:
    """Decode a Base64-encoded string back to raw bytes.

    Args:
        encoded: Base64-encoded string (standard alphabet, may include
            padding).

    Returns:
        Decoded binary data.

    Raises:
        Base64Error: If the string is not valid Base64.
    """
    try:
        return base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError, binascii.Error) as exc:
        raise Base64Error(
            f"Base64 decoding failed — invalid input: {exc}"
        ) from exc
