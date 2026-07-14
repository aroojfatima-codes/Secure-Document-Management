"""Document ID Generator Service — produces human-readable sequential
document identifiers.

Generates IDs in the format ``DOC-XXXX`` where ``XXXX`` is a
zero-padded sequential number (e.g. ``DOC-0001``, ``DOC-0157``).

The service delegates counter management to
:class:`~database.repositories.counter_repository.CounterRepository`
and never generates sequence numbers directly.  Uniqueness is
guaranteed by MongoDB's atomic ``$inc`` operation.
"""

from __future__ import annotations

from logger.logging_config import get_logger
from database.repositories.counter_repository import CounterRepository

logger = get_logger(__name__)

DOCUMENT_ID_PREFIX: str = "DOC"
DOCUMENT_ID_WIDTH: int = 4


class DocumentIDGeneratorService:
    """Generates sequential, human-readable Document IDs.

    Usage::

        svc = DocumentIDGeneratorService()
        doc_id = svc.generate_document_id()   # "DOC-0001"
        doc_id = svc.generate_document_id()   # "DOC-0002"
    """

    def __init__(self) -> None:
        self._counter_repo = CounterRepository()

    def generate_document_id(self) -> str:
        """Generate the next sequential Document ID.

        Returns:
            A string like ``DOC-0001``, ``DOC-0042``, ``DOC-1234``.

        Raises:
            DatabaseError: If the counter cannot be incremented.
        """
        seq: int = self._counter_repo.get_next_sequence("document_id")
        doc_id: str = f"{DOCUMENT_ID_PREFIX}-{seq:0{DOCUMENT_ID_WIDTH}d}"
        logger.info("Generated document_id: %s (seq=%d).", doc_id, seq)
        return doc_id

    def get_current_count(self) -> int:
        """Return how many Document IDs have been generated so far.

        Returns:
            The current counter value (0 if none generated yet).
        """
        return self._counter_repo.get_current_value("document_id")
