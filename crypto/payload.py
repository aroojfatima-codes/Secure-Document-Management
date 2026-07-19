"""Data structures that represent encrypted payloads.

These dataclasses encapsulate everything needed to decrypt a piece of
data: the ciphertext itself, the algorithm used, the initialisation
vector (for AES), and -- for hybrid-encryption scenarios -- the
RSA-wrapped AES key.

Modules that sit above the cryptography layer (services, controllers)
work with these payload objects instead of raw byte tuples.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EncryptedPayload:
    """Result of an AES encryption operation.

    Attributes:
        ciphertext: The encrypted bytes.
        iv:         16-byte initialisation vector used during encryption.
        algorithm:  Human-readable algorithm identifier
            (e.g. ``"AES-256-CBC"``).
    """

    ciphertext: bytes
    iv: bytes
    algorithm: str = "AES-256-CBC"


@dataclass(frozen=True)
class EncryptedKeyPayload:
    """Result of an RSA encryption operation protecting an AES key.

    Attributes:
        encrypted_key:   RSA-encrypted AES key bytes.
        iv:              The AES IV (stored alongside the wrapped key so
            the decryptor has everything needed).
        wrapped_algorithm:    Algorithm used to encrypt the AES key
            (e.g. ``"RSA-2048-OAEP-SHA-256"``).
        data_algorithm:  Algorithm used for the actual data encryption
            (e.g. ``"AES-256-CBC"``).
    """

    encrypted_key: bytes
    iv: bytes
    wrapped_algorithm: str = "RSA-2048-OAEP-SHA-256"
    data_algorithm: str = "AES-256-CBC"
