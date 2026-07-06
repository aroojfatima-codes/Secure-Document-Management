"""Cryptography-specific exception classes.

All exceptions in this module inherit from
:class:`exceptions.custom_exceptions.CryptographicError` so they are
caught by the existing SDMS exception framework.
"""

from __future__ import annotations

from exceptions.custom_exceptions import CryptographicError


class AESError(CryptographicError):
    """Raised when AES encryption or decryption fails."""


class RSAError(CryptographicError):
    """Raised when RSA key generation, encryption, or decryption fails."""


class HashingError(CryptographicError):
    """Raised when hashing or hash verification fails."""


class KeyGenerationError(CryptographicError):
    """Raised when secure random key or token generation fails."""


class Base64Error(CryptographicError):
    """Raised when Base64 encoding or decoding fails."""


class PaddingError(CryptographicError):
    """Raised when PKCS7 padding or unpadding fails."""


class KeySerializationError(CryptographicError):
    """Raised when exporting or importing cryptographic keys fails."""


class IntegrityCheckError(CryptographicError):
    """Raised when hash-based integrity verification fails."""
