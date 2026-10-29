# File Name: schemas.py
# Description: Pydantic schemas for Document Repository and Document Dashboard.
# Created At: 2026-09-27
# Created By: Tam Khang
# Updated At: 2026-10-29
# Updated By: Tam Khang

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator


class DocumentCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Document title")
    subject_id: Optional[UUID] = Field(None, description="Associated subject UUID")
    grade: Optional[str] = Field("12", description="Grade level (10, 11, 12)")
    document_type: Optional[str] = Field("reference", description="Document type: lecture, exam, reference")
    description: Optional[str] = Field(None, description="Optional document summary")
    is_public: Optional[bool] = Field(False, description="Public visibility")


# Values the dashboard buckets and list filters understand; anything else would make counts and filters disagree.
ALLOWED_GRADES = {"10", "11", "12"}
ALLOWED_DOCUMENT_TYPES = {"lecture", "exam", "reference"}


class DocumentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255, description="Document title")
    subject_id: Optional[UUID] = Field(None, description="Associated subject UUID")
    grade: Optional[str] = Field(None, description="Grade level (10, 11, 12)")
    document_type: Optional[str] = Field(None, description="Document type: lecture, exam, reference")
    description: Optional[str] = Field(None, description="Optional document summary")
    status: Optional[str] = Field(None, description="Document status")

    @field_validator("grade")
    @classmethod
    def validate_grade(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_GRADES:
            raise ValueError(f"Invalid grade '{v}'. Allowed grades: {', '.join(sorted(ALLOWED_GRADES))}")
        return v

    @field_validator("document_type")
    @classmethod
    def validate_document_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_DOCUMENT_TYPES:
            raise ValueError(f"Invalid document type '{v}'. Allowed types: {', '.join(sorted(ALLOWED_DOCUMENT_TYPES))}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"Uploaded", "Draft", "Archived"}
        if v.upper() == "DELETED":
            raise ValueError("Cannot set status to DELETED via update. Use DELETE endpoint instead.")
        if v not in allowed:
            raise ValueError(f"Invalid status '{v}'. Allowed statuses: {', '.join(sorted(allowed))}")
        return v


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: UUID
    title: str
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = Field(0, description="File size in bytes")
    subject_id: Optional[UUID] = None
    subject_name: Optional[str] = None
    grade: Optional[str] = "12"
    document_type: Optional[str] = "reference"
    description: Optional[str] = None
    uploaded_by: UUID
    author_name: Optional[str] = None
    download_count: Optional[int] = 0
    status: str = "ACTIVE"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DocumentListOut(BaseModel):
    items: List[DocumentOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class DocumentSubjectStat(BaseModel):
    subject_id: Optional[str] = None
    subject_name: str
    count: int


class DocumentTypeStat(BaseModel):
    document_type: str
    type_label: str
    count: int


class DocumentDashboardOut(BaseModel):
    total_documents: int
    total_downloads: int
    total_storage_bytes: int
    storage_formatted: str
    storage_used_formatted: Optional[str] = None
    by_subject: List[DocumentSubjectStat]
    by_type: List[DocumentTypeStat]
    recent_documents: List[DocumentOut]
