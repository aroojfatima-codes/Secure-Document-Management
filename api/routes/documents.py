"""Document API routes: upload, list, detail, download, share, delete."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse

from api.deps import clear_session, get_current_user, set_session
from api.models import (
    DocumentDetailResponse,
    DocumentListResponse,
    MessageResponse,
    RevokeShareRequest,
    ShareRequest,
    ShareResponse,
    UploadResponse,
)
from database.exceptions import DocumentNotFoundError
from crypto.exceptions import IntegrityCheckError
from exceptions.custom_exceptions import (
    FileHandlingError,
    SDMSException,
    ValidationError,
)
from logger.logging_config import get_logger
from models.audit import (
    AuditAction,
    OperationStatus,
    ResourceType,
    SeverityLevel,
)
from models.user import User
from services.audit_service import AuditService
from services.document_download_service import DocumentDownloadService
from services.document_listing_service import DocumentListingService
from services.document_service import DocumentUploadService
from services.document_sharing_service import DocumentSharingService

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

_audit_svc = AuditService()

# Roles allowed to upload, share, and delete documents
_EDITOR_ROLES = {"admin", "editor"}


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _require_editor_role(current_user: dict[str, Any]) -> None:
    """Raise 403 if the current user is not admin or editor."""
    if current_user.get("role", "") not in _EDITOR_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires admin or editor privileges.",
        )

def _format_audit_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    size: float = float(size_bytes)
    for unit in ("KB", "MB", "GB"):
        size /= 1024.0
        if size < 1024:
            return f"{size:.1f} {unit}"
    return f"{size:.1f} TB"


# ------------------------------------------------------------------
# Upload
# ------------------------------------------------------------------

@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_document(
    file: UploadFile,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Upload, encrypt, and store a document (admin/editor only)."""
    _require_editor_role(current_user)
    user: User = current_user["_user"]
    set_session(user)

    tmp_path: Path | None = None
    try:
        suffix = Path(file.filename or "upload").suffix
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=suffix, dir=str(Path("storage/temp").resolve())
        ) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = Path(tmp.name)

        upload_svc = DocumentUploadService()
        result: dict[str, Any] = upload_svc.upload(str(tmp_path))

        _audit_svc.log_event(
            action=AuditAction.DOCUMENT_UPLOAD.value,
            resource_type=ResourceType.DOCUMENT.value,
            resource_id=result["document_id"],
            resource_name=result["original_filename"],
            status=OperationStatus.SUCCESS.value,
            message=f"Document '{result['original_filename']}' uploaded via API.",
            severity=SeverityLevel.INFO.value,
            metadata={
                "file_size": result["file_size"],
                "mime_type": result.get("mime_type", ""),
            },
        )

        return {
            "success": True,
            "document_id": result["document_id"],
            "original_filename": result["original_filename"],
            "file_size": result["file_size"],
            "sha256_hash": result["sha256_hash"],
            "message": "Document uploaded and encrypted successfully.",
        }
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except SDMSException as exc:
        logger.error("Upload failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {exc}",
        ) from exc
    finally:
        clear_session()
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


# ------------------------------------------------------------------
# List my documents
# ------------------------------------------------------------------

@router.get("", response_model=DocumentListResponse)
def list_documents(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """List documents owned by the current user."""
    user: User = current_user["_user"]
    set_session(user)
    try:
        listing_svc = DocumentListingService()
        result = listing_svc.list_my_documents(page=page, per_page=per_page)
        return {
            "success": True,
            "documents": result["documents"],
            "pagination": result["pagination"],
        }
    except SDMSException as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    finally:
        clear_session()


# ------------------------------------------------------------------
# List shared with me
# ------------------------------------------------------------------

@router.get("/shared", response_model=DocumentListResponse)
def list_shared_documents(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """List documents shared with the current user."""
    user: User = current_user["_user"]
    set_session(user)
    try:
        listing_svc = DocumentListingService()
        result = listing_svc.list_shared_with_me(page=page, per_page=per_page)
        return {
            "success": True,
            "documents": result["documents"],
            "pagination": result["pagination"],
        }
    except SDMSException as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    finally:
        clear_session()


# ------------------------------------------------------------------
# Document detail
# ------------------------------------------------------------------

@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(
    document_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Get metadata for a single document."""
    user: User = current_user["_user"]
    set_session(user)
    try:
        listing_svc = DocumentListingService()
        doc_info = listing_svc.get_document_detail(document_id)
        return {"success": True, "document": doc_info}
    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except SDMSException as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    finally:
        clear_session()


# ------------------------------------------------------------------
# Download (decrypt)
# ------------------------------------------------------------------

@router.get("/{document_id}/download")
def download_document(
    document_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> StreamingResponse:
    """Download and decrypt a document, returning the original file."""
    user: User = current_user["_user"]
    set_session(user)
    try:
        from database.repositories.document_repository import DocumentRepository

        doc_repo = DocumentRepository()
        doc = doc_repo.get_by_document_id(document_id)
        if doc is None:
            raise DocumentNotFoundError(f"Document '{document_id}' not found.")

        download_svc = DocumentDownloadService()
        tmp_dir = tempfile.mkdtemp()
        result = download_svc.download(
            document_id=document_id, output_dir=tmp_dir
        )

        _audit_svc.log_event(
            action=AuditAction.DOCUMENT_DOWNLOAD.value,
            resource_type=ResourceType.DOCUMENT.value,
            resource_id=result["document_id"],
            resource_name=result["original_filename"],
            status=OperationStatus.SUCCESS.value,
            message=f"Document '{result['original_filename']}' downloaded via API.",
            severity=SeverityLevel.INFO.value,
        )

        output_path = Path(result["output_path"])

        def iter_file():
            with open(output_path, "rb") as f:
                yield from f
            output_path.unlink(missing_ok=True)

        return StreamingResponse(
            iter_file(),
            media_type=doc.mime_type or "application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{doc.original_filename}"'
            },
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except IntegrityCheckError as exc:
        _audit_svc.log_event(
            action=AuditAction.INTEGRITY_FAILURE.value,
            resource_type=ResourceType.DOCUMENT.value,
            resource_id=document_id,
            status=OperationStatus.FAILURE.value,
            message=f"Integrity check failed for '{document_id}'.",
            severity=SeverityLevel.CRITICAL.value,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except (FileHandlingError, SDMSException) as exc:
        logger.error("Download failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {exc}",
        ) from exc
    finally:
        clear_session()


# ------------------------------------------------------------------
# Share
# ------------------------------------------------------------------

@router.post("/{document_id}/share", response_model=ShareResponse)
def share_document(
    document_id: str,
    body: ShareRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Share a document with another user via RSA key re-encryption (admin/editor only)."""
    _require_editor_role(current_user)
    user: User = current_user["_user"]
    set_session(user)
    try:
        sharing_svc = DocumentSharingService()
        result = sharing_svc.share_document(
            document_id=document_id,
            recipient_username=body.recipient_username.strip(),
        )
        _audit_svc.log_event(
            action=AuditAction.DOCUMENT_SHARE.value,
            resource_type=ResourceType.SHARING.value,
            resource_id=result["document_id"],
            resource_name=result["recipient_username"],
            status=OperationStatus.SUCCESS.value,
            message=(
                f"Document '{result['document_id']}' shared with "
                f"'{result['recipient_username']}' via API."
            ),
            severity=SeverityLevel.INFO.value,
        )
        return {
            "success": True,
            "document_id": result["document_id"],
            "recipient_user_id": result["recipient_user_id"],
            "recipient_username": result["recipient_username"],
            "permission": result["permission"],
            "message": f"Document shared with '{result['recipient_username']}'.",
        }
    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except SDMSException as exc:
        logger.error("Share failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Share failed: {exc}",
        ) from exc
    finally:
        clear_session()


# ------------------------------------------------------------------
# Revoke share
# ------------------------------------------------------------------

@router.post("/{document_id}/revoke", response_model=MessageResponse)
def revoke_share(
    document_id: str,
    body: RevokeShareRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Revoke a previously granted share (admin/editor only)."""
    _require_editor_role(current_user)
    user: User = current_user["_user"]
    set_session(user)
    try:
        sharing_svc = DocumentSharingService()
        result = sharing_svc.revoke_share(
            document_id=document_id,
            recipient_user_id=body.recipient_user_id.strip(),
        )
        _audit_svc.log_event(
            action=AuditAction.DOCUMENT_SHARE.value,
            resource_type=ResourceType.SHARING.value,
            resource_id=result["document_id"],
            resource_name=result["recipient_user_id"],
            status=OperationStatus.SUCCESS.value,
            message=(
                f"Share revoked for document '{result['document_id']}' "
                f"— user '{result['recipient_user_id']}' via API."
            ),
            severity=SeverityLevel.INFO.value,
        )
        return {
            "success": True,
            "message": (
                f"Access revoked for user "
                f"'{result['recipient_user_id']}'."
            ),
        }
    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except SDMSException as exc:
        logger.error("Revoke failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Revoke failed: {exc}",
        ) from exc
    finally:
        clear_session()


# ------------------------------------------------------------------
# Delete (soft)
# ------------------------------------------------------------------

@router.delete("/{document_id}", status_code=200)
def delete_document(
    document_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Soft-delete a document (owner or admin only, admin/editor role required)."""
    _require_editor_role(current_user)
    user: User = current_user["_user"]
    set_session(user)
    try:
        from database.repositories.document_repository import DocumentRepository

        doc_repo = DocumentRepository()
        doc = doc_repo.get_by_document_id(document_id)
        if doc is None:
            raise DocumentNotFoundError(f"Document '{document_id}' not found.")
        if doc.owner_id != user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the document owner can delete it.",
            )

        doc_repo.soft_delete_document(document_id)

        _audit_svc.log_event(
            action=AuditAction.DOCUMENT_SHARE.value,
            resource_type=ResourceType.DOCUMENT.value,
            resource_id=document_id,
            resource_name=doc.original_filename,
            status=OperationStatus.SUCCESS.value,
            message=f"Document '{document_id}' soft-deleted via API.",
            severity=SeverityLevel.INFO.value,
        )

        return {
            "success": True,
            "message": f"Document '{document_id}' deleted.",
        }
    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except SDMSException as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    finally:
        clear_session()
