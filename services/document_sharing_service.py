"""Document sharing service — securely shares encrypted documents via
key re-encryption (hybrid encryption key distribution).

The document's AES-256 key is unwrapped using the owner's RSA private
key, then re-wrapped with the recipient's RSA public key.  The
recipient-specific encrypted key is stored in the document's ACL
(``shared_with`` list).  The encrypted document on disk is never
touched.
"""

from __future__ import annotations

from typing import Any

from crypto.base64_utils import b64_decode, b64_encode
from crypto.rsa_cipher import RSACipher
from database.exceptions import DocumentNotFoundError, UserNotFoundError
from database.repositories.document_repository import DocumentRepository
from database.repositories.user_repository import UserRepository
from exceptions.custom_exceptions import ValidationError
from logger.logging_config import get_logger
from models.document import Document
from services.session_manager import SessionManager

logger = get_logger(__name__)


class DocumentSharingService:
    """Coordinates secure document sharing via key re-encryption.

    Usage::

        svc = DocumentSharingService()
        result = svc.share_document(
            document_id="abc...",
            recipient_username="alice",
        )
    """

    def __init__(self) -> None:
        self._session_mgr: SessionManager = SessionManager()
        self._doc_repo: DocumentRepository = DocumentRepository()
        self._user_repo: UserRepository = UserRepository()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def share_document(
        self, document_id: str, recipient_username: str
    ) -> dict[str, Any]:
        """Share a document with another registered user.

        The sharing flow:

        1. Verify an active authenticated session exists.
        2. Retrieve the document from MongoDB.
        3. Confirm the current user is the document owner.
        4. Look up the recipient by username.
        5. Validate the recipient is not the owner and does not
           already have access.
        6. Decrypt the document's AES-256 key using the owner's
           RSA private key.
        7. Re-encrypt the AES key using the recipient's RSA
           public key.
        8. Append a ``SharedUser`` entry to the document's ACL.
        9. Persist the updated ACL to MongoDB.

        Args:
            document_id:       The UUID4 hex document identifier.
            recipient_username: The username of the target user.

        Returns:
            A dict with sharing metadata::

                {
                    "document_id": "...",
                    "recipient_user_id": "...",
                    "recipient_username": "...",
                    "permission": "view",
                }

        Raises:
            AuthenticationError: If no session is active.
            DocumentNotFoundError: If the document does not exist or
                the user is not the owner.
            UserNotFoundError: If the recipient does not exist.
            ValidationError: If the recipient is the owner or already
                has access.
            SDMSException: On any other failure.
        """
        session = self._session_mgr.get_current_session()

        if not document_id or not document_id.strip():
            raise ValidationError("Document ID is required.")
        if not recipient_username or not recipient_username.strip():
            raise ValidationError("Recipient username is required.")

        doc: Document | None = self._doc_repo.get_by_document_id(
            document_id
        )
        if doc is None:
            raise DocumentNotFoundError(
                f"Document '{document_id}' not found."
            )

        if doc.owner_id != session.user_id:
            raise DocumentNotFoundError(
                f"Document '{document_id}' not found."
            )

        recipient = self._user_repo.get_by_username(
            recipient_username.strip()
        )
        if recipient is None:
            raise UserNotFoundError(
                f"User '{recipient_username}' not found."
            )

        if recipient.user_id == session.user_id:
            raise ValidationError(
                "Cannot share a document with yourself."
            )

        for entry in doc.shared_with:
            if entry.user_id == recipient.user_id:
                raise ValidationError(
                    f"Document is already shared with "
                    f"'{recipient_username}'."
                )

        logger.info(
            "Sharing document '%s' with user '%s' (%s).",
            document_id,
            recipient_username,
            recipient.user_id,
        )

        rsa_cipher: RSACipher = RSACipher()
        rsa_cipher.load_private_key(
            session.rsa_private_key.encode("utf-8")
        )
        encrypted_aes_key_bytes: bytes = b64_decode(
            doc.encrypted_aes_key
        )
        aes_key: bytes = rsa_cipher.decrypt(encrypted_aes_key_bytes)
        logger.debug("AES key recovered for re-encryption.")

        rsa_cipher.load_public_key(
            recipient.rsa_public_key.encode("utf-8")
        )
        re_encrypted_key: bytes = rsa_cipher.encrypt(aes_key)
        re_encrypted_b64: str = b64_encode(re_encrypted_key)
        logger.debug(
            "AES key re-encrypted with recipient's public key."
        )

        doc.add_share(
            user_id=recipient.user_id,
            permission="view",
            encrypted_aes_key=re_encrypted_b64,
        )

        self._doc_repo.update_document(
            document_id,
            {"shared_with": [sw.to_dict() for sw in doc.shared_with]},
        )

        logger.info(
            "Document '%s' shared with user '%s'.",
            document_id,
            recipient_username,
        )

        return {
            "document_id": doc.document_id,
            "recipient_user_id": recipient.user_id,
            "recipient_username": recipient_username,
            "permission": "view",
        }
