"""Storage manager for encrypted documents on disk.

Provides read, write, and delete operations within the encrypted
storage directory.  All file operations use the encrypted filename
(never the original filename) to prevent information leakage
through the filesystem.
"""

from __future__ import annotations

from pathlib import Path

from config.settings import settings
from exceptions.custom_exceptions import FileHandlingError
from logger.logging_config import get_logger
from utilities.helpers import ensure_directory

logger = get_logger(__name__)


class StorageManager:
    """Manages on-disk encrypted document storage.

    Two directories are maintained:

        * **Encrypted documents** (``storage/encrypted_documents/``)
        * **Temporary files**      (``storage/temp/``)
    """

    def __init__(self) -> None:
        self._encrypted_dir: Path = settings.STORAGE_ENCRYPTED_PATH
        self._temp_dir: Path = settings.STORAGE_TEMP_PATH

    def initialise(self) -> None:
        """Create storage directories if they do not exist."""
        ensure_directory(self._encrypted_dir)
        ensure_directory(self._temp_dir)
        logger.info(
            "Storage directories initialised at '%s' and '%s'.",
            self._encrypted_dir,
            self._temp_dir,
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def encrypted_dir(self) -> Path:
        """Return the resolved path to the encrypted-document directory."""
        return self._encrypted_dir

    @property
    def temp_dir(self) -> Path:
        """Return the resolved path to the temporary-storage directory."""
        return self._temp_dir

    # ------------------------------------------------------------------
    # Encrypted file operations
    # ------------------------------------------------------------------

    def save_encrypted_file(self, encrypted_filename: str, data: bytes) -> Path:
        """Write encrypted bytes to the storage directory.

        Args:
            encrypted_filename: The filename to use on disk
                (e.g. ``"<document_id>.enc"``).
            data:               The encrypted binary data.

        Returns:
            The full :class:`~pathlib.Path` to the written file.

        Raises:
            FileHandlingError: If the write fails.
        """
        dest: Path = self._encrypted_dir / encrypted_filename
        try:
            dest.write_bytes(data)
            logger.debug("Wrote encrypted file: %s (%d bytes).", dest, len(data))
            return dest
        except OSError as exc:
            raise FileHandlingError(
                f"Failed to write encrypted file '{dest}': {exc}"
            ) from exc

    def read_encrypted_file(self, encrypted_filename: str) -> bytes:
        """Read encrypted bytes from the storage directory.

        Args:
            encrypted_filename: The filename on disk.

        Returns:
            The encrypted binary data.

        Raises:
            FileHandlingError: If the file does not exist or cannot be read.
        """
        src: Path = self._encrypted_dir / encrypted_filename
        if not src.is_file():
            raise FileHandlingError(
                f"Encrypted file not found: '{src}'."
            )
        try:
            data: bytes = src.read_bytes()
            logger.debug("Read encrypted file: %s (%d bytes).", src, len(data))
            return data
        except OSError as exc:
            raise FileHandlingError(
                f"Failed to read encrypted file '{src}': {exc}"
            ) from exc

    def delete_encrypted_file(self, encrypted_filename: str) -> None:
        """Remove an encrypted file from the storage directory.

        Args:
            encrypted_filename: The filename on disk.

        Raises:
            FileHandlingError: If the file cannot be deleted.
        """
        target: Path = self._encrypted_dir / encrypted_filename
        if not target.is_file():
            logger.warning("Encrypted file not found for deletion: '%s'.", target)
            return
        try:
            target.unlink()
            logger.debug("Deleted encrypted file: %s.", target)
        except OSError as exc:
            raise FileHandlingError(
                f"Failed to delete encrypted file '{target}': {exc}"
            ) from exc

    def encrypted_file_exists(self, encrypted_filename: str) -> bool:
        """Check whether an encrypted file exists on disk.

        Args:
            encrypted_filename: The filename on disk.

        Returns:
            ``True`` if the file exists.
        """
        return (self._encrypted_dir / encrypted_filename).is_file()
