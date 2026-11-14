# File Name: documents.py
# Description: API Router for Teacher Document Repository & Document Dashboard.
# Created At: 2026-09-27
# Created By: Tam Khang
# Updated At: 2026-11-03
# Updated By: Tam Khang

from typing import Optional
from urllib.parse import quote
from uuid import UUID
from fastapi import BackgroundTasks, APIRouter, Depends, Query, UploadFile, File, Form, status, HTTPException
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import LocalStorage, get_storage
from models.models import User
from app.modules.auth.dependencies import require_roles
from app.modules.document.schemas import DocumentOut, DocumentListOut, DocumentDashboardOut, DocumentUpdate
from app.modules.document.services import document_service
from app.modules.document.services.document_ingest_service import DocumentIngestService
from app.modules.document.services.document_service import DocumentService

# The repository is a teacher resource; students are rejected on every route.
get_current_user = require_roles("Teacher", "HomeroomTeacher", "Admin")

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


def _content_disposition(disposition: str, filename: str) -> str:
    """Build the same Content-Disposition value Starlette's FileResponse uses."""
    encoded = quote(filename)
    if encoded != filename:
        return f"{disposition}; filename*=utf-8''{encoded}"
    return f'{disposition}; filename="{filename}"'


def _document_response(file_url: Optional[str], media_type: str, disposition: str, filename: str) -> Response:
    """Serve a document from the configured storage backend with the requested headers."""
    storage = get_storage()
    key = DocumentService._storage_key(file_url)
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ERR-DOC-NOT_FOUND", "message": "File attachment not found."}
        )

    if isinstance(storage, LocalStorage):
        # Local files stream straight from disk: keeps Range/ETag support (in-browser PDF
        # viewers need Range) and avoids loading a 50 MB file into the API process.
        path = storage.path_for(key)
        if not path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ERR-DOC-NOT_FOUND", "message": "File attachment not found."}
            )
        return FileResponse(
            path=path,
            filename=filename,
            media_type=media_type,
            content_disposition_type=disposition,
        )

    try:
        data = DocumentService.read_file_bytes(file_url)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ERR-DOC-NOT_FOUND", "message": "File attachment not found."}
        )
    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": _content_disposition(disposition, filename)},
    )


@router.get("/dashboard", response_model=DocumentDashboardOut)
def get_document_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve document repository statistics and real metrics for the dashboard.
    """
    return DocumentService.get_document_dashboard(db=db, current_user=current_user)


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Uploaded document file (.pdf, .docx, .xlsx)"),
    title: str = Form(..., description="Document title"),
    subject_id: Optional[UUID] = Form(None, description="Subject UUID"),
    grade: Optional[str] = Form("12", description="Target grade"),
    document_type: Optional[str] = Form("reference", description="Type: lecture, exam, reference"),
    description: Optional[str] = Form(None, description="Optional description"),
    is_public: Optional[bool] = Form(False, description="Public status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a new teaching document with metadata.
    """
    out = DocumentService.upload_document(
        db=db,
        current_user=current_user,
        file=file,
        title=title,
        subject_id=subject_id,
        grade=grade,
        document_type=document_type,
        description=description,
        is_public=is_public
    )
    # Ingestion runs after the response with its own DB session.
    background_tasks.add_task(DocumentIngestService.ingest, out.document_id)
    return out


@router.post("/{document_id}/ingest", response_model=DocumentOut, status_code=status.HTTP_202_ACCEPTED)
def reingest_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Re-trigger content ingestion (owner or admin only).
    """
    doc = DocumentService.trigger_ingest(db, document_id, current_user)
    background_tasks.add_task(DocumentIngestService.ingest, document_id)
    return DocumentService.to_document_out(doc, db)


@router.get("", response_model=DocumentListOut)
def list_documents(
    subject_id: Optional[UUID] = Query(None, description="Filter by subject"),
    grade: Optional[str] = Query(None, description="Filter by grade"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    search: Optional[str] = Query(None, description="Search query"),
    status: Optional[str] = Query("Uploaded", description="Filter by status, or ALL for every non-deleted status"),
    mine: bool = Query(False, description="Only documents uploaded by the current user"),
    ready_only: bool = Query(False, description="Only documents whose ingest_status is DONE"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List documents with multi-criteria filtering and pagination.
    """
    return DocumentService.list_documents(
        db=db,
        current_user=current_user,
        subject_id=subject_id,
        grade=grade,
        document_type=document_type,
        search=search,
        status_val=status,
        mine=mine,
        ready_only=ready_only,
        page=page,
        page_size=page_size
    )


@router.get("/{document_id}", response_model=DocumentOut)
def get_document_detail(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve single document detail by document_id with access control.
    """
    return DocumentService.get_document_detail(db, document_id, current_user)


@router.put("/{document_id}", response_model=DocumentOut)
def update_document(
    document_id: UUID,
    payload: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update document metadata (title, subject_id, grade, document_type, description, status).
    """
    return DocumentService.update_document(db, document_id, payload, current_user)


@router.get("/{document_id}/view")
def view_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Stream document file for inline viewing (PDF/doc preview) without incrementing download counter.
    """
    doc = DocumentService.get_document_by_id(db, document_id)
    DocumentService.check_document_access(db, doc, current_user, requires_ownership=False)

    ext = (doc.file_type or "").lower()
    media_type = "application/pdf" if ext == "pdf" else "application/octet-stream"
    if ext in ["png", "jpg", "jpeg"]:
        media_type = f"image/{ext}"
    # Only PDF/images are safe to render inline; everything else is offered as attachment.
    disposition = "inline" if media_type != "application/octet-stream" else "attachment"

    return _document_response(
        doc.file_url,
        media_type=media_type,
        disposition=disposition,
        filename=f"{doc.title}.{doc.file_type or 'pdf'}",
    )


@router.get("/{document_id}/download")
def download_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download a document file stream and increment real download counter after access check.
    """
    doc = DocumentService.get_document_by_id(db, document_id)
    DocumentService.check_document_access(db, doc, current_user, requires_ownership=False)
    # Verify the file exists before counting so a missing file never yields a bogus download.
    if not DocumentService.file_exists(doc.file_url):
        raise HTTPException(status_code=404, detail="File attachment not found.")
    doc = DocumentService.record_download(db, document_id, current_user)

    return _document_response(
        doc.file_url,
        media_type="application/octet-stream",
        disposition="attachment",
        filename=f"{doc.title}.{doc.file_type or 'pdf'}",
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Soft delete a document (sets status to DELETED).
    """
    DocumentService.delete_document(db, document_id, current_user)


@router.post("/{document_id}/restore", response_model=DocumentOut)
def restore_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Restore a soft-deleted document back to Uploaded status.
    """
    return DocumentService.restore_document(db, document_id, current_user)
