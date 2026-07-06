"""Abstract base model with serialisation and validation helpers.

All SDMS data models inherit from :class:`BaseModel` to ensure
a consistent interface for converting between Python objects
and MongoDB documents.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseModel(ABC):
    """Abstract base for all SDMS data models.

    Subclasses must implement :meth:`to_dict` and :meth:`validate`.
    """

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialize this model instance to a MongoDB document dict.

        The returned dict is ready for ``insert_one`` / ``replace_one``.
        The ``_id`` field is excluded so MongoDB auto-generates it
        on insert unless the caller explicitly sets it.
        """

    @abstractmethod
    def validate(self) -> None:
        """Validate model fields, raising :class:`ValidationError` on failure."""

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> BaseModel:
        """Construct a model instance from a MongoDB document dict."""

    def update(self, updates: dict[str, Any]) -> None:
        """Apply field updates from a dict, skipping unknown attributes."""
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value)
