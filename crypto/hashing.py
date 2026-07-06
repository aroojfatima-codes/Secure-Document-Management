"""SHA-256 hashing module for strings, files, and integrity verification.

Implements :class:`~crypto.interfaces.BaseHasher` and provides
convenience methods that higher-level modules use for password storage
and document integrity checks.
"""

from __future__ import annotations

import hashlib
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

        Args:
            data: The raw bytes to hash.

        Returns:
            A 64-character lower-case hex digest string.

        Raises:
            HashingError: If the hashing operation fails.
        """
        try:
            return hashlib.sha256(data).hexdigest()
        except (TypeError, ValueError) as exc:
            raise HashingError(f"Hashing failed: {exc}") from exc

    def verify(self, data: bytes, digest: str) -> bool:
        """Check whether *data* hashes to the given *digest*.

        Args:
            data:   The original bytes.
            digest: Previously computed hex digest to compare against.

        Returns:
            ``True`` if the hash matches, ``False`` otherwise.
        """
        return self.hash(data) == digest

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------

    def hash_string(self, value: str) -> str:
        """Hash a Unicode string (encoded as UTF-8).

        Args:
            value: The string to hash.

        Returns:
            Hex-encoded SHA-256 digest.
        """
        return self.hash(value.encode("utf-8"))

    def hash_file(self, file_path: str | Path, chunk_size: int = 65536) -> str:
        """Compute the SHA-256 digest of a file on disk.

        Reads the file in streaming fashion to avoid loading large
        documents entirely into memory.

        Args:
            file_path:  Path to the file.
            chunk_size: Number of bytes to read per iteration (default 64 KB).

        Returns:
            Hex-encoded SHA-256 digest.

        Raises:
            HashingError: If the file cannot be read.
        """
        path = Path(file_path)
        if not path.is_file():
            raise HashingError(f"Not a file or does not exist: {path}")

        try:
            hasher = hashlib.sha256()
            with path.open("rb") as fh:
                while chunk := fh.read(chunk_size):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (OSError, ValueError) as exc:
            raise HashingError(
                f"Failed to hash file '{path}': {exc}"
            ) from exc

    def hash_stream(self, stream: BinaryIO, chunk_size: int = 65536) -> str:
        """Compute the SHA-256 digest of a binary stream.

        Args:
            stream:     An open binary stream (e.g. ``open(f, "rb")``).
            chunk_size: Read buffer size in bytes (default 64 KB).

        Returns:
            Hex-encoded SHA-256 digest.
        """
        try:
            hasher = hashlib.sha256()
            while chunk := stream.read(chunk_size):
                hasher.update(chunk)
            return hasher.hexdigest()
        except (OSError, ValueError) as exc:
            raise HashingError(
                f"Failed to hash stream: {exc}"
            ) from exc

    def verify_file(
        self, file_path: str | Path, expected_digest: str
    ) -> bool:
        """Verify the integrity of a file against an expected hash.

        Args:
            file_path:       Path to the file.
            expected_digest: The previously computed hex digest.

        Returns:
            ``True`` if the file hash matches *expected_digest*.
        """
        return self.hash_file(file_path) == expected_digest
