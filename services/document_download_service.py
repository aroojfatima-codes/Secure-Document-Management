"""Document download service — decrypts and verifies documents for retrieval.

Completes the secure document lifecycle by reversing the upload
process: authenticated owners can retrieve their original files
after RSA key unwrapping, AES-256-CBC decryption, and SHA-256
integrity verification.

No plaintext AES key is ever persisted — it exists only in memory
during decryption and is discarded immediately after use.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from crypto.aes_cipher import AESCipher
from crypto.base64_utils import b64_decode
from crypto.exceptions import IntegrityCheckError
from crypto.hashing import SHA256Hasher
from crypto.rsa_cipher import RSACipher
from database.exceptions import DocumentNotFoundError
from database.repositories.document_repository import DocumentRepository
from exceptions.custom_exceptions import ValidationError
from logger.logging_config import get_logger
from services.session_manager import SessionManager
from storage.manager import StorageManager

logger = get_logger(__name__)


class DocumentDownloadService:
    """Coordinates the full document download / decrypt / verify workflow.

    Usage::

        svc = DocumentDownloadService()
        result = svc.download(document_id="abc...", output_dir="/tmp")
    """

    def __init__(self) -> None:
        self._session_mgr: SessionManager = SessionManager()
        self._storage_mgr: StorageManager = StorageManager()
        self._doc_repo: DocumentRepository = DocumentRepository()
        self._hasher: SHA256Hasher = SHA256Hasher()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def download(self, document_id: str, output_dir: str) -> dict[str, Any]:
        """Download, decrypt, verify, and write a document.

        The download flow:

        1. Verify an active authenticated session exists.
        2. Retrieve document metadata from MongoDB.
        3. Confirm the current user is the document owner.
        4. Load the encrypted file from secure storage.
        5. RSA-decrypt the AES-256 key using the session's private key.
        6. AES-256-CBC decrypt the ciphertext.
        7. SHA-256 integrity verification against the stored hash.
        8. Write the decrypted file to *output_dir*.
        9. Return success metadata.

        If integrity verification fails, the operation is aborted
        and no file is written.

        Args:
            document_id: The UUID4 hex document identifier.
            output_dir:  Directory path where the decrypted file will
                         be written.

        Returns:
            A dict with download metadata::

                {
                    "document_id": "...",
                    "original_filename": "...",
                    "output_path": "/path/to/restored/file.pdf",
                    "file_size": 12345,
                    "sha256_hash": "...",
                    "integrity_verified": True,
                }

        Raises:
            AuthenticationError: If no session is active.
            DocumentNotFoundError: If the document does not exist or
                the user has no access.
            FileHandlingError: If the encrypted file is missing or
                unreadable on disk.
            IntegrityCheckError: If the decrypted content hash does
                not match the stored hash.
            CryptographicError: If RSA or AES decryption fails.
            ValidationError: If input parameters are invalid.
            SDMSException: On any other unexpected failure.
        """
        session = self._session_mgr.get_current_session()

        if not document_id or not document_id.strip():
            raise ValidationError("Document ID is required.")

        if not output_dir or not output_dir.strip():
            raise ValidationError("Output directory is required.")

        output_path: Path = Path(output_dir).resolve()

        doc = self._doc_repo.get_by_document_id(document_id)
        if doc is None:
            raise DocumentNotFoundError(
                f"Document '{document_id}' not found."
            )

        encrypted_aes_key_str: str
        if doc.owner_id == session.user_id:
            encrypted_aes_key_str = doc.encrypted_aes_key
        else:
            shared_entry = next(
                (
                    sw
                    for sw in doc.shared_with
                    if sw.user_id == session.user_id
                ),
                None,
            )
            if shared_entry is None or not shared_entry.encrypted_aes_key:
                raise DocumentNotFoundError(
                    f"Document '{document_id}' not found."
                )
            encrypted_aes_key_str = shared_entry.encrypted_aes_key

        logger.info(
            "Downloading document '%s' (user=%s).",
            document_id,
            session.user_id,
        )

        ciphertext: bytes = self._storage_mgr.read_encrypted_file(
            doc.encrypted_filename
        )
        logger.debug(
            "Loaded encrypted file '%s' (%d bytes).",
            doc.encrypted_filename,
            len(ciphertext),
        )

        encrypted_aes_key: bytes = b64_decode(encrypted_aes_key_str)
        iv: bytes = b64_decode(doc.iv)

        rsa_cipher: RSACipher = RSACipher()
        rsa_cipher.load_private_key(
            session.rsa_private_key.encode("utf-8")
        )
        aes_key: bytes = rsa_cipher.decrypt(encrypted_aes_key)
        logger.debug("AES key recovered via RSA decryption.")

        aes_cipher: AESCipher = AESCipher(aes_key)
        plaintext: bytes = aes_cipher.decrypt_bytes(ciphertext, iv)
        logger.debug(
            "AES decryption completed (%d bytes).", len(plaintext)
        )

        if not self._hasher.verify(plaintext, doc.sha256_hash):
            raise IntegrityCheckError(
                f"Integrity verification failed for document "
                f"'{document_id}'. The decrypted content does not "
                f"match the stored SHA-256 hash. Possible corruption "
                f"or tampering detected."
            )

        logger.debug("Integrity verification passed.")

        output_path = self._resolve_output_path(
            output_path / doc.original_filename
        )

        if not output_path.parent.exists():
            output_path.parent.mkdir(parents=True, exist_ok=True)

        output_path.write_bytes(plaintext)
        logger.info(
            "Document '%s' decrypted and written to '%s' (%d bytes).",
            document_id,
            str(output_path),
            len(plaintext),
        )

        return {
            "document_id": doc.document_id,
            "original_filename": doc.original_filename,
            "output_path": str(output_path),
            "file_size": doc.file_size,
            "sha256_hash": doc.sha256_hash,
            "integrity_verified": True,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_output_path(target: Path) -> Path:
        """If *target* already exists, append a numeric suffix.

        Examples:
            ``report.pdf``        → ``report.pdf``
            ``report.pdf`` (dup)  → ``report_1.pdf``
            ``report_1.pdf`` (dup) → ``report_2.pdf``
        """
        if not target.exists():
            return target

        stem: str = target.stem
        suffix: str = target.suffix
        parent: Path = target.parent
        counter: int = 1

        while True:
            candidate: Path = parent / f"{stem}_{counter}{suffix}"
            if not candidate.exists():
                return candidate
            counter += 1
