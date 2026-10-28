# File Name: documents.py
# Description: API Router for Teacher Document Repository & Document Dashboard.
# Created At: 2026-09-27
# Created By: Tam Khang
# Updated At: 2026-10-28
# Updated By: Tam Khang

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, status, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from app.core.database import get_db
from models.models import User
from app.modules.auth.dependencies import get_current_user
from app.modules.document.schemas import DocumentOut, DocumentListOut, DocumentDashboardOut, DocumentUpdate
from app.modules.document.services import document_service
from app.modules.document.services.document_service import DocumentService, UPLOAD_DIR

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


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
    return DocumentService.upload_document(
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


@router.get("", response_model=DocumentListOut)
def list_documents(
    subject_id: Optional[UUID] = Query(None, description="Filter by subject"),
    grade: Optional[str] = Query(None, description="Filter by grade"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    search: Optional[str] = Query(None, description="Search query"),
    status: Optional[str] = Query("Uploaded", description="Filter by status or ALL"),
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
        subject_id=subject_id,
        grade=grade,
        document_type=document_type,
        search=search,
        status_val=status,
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
    Retrieve single document detail by document_id.
    """
    return DocumentService.get_document_detail(db, document_id)


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


@router.get("/{document_id}/download")
def download_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download a document file stream and increment real download counter.
    """
    doc = DocumentService.record_download(db, document_id)
    if not doc.file_url:
        raise HTTPException(status_code=404, detail="File attachment not found.")

    file_name = Path(doc.file_url).name
    file_path = UPLOAD_DIR / file_name

    if not file_path.exists():
        return {
            "document_id": doc.document_id,
            "title": doc.title,
            "file_url": doc.file_url,
            "download_count": doc.download_count,
            "message": "File download initiated."
        }

    return FileResponse(
        path=file_path,
        filename=f"{doc.title}.{doc.file_type or 'pdf'}",
        media_type="application/octet-stream"
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
