"""General-purpose utility functions for the SDMS.

These helpers are stateless and free of business logic so they can be
used safely from any module.
"""

from __future__ import annotations

from pathlib import Path


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
