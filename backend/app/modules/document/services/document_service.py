# File Name: document_service.py
# Description: Service layer for Document Repository and Document Dashboard management.
# Created At: 2026-09-27
# Created By: Tam Khang
# Updated At: 2026-10-29
# Updated By: Tam Khang

import math
import uuid
from pathlib import Path
from typing import Optional, List
from uuid import UUID
from fastapi import UploadFile, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.models import Document, Subject, User, Role
from app.modules.document.schemas import (
    DocumentOut, DocumentListOut, DocumentDashboardOut,
    DocumentSubjectStat, DocumentTypeStat, DocumentUpdate
)

UPLOAD_DIR = Path("uploads/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def format_storage_size(bytes_val: int) -> str:
    """Format byte size into human readable string."""
    if bytes_val <= 0:
        return "0 MB"
    if bytes_val < 1024:
        return f"{bytes_val} B"
    if bytes_val < 1024 * 1024:
        return f"{(bytes_val / 1024):.1f} KB"
    if bytes_val < 1024 * 1024 * 1024:
        return f"{(bytes_val / (1024 * 1024)):.1f} MB"
    return f"{(bytes_val / (1024 * 1024 * 1024)):.2f} GB"


class DocumentService:
    @staticmethod
    def check_document_access(db: Session, doc: Document, current_user: User, requires_ownership: bool = False) -> None:
        """Verify user permissions and document access rights."""
        is_owner = doc.uploaded_by == current_user.user_id
        admin_role = db.query(Role).filter(Role.name == "Admin").first()
        is_admin = bool(admin_role and current_user.role_id == admin_role.role_id)

        if requires_ownership and not (is_owner or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "ERR-DOC-PERMISSION_DENIED", "message": "You do not have permission to modify this document."}
            )

        # Only published ("Uploaded") documents are visible to non-owners; Draft, Archived and DELETED stay private.
        if doc.status != "Uploaded" and not (is_owner or is_admin):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ERR-DOC-NOT_FOUND", "message": "Document not found."}
            )

    @staticmethod
    def to_document_out(
        doc: Document,
        db: Session,
        subject_name: Optional[str] = None,
        author_name: Optional[str] = None
    ) -> DocumentOut:
        """Convert Document ORM model to DocumentOut Pydantic schema without DB writes on read."""
        if subject_name is None:
            subj = db.query(Subject).filter(Subject.subject_id == doc.subject_id).first() if doc.subject_id else None
            subject_name = subj.subject_name if subj else "Chung"

        if author_name is None:
            author = db.query(User).filter(User.user_id == doc.uploaded_by).first() if doc.uploaded_by else None
            author_name = author.full_name if author else "Giáo viên"

        size = doc.file_size or 0
        if size == 0 and doc.file_url:
            disk_path = UPLOAD_DIR / Path(doc.file_url).name
            if disk_path.exists():
                size = disk_path.stat().st_size

        return DocumentOut(
            document_id=doc.document_id,
            title=doc.title,
            file_url=doc.file_url,
            file_type=doc.file_type or "pdf",
            file_size=size,
            subject_id=doc.subject_id,
            subject_name=subject_name,
            grade=doc.grade or "12",
            document_type=doc.document_type or "reference",
            description=doc.raw_content,
            uploaded_by=doc.uploaded_by,
            author_name=author_name,
            download_count=doc.download_count or 0,
            status=doc.status,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def upload_document(
        db: Session,
        current_user: User,
        file: UploadFile,
        title: str,
        subject_id: Optional[UUID] = None,
        grade: Optional[str] = "12",
        document_type: Optional[str] = "reference",
        description: Optional[str] = None,
        is_public: Optional[bool] = False
    ) -> DocumentOut:
        """Upload and persist document metadata and file content."""
        if not title or len(title.strip()) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "ERR-DOC-INVALID_TITLE", "message": "Title must be at least 3 characters."}
            )

        file_ext = Path(file.filename).suffix.lower()
        allowed_exts = {".pdf", ".docx", ".xlsx", ".doc", ".xls"}
        if file_ext not in allowed_exts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "ERR-DOC-INVALID_FILE_TYPE", "message": "Allowed file types: .pdf, .docx, .xlsx"}
            )

        stored_filename = f"{uuid.uuid4()}{file_ext}"
        target_path = UPLOAD_DIR / stored_filename

        file_bytes = file.file.read()
        file_size = len(file_bytes)

        if file_size > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "ERR-DOC-FILE_TOO_LARGE", "message": "File exceeds maximum size of 50MB."}
            )

        with open(target_path, "wb") as f:
            f.write(file_bytes)

        doc = Document(
            document_id=uuid.uuid4(),
            uploaded_by=current_user.user_id,
            subject_id=subject_id,
            title=title.strip(),
            file_url=f"/uploads/documents/{stored_filename}",
            file_type=file_ext.replace(".", "").lower(),
            file_size=file_size,
            download_count=0,
            grade=grade or "12",
            document_type=document_type or "reference",
            raw_content=description or "",
            status="Uploaded"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        return DocumentService.to_document_out(doc, db)

    @staticmethod
    def list_documents(
        db: Session,
        current_user: User,
        subject_id: Optional[UUID] = None,
        grade: Optional[str] = None,
        document_type: Optional[str] = None,
        search: Optional[str] = None,
        status_val: Optional[str] = "Uploaded",
        page: int = 1,
        page_size: int = 12
    ) -> DocumentListOut:
        """List documents with filtering, search, and pagination."""
        query = db.query(Document)

        # "ALL" (or empty) means every non-deleted status; DELETED is only listed when explicitly requested.
        if status_val and status_val != "ALL":
            query = query.filter(Document.status == status_val)
        else:
            query = query.filter(Document.status != "DELETED")

        # Non-published documents (Draft, Archived, DELETED) are visible to their owner or an admin only.
        admin_role = db.query(Role).filter(Role.name == "Admin").first()
        is_admin = bool(admin_role and current_user.role_id == admin_role.role_id)
        if not is_admin:
            query = query.filter(
                (Document.status == "Uploaded") | (Document.uploaded_by == current_user.user_id)
            )

        if subject_id:
            query = query.filter(Document.subject_id == subject_id)

        if grade and grade != "all":
            query = query.filter(Document.grade == grade)

        if document_type and document_type != "all":
            query = query.filter(Document.document_type == document_type)

        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.filter(Document.title.ilike(search_pattern))

        total = query.count()
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        offset = (page - 1) * page_size

        docs = query.order_by(Document.created_at.desc()).offset(offset).limit(page_size).all()

        # Batch load subjects and authors to eliminate N+1 queries
        subject_ids = {d.subject_id for d in docs if d.subject_id}
        author_ids = {d.uploaded_by for d in docs if d.uploaded_by}

        subjects = {s.subject_id: s.subject_name for s in db.query(Subject).filter(Subject.subject_id.in_(subject_ids)).all()} if subject_ids else {}
        authors = {u.user_id: u.full_name for u in db.query(User).filter(User.user_id.in_(author_ids)).all()} if author_ids else {}

        items = [
            DocumentService.to_document_out(
                d,
                db,
                subject_name=subjects.get(d.subject_id, "Chung"),
                author_name=authors.get(d.uploaded_by, "Giáo viên")
            )
            for d in docs
        ]

        return DocumentListOut(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    @staticmethod
    def get_document_by_id(db: Session, document_id: UUID) -> Document:
        """Retrieve single document entity."""
        doc = db.query(Document).filter(Document.document_id == document_id).first()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ERR-DOC-NOT_FOUND", "message": "Document not found."}
            )
        return doc

    @staticmethod
    def get_document_detail(db: Session, document_id: UUID, current_user: User) -> DocumentOut:
        """Retrieve single document detail DTO with access validation."""
        doc = DocumentService.get_document_by_id(db, document_id)
        DocumentService.check_document_access(db, doc, current_user, requires_ownership=False)
        return DocumentService.to_document_out(doc, db)

    @staticmethod
    def update_document(
        db: Session,
        document_id: UUID,
        payload: DocumentUpdate,
        current_user: User
    ) -> DocumentOut:
        """Update document metadata and status (ownership verified)."""
        doc = DocumentService.get_document_by_id(db, document_id)
        DocumentService.check_document_access(db, doc, current_user, requires_ownership=True)

        if payload.title is not None:
            if len(payload.title.strip()) < 3:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "ERR-DOC-INVALID_TITLE", "message": "Title must be at least 3 characters."}
                )
            doc.title = payload.title.strip()

        if payload.subject_id is not None:
            doc.subject_id = payload.subject_id

        if payload.grade is not None:
            doc.grade = payload.grade

        if payload.document_type is not None:
            doc.document_type = payload.document_type

        if payload.description is not None:
            doc.raw_content = payload.description

        if payload.status is not None:
            doc.status = payload.status

        db.commit()
        db.refresh(doc)
        return DocumentService.to_document_out(doc, db)

    @staticmethod
    def record_download(db: Session, document_id: UUID, current_user: User) -> Document:
        """Increment document download counter and return entity after access check."""
        doc = DocumentService.get_document_by_id(db, document_id)
        DocumentService.check_document_access(db, doc, current_user, requires_ownership=False)
        # Atomic SQL increment avoids lost updates under concurrent downloads.
        db.query(Document).filter(Document.document_id == document_id).update(
            {Document.download_count: func.coalesce(Document.download_count, 0) + 1},
            synchronize_session=False,
        )
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def delete_document(db: Session, document_id: UUID, current_user: User) -> None:
        """Soft delete document (set status = DELETED, ownership verified)."""
        doc = DocumentService.get_document_by_id(db, document_id)
        DocumentService.check_document_access(db, doc, current_user, requires_ownership=True)
        doc.status = "DELETED"
        db.commit()

    @staticmethod
    def restore_document(db: Session, document_id: UUID, current_user: User) -> DocumentOut:
        """Restore soft-deleted document to Uploaded status (ownership verified)."""
        doc = DocumentService.get_document_by_id(db, document_id)
        DocumentService.check_document_access(db, doc, current_user, requires_ownership=True)
        doc.status = "Uploaded"
        db.commit()
        db.refresh(doc)
        return DocumentService.to_document_out(doc, db)

    @staticmethod
    def get_document_dashboard(db: Session, current_user: Optional[User] = None) -> DocumentDashboardOut:
        """Aggregate real metrics and statistics for Document Repository Dashboard without writes on read."""
        active_docs = db.query(Document).filter(Document.status != "DELETED").all()
        total_documents = len(active_docs)
        total_downloads = sum(d.download_count or 0 for d in active_docs)

        # Calculate actual storage from active documents in-memory
        total_storage_bytes = 0
        for d in active_docs:
            if d.file_size:
                total_storage_bytes += d.file_size
            elif d.file_url:
                disk_path = UPLOAD_DIR / Path(d.file_url).name
                if disk_path.exists():
                    total_storage_bytes += disk_path.stat().st_size

        storage_formatted = format_storage_size(total_storage_bytes)

        # Subject breakdown
        subjects = db.query(Subject).all()
        subject_map = {s.subject_id: s.subject_name for s in subjects}

        subj_counts = {}
        for d in active_docs:
            name = subject_map.get(d.subject_id, "Tài liệu chung")
            subj_counts[name] = subj_counts.get(name, 0) + 1

        by_subject = [
            DocumentSubjectStat(subject_id=str(k), subject_name=k, count=v)
            for k, v in subj_counts.items()
        ]

        # Type breakdown
        type_counts = {"lecture": 0, "exam": 0, "reference": 0}
        type_labels = {
            "lecture": "Giáo án & Bài giảng",
            "exam": "Đề thi & Kiểm tra",
            "reference": "Tài liệu tham khảo"
        }
        for d in active_docs:
            dtype = d.document_type if d.document_type in type_counts else "reference"
            type_counts[dtype] += 1

        by_type = [
            DocumentTypeStat(document_type=k, type_label=type_labels[k], count=v)
            for k, v in type_counts.items()
        ]

        # Recent documents
        recent_docs = db.query(Document).filter(
            Document.status != "DELETED"
        ).order_by(Document.created_at.desc()).limit(5).all()

        author_ids = {d.uploaded_by for d in recent_docs if d.uploaded_by}
        authors = {u.user_id: u.full_name for u in db.query(User).filter(User.user_id.in_(author_ids)).all()} if author_ids else {}

        recent_items = [
            DocumentService.to_document_out(
                d,
                db,
                subject_name=subject_map.get(d.subject_id, "Chung"),
                author_name=authors.get(d.uploaded_by, "Giáo viên")
            )
            for d in recent_docs
        ]

        return DocumentDashboardOut(
            total_documents=total_documents,
            total_downloads=total_downloads,
            total_storage_bytes=total_storage_bytes,
            storage_formatted=storage_formatted,
            storage_used_formatted=storage_formatted,
            by_subject=by_subject,
            by_type=by_type,
            recent_documents=recent_items
        )
