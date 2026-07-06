"""SDMS data models — define the structure, validation, and serialisation
of entities persisted in MongoDB.

Every model inherits from :class:`~models.base.BaseModel`.
"""

from __future__ import annotations

from models.base import BaseModel
from models.document import Document
from models.user import User

__all__: list[str] = [
    "BaseModel",
    "Document",
    "User",
]
