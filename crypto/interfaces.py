"""Abstract base classes for all cryptographic implementations.

Concrete cipher and hasher classes in this package inherit from
these ABCs so that higher-level modules can program against an
interface rather than a specific implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from crypto.payload import EncryptedPayload

_PayloadT = TypeVar("_PayloadT", bytes, EncryptedPayload)


class BaseCipher(ABC, Generic[_PayloadT]):
    """Abstract interface that all cipher implementations must satisfy.

    Type parameter ``_PayloadT`` is the return type of ``encrypt`` and
    the argument type of ``decrypt`` — ``bytes`` for RSA, and
    :class:`~crypto.payload.EncryptedPayload` for AES.
    """

    @abstractmethod
    def encrypt(self, data: bytes) -> _PayloadT:
        """Encrypt *data* and return the ciphertext / payload.

        Args:
            data: Plaintext bytes.

        Returns:
            Encrypted output (type varies by implementation).
        """
        ...

    @abstractmethod
    def decrypt(self, ciphertext: _PayloadT) -> bytes:
        """Decrypt *ciphertext* and return plaintext.

        Args:
            ciphertext: The encrypted data or payload object.

        Returns:
            Original plaintext bytes.
        """
        ...


class BaseHasher(ABC):
    """Abstract interface for hashing implementations."""

    @abstractmethod
    def hash(self, data: bytes) -> str:
        """Return a hex-encoded digest of *data*."""
        ...

    @abstractmethod
    def verify(self, data: bytes, digest: str) -> bool:
        """Check whether *data* hashes to the given *digest*.

        Returns:
            ``True`` if the hash matches, ``False`` otherwise.
        """
        ...
