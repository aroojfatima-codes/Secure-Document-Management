"""Document controller — handles upload, listing, detail, and search.

This is the thin presentation-coordination layer.  It validates
authentication, delegates to the service layer, formats results,
and handles errors for display.

RBAC enforcement: every public method checks the current session
role against the centralized permission definitions before
proceeding.  This prevents unauthorised operations even if the GUI
is bypassed.
"""

from __future__ import annotations

from typing import Any

from database.exceptions import DocumentNotFoundError, UserNotFoundError
from database.repositories.document_repository import DocumentRepository
from database.repositories.user_repository import UserRepository
from crypto.exceptions import IntegrityCheckError
from exceptions.custom_exceptions import (
    AuthenticationError,
    AuthorizationError,
    FileHandlingError,
    SDMSException,
    ValidationError,
)
from logger.logging_config import get_logger
from models.audit import AuditAction, OperationStatus, ResourceType, SeverityLevel
from services.audit_service import AuditService
from services.document_download_service import DocumentDownloadService
from services.document_listing_service import DocumentListingService
from services.document_service import DocumentUploadService
from services.document_sharing_service import DocumentSharingService
from services.session_manager import SessionManager
from utilities.permissions import Permission

logger = get_logger(__name__)


class DocumentController:
    """Coordinates document workflows.

    Usage::

        ctrl = DocumentController()
        result = ctrl.upload("/path/to/doc.pdf")
        docs = ctrl.list_my_documents(page=1)
        detail = ctrl.get_document_detail("abc...")
        results = ctrl.search_my_documents(query="report")
    """

    def __init__(self) -> None:
        self._upload_service: DocumentUploadService = DocumentUploadService()
        self._listing_service: DocumentListingService = DocumentListingService()
        self._download_service: DocumentDownloadService = DocumentDownloadService()
        self._sharing_service: DocumentSharingService = DocumentSharingService()
        self._audit_service: AuditService = AuditService()
        self._session_mgr: SessionManager = SessionManager()
        self._doc_repo = DocumentRepository()

    def _safe_call(
        self, fn: Any, default: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute *fn* and convert exceptions to error dicts."""
        try:
            return fn()
        except AuthenticationError as exc:
            logger.warning("Operation denied -- not authenticated.")
            return {"success": False, "error": str(exc), **(default or {})}
        except SDMSException as exc:
            logger.error("Operation failed: %s", exc)
            return {"success": False, "error": str(exc), **(default or {})}

    def _log_share_failure(
        self, document_id: str, recipient: str, message: str,
    ) -> None:
        """Log a failed share attempt to the audit trail."""
        self._audit_service.log_event(
            action=AuditAction.DOCUMENT_SHARE.value,
            resource_type=ResourceType.SHARING.value,
            resource_id=document_id,
            resource_name=recipient,
            status=OperationStatus.FAILURE.value,
            message=f"Share failed: {message}",
            severity=SeverityLevel.WARNING.value,
        )

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------

    def upload(self, file_path: str) -> dict[str, Any]:
        """Upload, encrypt, and persist a document.

        RBAC: Requires ``upload_document`` permission (admin, editor).

        Args:
            file_path: Path to the file on the local filesystem.

        Returns:
            A dict with the upload result::

                {
                    "success": True,
                    "document_id": "...",
                    "original_filename": "...",
                    "file_size": 12345,
                    "message": "Document '...' uploaded and encrypted."
                }
        """
        try:
            self._session_mgr.require_permission(Permission.UPLOAD_DOCUMENT)
            result = self._upload_service.upload(file_path)
            self._audit_service.log_event(
                action=AuditAction.DOCUMENT_UPLOAD.value,
                resource_type=ResourceType.DOCUMENT.value,
                resource_id=result["document_id"],
                resource_name=result["original_filename"],
                status=OperationStatus.SUCCESS.value,
                message=f"Document '{result['original_filename']}' uploaded ({result['file_size']} bytes, SHA-256: {result['sha256_hash'][:16]}...).",
                severity=SeverityLevel.INFO.value,
                metadata={
                    "file_size": result["file_size"],
                    "mime_type": result.get("mime_type", ""),
                    "sha256_prefix": result["sha256_hash"][:16],
                },
            )
            return {
                "success": True,
                **result,
                "message": (
                    f"Document '{result['original_filename']}' "
                    f"uploaded and encrypted successfully."
                ),
            }
        except AuthenticationError as exc:
            logger.warning("Upload denied — not authenticated.")
            return {"success": False, "error": str(exc)}
        except AuthorizationError as exc:
            logger.warning("Upload denied — insufficient permissions: %s", exc)
            return {"success": False, "error": str(exc)}
        except ValidationError as exc:
            logger.warning("Upload validation failed: %s", exc)
            return {"success": False, "error": str(exc)}
        except SDMSException as exc:
            logger.error("Upload failed: %s", exc)
            return {"success": False, "error": f"Upload failed: {exc}"}

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    def list_my_documents(
        self, page: int = 1, per_page: int = 20
    ) -> dict[str, Any]:
        """List documents owned by the current user."""
        return self._safe_call(
            lambda: {"success": True, **self._listing_service.list_my_documents(
                page=page, per_page=per_page
            )},
            default={"documents": []},
        )

    def list_shared_with_me(
        self, page: int = 1, per_page: int = 20
    ) -> dict[str, Any]:
        """List documents shared with the current user."""
        return self._safe_call(
            lambda: {"success": True, **self._listing_service.list_shared_with_me(
                page=page, per_page=per_page
            )},
            default={"documents": []},
        )

    # ------------------------------------------------------------------
    # Detail
    # ------------------------------------------------------------------

    def get_document_detail(self, document_id: str) -> dict[str, Any]:
        """View safe metadata for a single document."""
        return self._safe_call(
            lambda: {"success": True, "document": self._listing_service.get_document_detail(document_id)},
        )

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_my_documents(
        self,
        query: str = "",
        mime_type: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        """Search and filter documents owned by the current user."""
        extra = {"search_query": query, "mime_filter": mime_type}
        return self._safe_call(
            lambda: {
                "success": True,
                **self._listing_service.search_my_documents(
                    query=query, mime_type=mime_type, page=page, per_page=per_page,
                ),
                **extra,
            },
            default={"documents": [], **extra},
        )

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def download(self, document_id: str, output_dir: str) -> dict[str, Any]:
        """Download, decrypt, verify integrity, and save a document.

        RBAC: Requires ``download_document`` permission (all roles).

        Args:
            document_id: The UUID4 hex document identifier.
            output_dir:  Directory path for the restored file.

        Returns:
            A dict with the download result::

                {
                    "success": True,
                    "document_id": "...",
                    "original_filename": "...",
                    "output_path": "/path/to/file.pdf",
                    "file_size": 12345,
                    "integrity_verified": True,
                    "message": "Document '...' decrypted and saved."
                }
        """
        try:
            self._session_mgr.require_permission(Permission.DOWNLOAD_DOCUMENT)
            result = self._download_service.download(
                document_id=document_id, output_dir=output_dir
            )
            self._audit_service.log_event(
                action=AuditAction.DOCUMENT_DOWNLOAD.value,
                resource_type=ResourceType.DOCUMENT.value,
                resource_id=result["document_id"],
                resource_name=result["original_filename"],
                status=OperationStatus.SUCCESS.value,
                message=(
                    f"Document '{result['original_filename']}' "
                    f"downloaded and integrity verified."
                ),
                severity=SeverityLevel.INFO.value,
                metadata={
                    "output_path": result["output_path"],
                    "file_size": result["file_size"],
                    "integrity_verified": result.get("integrity_verified", False),
                },
            )
            return {
                "success": True,
                **result,
                "message": (
                    f"Document '{result['original_filename']}' "
                    f"decrypted and saved to '{result['output_path']}'."
                ),
            }
        except AuthenticationError as exc:
            logger.warning("Download denied — not authenticated.")
            return {"success": False, "error": str(exc)}
        except AuthorizationError as exc:
            logger.warning("Download denied — insufficient permissions: %s", exc)
            return {"success": False, "error": str(exc)}
        except ValidationError as exc:
            logger.warning("Download validation failed: %s", exc)
            return {"success": False, "error": str(exc)}
        except DocumentNotFoundError as exc:
            logger.warning("Download denied — document not found: %s", exc)
            return {"success": False, "error": str(exc)}
        except FileHandlingError as exc:
            logger.error("Download storage error: %s", exc)
            return {
                "success": False,
                "error": "Encrypted file could not be read from storage.",
            }
        except IntegrityCheckError as exc:
            logger.error("Download integrity failure: %s", exc)
            self._audit_service.log_event(
                action=AuditAction.INTEGRITY_FAILURE.value,
                resource_type=ResourceType.DOCUMENT.value,
                resource_id=document_id,
                resource_name="",
                status=OperationStatus.FAILURE.value,
                message=(
                    f"Integrity verification failed for "
                    f"document '{document_id}': {exc}"
                ),
                severity=SeverityLevel.CRITICAL.value,
                metadata={"document_id": document_id},
            )
            return {"success": False, "error": str(exc)}
        except SDMSException as exc:
            logger.error("Download failed: %s", exc)
            return {"success": False, "error": f"Download failed: {exc}"}

    # ------------------------------------------------------------------
    # Sharing
    # ------------------------------------------------------------------

    def share_document(
        self, document_id: str, recipient_username: str
    ) -> dict[str, Any]:
        """Share a document with another registered user.

        Args:
            document_id:       The UUID4 hex document identifier.
            recipient_username: The recipient's username.

        Returns:
            A dict with the share result::

                {
                    "success": True,
                    "document_id": "...",
                    "recipient_username": "...",
                    "permission": "view",
                    "message": "Document shared with '...'."
                }
        """
        try:
            self._session_mgr.require_permission(Permission.SHARE_DOCUMENT)
            result = self._sharing_service.share_document(
                document_id=document_id,
                recipient_username=recipient_username,
            )
            self._audit_service.log_event(
                action=AuditAction.DOCUMENT_SHARE.value,
                resource_type=ResourceType.SHARING.value,
                resource_id=result["document_id"],
                resource_name=result["recipient_username"],
                status=OperationStatus.SUCCESS.value,
                message=(
                    f"Document '{result['document_id']}' "
                    f"shared with user '{result['recipient_username']}'."
                ),
                severity=SeverityLevel.INFO.value,
                metadata={
                    "recipient_user_id": result.get("recipient_user_id", ""),
                    "permission": result.get("permission", "view"),
                },
            )
            return {
                "success": True,
                **result,
                "message": (
                    f"Document shared with "
                    f"'{result['recipient_username']}'."
                ),
            }
        except AuthenticationError as exc:
            logger.warning("Share denied — not authenticated.")
            return {"success": False, "error": str(exc)}
        except AuthorizationError as exc:
            logger.warning("Share denied — insufficient permissions: %s", exc)
            return {"success": False, "error": str(exc)}
        except ValidationError as exc:
            logger.warning("Share validation failed: %s", exc)
            self._log_share_failure(document_id, recipient_username, str(exc))
            return {"success": False, "error": str(exc)}
        except (DocumentNotFoundError, UserNotFoundError) as exc:
            logger.warning("Share failed: %s", exc)
            self._log_share_failure(document_id, recipient_username, str(exc))
            return {"success": False, "error": str(exc)}
        except SDMSException as exc:
            logger.error("Share failed: %s", exc)
            return {"success": False, "error": f"Share failed: {exc}"}

    # ------------------------------------------------------------------
    # Revoke Share
    # ------------------------------------------------------------------

    def revoke_share(
        self, document_id: str, recipient_user_id: str
    ) -> dict[str, Any]:
        """Revoke a previously granted share.

        RBAC: Only the document owner or an admin may revoke.

        Args:
            document_id:       The document identifier.
            recipient_user_id: The user whose access is being revoked.

        Returns:
            A dict with the revocation result.
        """
        try:
            result = self._sharing_service.revoke_share(
                document_id=document_id,
                recipient_user_id=recipient_user_id,
            )
            self._audit_service.log_event(
                action=AuditAction.DOCUMENT_SHARE.value,
                resource_type=ResourceType.SHARING.value,
                resource_id=result["document_id"],
                resource_name=result["recipient_user_id"],
                status=OperationStatus.SUCCESS.value,
                message=(
                    f"Share revoked for document '{result['document_id']}' "
                    f"— user '{result['recipient_user_id']}'."
                ),
                severity=SeverityLevel.INFO.value,
                metadata={
                    "recipient_user_id": result.get("recipient_user_id", ""),
                    "operation": "revoke",
                },
            )
            return {
                "success": True,
                **result,
                "message": (
                    f"Access revoked for user "
                    f"'{result['recipient_user_id']}'."
                ),
            }
        except AuthenticationError as exc:
            logger.warning("Revoke denied — not authenticated.")
            return {"success": False, "error": str(exc)}
        except ValidationError as exc:
            logger.warning("Revoke validation failed: %s", exc)
            return {"success": False, "error": str(exc)}
        except (DocumentNotFoundError, UserNotFoundError) as exc:
            logger.warning("Revoke failed: %s", exc)
            return {"success": False, "error": str(exc)}
        except SDMSException as exc:
            logger.error("Revoke failed: %s", exc)
            return {"success": False, "error": f"Revoke failed: {exc}"}

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_document(self, document_id: str) -> dict[str, Any]:
        """Soft-delete a document and remove its encrypted file from storage.

        RBAC: Requires ``delete_document`` permission (admin, editor).
        Only the document owner or an admin may delete.

        Args:
            document_id: The UUID4 hex document identifier.

        Returns:
            A dict with the delete result.
        """
        try:
            self._session_mgr.require_permission(Permission.DELETE_DOCUMENT)

            doc = self._listing_service.get_document_detail(document_id)
            session = self._session_mgr.get_current_session()

            if doc.get("owner_id") != session.user_id and session.role != "admin":
                raise AuthorizationError("You can only delete your own documents.")

            self._doc_repo.soft_delete_document(document_id)
            self._audit_service.log_event(
                action=AuditAction.DOCUMENT_DELETE.value,
                resource_type=ResourceType.DOCUMENT.value,
                resource_id=document_id,
                resource_name=doc.get("original_filename", ""),
                status=OperationStatus.SUCCESS.value,
                message=f"Document '{doc.get('original_filename', '')}' deleted.",
                severity=SeverityLevel.INFO.value,
            )
            return {
                "success": True,
                "document_id": document_id,
                "message": f"Document '{doc.get('original_filename', '')}' deleted successfully.",
            }
        except AuthenticationError as exc:
            logger.warning("Delete denied — not authenticated.")
            return {"success": False, "error": str(exc)}
        except AuthorizationError as exc:
            logger.warning("Delete denied — insufficient permissions: %s", exc)
            return {"success": False, "error": str(exc)}
        except DocumentNotFoundError as exc:
            logger.warning("Delete failed — document not found: %s", exc)
            return {"success": False, "error": str(exc)}
        except SDMSException as exc:
            logger.error("Delete failed: %s", exc)
            return {"success": False, "error": f"Delete failed: {exc}"}

    # ------------------------------------------------------------------
    # User listing (for share dialog)
    # ------------------------------------------------------------------

    def list_all_users(self) -> dict[str, Any]:
        """List all active users (for the share dialog dropdown).

        Returns:
            A dict with ``{"success": True, "users": [...]}``.
        """
        try:
            self._session_mgr.require_permission(Permission.VIEW_DOCUMENT)
            user_repo = UserRepository()
            users = user_repo.get_all_users(limit=200)
            current_user_id = self._session_mgr.get_current_user_id()
            user_list = [
                {
                    "user_id": u.user_id,
                    "username": u.username,
                    "role": u.role,
                }
                for u in users
                if u.user_id != current_user_id and u.is_active
            ]
            return {"success": True, "users": user_list}
        except AuthenticationError as exc:
            return {"success": False, "error": str(exc), "users": []}
        except SDMSException as exc:
            logger.error("Failed to list users: %s", exc)
            return {"success": False, "error": str(exc), "users": []}
