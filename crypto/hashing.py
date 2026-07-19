"""SHA-256 hashing module for strings, files, and integrity verification.

Implements :class:`~crypto.interfaces.BaseHasher` and provides
convenience methods that higher-level modules use for password storage
and document integrity checks.
"""

from __future__ import annotations

import hashlib
import hmac
from pathlib import Path
from typing import BinaryIO

from crypto.exceptions import HashingError
from crypto.interfaces import BaseHasher


class SHA256Hasher(BaseHasher):
    """SHA-256 hashing implementation.

    Usage::

        hasher = SHA256Hasher()
        digest = hasher.hash(b"hello")
        assert hasher.verify(b"hello", digest)
    """

    def hash(self, data: bytes) -> str:
        """Return the hex-encoded SHA-256 digest of *data*.

        Raises:
            HashingError: If the hashing operation fails.
        """
        try:
            return hashlib.sha256(data).hexdigest()
        except (TypeError, ValueError) as exc:
            raise HashingError(f"Hashing failed: {exc}") from exc

    def verify(self, data: bytes, digest: str) -> bool:
        """Constant-time check whether *data* hashes to *digest*."""
        return hmac.compare_digest(self.hash(data), digest)

    def hash_string(self, value: str) -> str:
        """Hash a Unicode string (encoded as UTF-8)."""
        return self.hash(value.encode("utf-8"))

    def _hash_stream(self, stream: BinaryIO, chunk_size: int = 65536) -> str:
        """Compute SHA-256 over a binary stream."""
        try:
            hasher = hashlib.sha256()
            while chunk := stream.read(chunk_size):
                hasher.update(chunk)
            return hasher.hexdigest()
        except (OSError, ValueError) as exc:
            raise HashingError(f"Failed to hash stream: {exc}") from exc

    def hash_file(self, file_path: str | Path, chunk_size: int = 65536) -> str:
        """Compute the SHA-256 digest of a file on disk.

        Reads the file in streaming fashion to avoid loading large
        documents entirely into memory.

        Raises:
            HashingError: If the file cannot be read.
        """
        path = Path(file_path)
        if not path.is_file():
            raise HashingError(f"Not a file or does not exist: {path}")

        try:
            with path.open("rb") as fh:
                return self._hash_stream(fh, chunk_size)
        except (OSError, ValueError) as exc:
            raise HashingError(
                f"Failed to hash file '{path}': {exc}"
            ) from exc

    def hash_stream(self, stream: BinaryIO, chunk_size: int = 65536) -> str:
        """Compute the SHA-256 digest of a binary stream."""
        return self._hash_stream(stream, chunk_size)

    def verify_file(
        self, file_path: str | Path, expected_digest: str
    ) -> bool:
        """Verify file integrity against an expected hash (constant-time)."""
        return hmac.compare_digest(self.hash_file(file_path), expected_digest)
