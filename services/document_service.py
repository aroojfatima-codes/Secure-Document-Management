"""Document upload service — orchestrates the secure hybrid-encryption
upload workflow for authenticated users.

Flow: validate session → validate file → read bytes → SHA-256 hash →
generate AES key + IV → AES-256-CBC encrypt → RSA-wrap AES key →
save encrypted file → persist document metadata.

No cryptographic algorithms or database queries are implemented
directly here — the service delegates to the crypto, storage, and
repository abstractions.
"""

from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import Any

from crypto.aes_cipher import AESCipher
from crypto.base64_utils import b64_encode
from crypto.hashing import SHA256Hasher
from crypto.key_generator import generate_aes_key, generate_crypto_id, generate_iv
from crypto.rsa_cipher import RSACipher
from database.repositories.document_repository import DocumentRepository
from exceptions.custom_exceptions import (
    FileHandlingError,
    SDMSException,
    ValidationError,
)
from logger.logging_config import get_logger
from models.document import Document
from services.document_id_service import DocumentIDGeneratorService
from services.session_manager import SessionManager
from storage.manager import StorageManager

logger = get_logger(__name__)

ENCRYPTED_FILE_SUFFIX: str = ".enc"
MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB


class DocumentUploadService:
    """Coordinates the full document-upload workflow.

    Usage::

        service = DocumentUploadService()
        result = service.upload("/path/to/document.pdf")
    """

    def __init__(self) -> None:
        self._session_mgr: SessionManager = SessionManager()
        self._storage_mgr: StorageManager = StorageManager()
        self._doc_repo: DocumentRepository = DocumentRepository()
        self._hasher: SHA256Hasher = SHA256Hasher()
        self._doc_id_svc: DocumentIDGeneratorService = DocumentIDGeneratorService()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def upload(self, file_path: str) -> dict[str, Any]:
        """Upload, encrypt, and persist a document.

        The upload flow:

        1. Verify the user has an active authenticated session.
        2. Validate the file (exists, readable, size limits).
        3. Read the full file contents into memory.
        4. Generate a SHA-256 hash of the plaintext.
        5. Generate an AES-256 key and IV.
        6. Encrypt the file contents with AES-256-CBC.
        7. Encrypt the AES key with the user's RSA public key.
        8. Save the encrypted file to the storage directory.
        9. Persist the document metadata in MongoDB.
        10. Return a success summary.

        If any step after file storage fails, the partially-written
        file is cleaned up to prevent orphaned data.

        Args:
            file_path: Absolute or relative path to the document
                on the local filesystem.

        Returns:
            A dict with upload metadata::

                {
                    "document_id": "...",
                    "original_filename": "...",
                    "file_size": 12345,
                    "sha256_hash": "...",
                    "message": "Document uploaded and encrypted successfully."
                }

        Raises:
            AuthenticationError: If no session is active.
            ValidationError: If the file is invalid or too large.
            FileHandlingError: If file I/O fails.
            SDMSException: On any other failure (with cleanup).
        """
        session = self._session_mgr.get_current_session()

        path: Path = self._validate_file(file_path)
        original_filename: str = path.name
        file_size: int = path.stat().st_size
        mime_type: str = (
            mimetypes.guess_type(original_filename)[0]
            or "application/octet-stream"
        )
        document_id: str = self._doc_id_svc.generate_document_id()
        internal_id: str = generate_crypto_id()
        encrypted_filename: str = f"{internal_id}{ENCRYPTED_FILE_SUFFIX}"

        try:
            file_bytes: bytes = path.read_bytes()
            logger.debug("Read %d bytes from '%s'.", file_size, original_filename)

            sha256_hash: str = self._hasher.hash(file_bytes)

            aes_key: bytes = generate_aes_key()
            iv: bytes = generate_iv()

            aes_cipher: AESCipher = AESCipher(aes_key)
            ciphertext, used_iv = aes_cipher.encrypt_bytes(file_bytes, iv)

            rsa_cipher: RSACipher = RSACipher()
            rsa_cipher.load_public_key(session.rsa_public_key.encode("utf-8"))
            encrypted_aes_key: bytes = rsa_cipher.encrypt(aes_key)

            self._storage_mgr.save_encrypted_file(encrypted_filename, ciphertext)

            document = Document(
                document_id=document_id,
                original_filename=original_filename,
                encrypted_filename=encrypted_filename,
                owner_id=session.user_id,
                encrypted_aes_key=b64_encode(encrypted_aes_key),
                iv=b64_encode(used_iv),
                sha256_hash=sha256_hash,
                file_size=file_size,
                mime_type=mime_type,
            )
            self._doc_repo.create_document(document)

            logger.info(
                "Document '%s' uploaded (id=%s, %d bytes, hash=%s).",
                original_filename,
                document_id,
                file_size,
                sha256_hash[:16],
            )

            return {
                "document_id": document_id,
                "original_filename": original_filename,
                "file_size": file_size,
                "mime_type": mime_type,
                "sha256_hash": sha256_hash,
                "encrypted_filename": encrypted_filename,
            }

        except SDMSException:
            self._storage_mgr.delete_encrypted_file(encrypted_filename)
            raise
        except OSError as exc:
            self._storage_mgr.delete_encrypted_file(encrypted_filename)
            raise FileHandlingError(
                f"File operation failed during upload: {exc}"
            ) from exc
        except Exception as exc:
            self._storage_mgr.delete_encrypted_file(encrypted_filename)
            raise SDMSException(
                f"Unexpected error during document upload: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_file(file_path: str) -> Path:
        """Validate that the file exists, is readable, and is within limits.

        Args:
            file_path: Path to validate.

        Returns:
            Resolved :class:`~pathlib.Path`.

        Raises:
            ValidationError: If validation fails.
        """
        if not file_path or not file_path.strip():
            raise ValidationError("File path is required.")

        path: Path = Path(file_path).resolve()

        if not path.exists():
            raise ValidationError(f"File not found: '{path}'.")
        if not path.is_file():
            raise ValidationError(f"Path is not a file: '{path}'.")
        if not os.access(str(path), os.R_OK):
            raise ValidationError(f"File is not readable: '{path}'.")

        file_size: int = path.stat().st_size
        if file_size == 0:
            raise ValidationError(f"File is empty: '{path}'.")
        if file_size > MAX_FILE_SIZE_BYTES:
            max_mb: int = MAX_FILE_SIZE_BYTES // (1024 * 1024)
            size_mb: float = file_size / (1024 * 1024)
            raise ValidationError(
                f"File size ({size_mb:.1f} MB) exceeds the maximum "
                f"allowed size of {max_mb} MB."
            )

        return path
