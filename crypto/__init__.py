"""SDMS Cryptography Module.

A standalone, reusable security library that implements hybrid
cryptography (AES-256-CBC + RSA-2048-OAEP), SHA-256 hashing, secure
key generation, Base64 encoding, and encrypted payload data structures.

This module has **zero dependencies** on the database, business logic,
or user interface — it can be imported and tested independently.
"""

from __future__ import annotations

from crypto.aes_cipher import AESCipher
from crypto.base64_utils import b64_decode, b64_encode
from crypto.exceptions import (
    AESError,
    Base64Error,
    HashingError,
    IntegrityCheckError,
    KeyGenerationError,
    KeySerializationError,
    PaddingError,
    RSAError,
)
from crypto.hashing import SHA256Hasher
from crypto.interfaces import BaseCipher, BaseHasher
from crypto.key_generator import (
    generate_aes_key,
    generate_crypto_id,
    generate_iv,
    generate_salt,
    generate_secure_token,
)
from crypto.payload import EncryptedKeyPayload, EncryptedPayload
from crypto.rsa_cipher import RSACipher

__all__: list[str] = [
    "AESCipher",
    "AESError",
    "Base64Error",
    "BaseCipher",
    "BaseHasher",
    "b64_decode",
    "b64_encode",
    "EncryptedKeyPayload",
    "EncryptedPayload",
    "generate_aes_key",
    "generate_crypto_id",
    "generate_iv",
    "generate_salt",
    "generate_secure_token",
    "HashingError",
    "IntegrityCheckError",
    "KeyGenerationError",
    "KeySerializationError",
    "PaddingError",
    "RSACipher",
    "RSAError",
    "SHA256Hasher",
]
