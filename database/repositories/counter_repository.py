"""Repository for atomic counter operations.

Manages the ``counters`` collection used to generate sequential
identifiers (e.g. Document IDs).  Each counter is identified by
its ``_id`` field (the counter name) and holds a ``seq`` integer
that is atomically incremented via ``find_one_and_update`` with
``$inc``.

This guarantees uniqueness even when multiple clients request
identifiers concurrently.
"""

from __future__ import annotations

from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from database.manager import DatabaseManager
from exceptions.custom_exceptions import DatabaseError
from logger.logging_config import get_logger

logger = get_logger(__name__)


class CounterRepository:
    """Provides atomic sequential counter operations.

    Usage::

        repo = CounterRepository()
        next_val = repo.get_next_sequence("document_id")
    """

    _collection_name: str = "counters"

    def __init__(self) -> None:
        self._db_mgr = DatabaseManager()

    @property
    def _collection(self) -> Collection:
        return self._db_mgr.get_collection(self._collection_name)

    def get_next_sequence(self, counter_name: str) -> int:
        """Atomically increment and return the next sequence value.

        If the counter does not exist it is initialised to 1.

        Args:
            counter_name: The logical name of the counter
                          (e.g. ``"document_id"``).

        Returns:
            The next integer in the sequence (1, 2, 3, …).

        Raises:
            DatabaseError: If the MongoDB operation fails.
        """
        try:
            result = self._collection.find_one_and_update(
                {"_id": counter_name},
                {"$inc": {"seq": 1}},
                upsert=True,
                return_document=True,
            )
            seq: int = result.get("seq", 1)
            logger.debug(
                "Counter '%s' incremented to %d.", counter_name, seq
            )
            return seq
        except PyMongoError as exc:
            logger.error(
                "Failed to increment counter '%s': %s",
                counter_name,
                exc,
            )
            raise DatabaseError(
                f"Could not increment counter '{counter_name}': {exc}"
            ) from exc

    def get_current_value(self, counter_name: str) -> int:
        """Return the current sequence value without incrementing.

        Args:
            counter_name: The logical name of the counter.

        Returns:
            The current value, or 0 if the counter does not exist.
        """
        try:
            doc = self._collection.find_one({"_id": counter_name})
            return doc.get("seq", 0) if doc else 0
        except PyMongoError as exc:
            logger.error(
                "Failed to read counter '%s': %s", counter_name, exc
            )
            raise DatabaseError(
                f"Could not read counter '{counter_name}': {exc}"
            ) from exc

    def reset_counter(self, counter_name: str, value: int = 0) -> None:
        """Reset a counter to a specific value.

        Args:
            counter_name: The logical name of the counter.
            value:        The value to set (default 0).
        """
        try:
            self._collection.update_one(
                {"_id": counter_name},
                {"$set": {"seq": value}},
                upsert=True,
            )
            logger.info(
                "Counter '%s' reset to %d.", counter_name, value
            )
        except PyMongoError as exc:
            logger.error(
                "Failed to reset counter '%s': %s", counter_name, exc
            )
            raise DatabaseError(
                f"Could not reset counter '{counter_name}': {exc}"
            ) from exc
