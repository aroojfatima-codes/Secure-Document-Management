"""General-purpose utility functions for the SDMS.

These helpers are stateless and free of business logic so they can be
used safely from any module.
"""

from __future__ import annotations

import re
import string
import uuid
from datetime import datetime, timezone
from pathlib import Path


def generate_timestamp() -> str:
    """Return the current UTC time as an ISO-8601 string.

    Returns:
        e.g. ``"2026-07-06T14:30:00.123456+00:00"``
    """
    return datetime.now(timezone.utc).isoformat()


def generate_document_id() -> str:
    """Return a cryptographically random, URL-safe document identifier.

    Uses :func:`uuid.uuid4` to produce a 128-bit unique ID.
    """
    return uuid.uuid4().hex


def sanitize_filename(filename: str) -> str:
    """Remove or replace characters that are unsafe in filenames.

    Keeps only alphanumeric characters, dashes, underscores, and dots.
    All other characters are replaced with an underscore.

    Args:
        filename: The original filename to sanitize.

    Returns:
        A safe filename string.

    Raises:
        ValueError: If the resulting filename is empty.
    """
    safe_chars = string.ascii_letters + string.digits + "-_."
    sanitized = "".join(ch if ch in safe_chars else "_" for ch in filename)
    if not sanitized:
        msg = f"Filename '{filename}' produced an empty safe name."
        raise ValueError(msg)
    return sanitized


def validate_file_path(file_path: str | Path) -> Path:
    """Resolve and validate that a file path exists and is a file.

    Args:
        file_path: Path to validate.

    Returns:
        Resolved :class:`~pathlib.Path` object.

    Raises:
        FileNotFoundError: If the path does not exist.
        ValueError: If the path is not a file.
    """
    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")
    return path


def ensure_directory(path: str | Path) -> Path:
    """Create the directory at *path* (and parents) if it does not exist.

    Args:
        path: Directory path to ensure.

    Returns:
        Resolved :class:`~pathlib.Path` object.
    """
    resolved = Path(path).resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def is_valid_object_id(id_string: str) -> bool:
    """Check whether a string is a valid 24-hex-character MongoDB ObjectId.

    Args:
        id_string: The string to test.

    Returns:
        ``True`` if the string is a valid ObjectId, ``False`` otherwise.
    """
    return bool(re.fullmatch(r"[0-9a-fA-F]{24}", id_string))
