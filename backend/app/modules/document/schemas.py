# File Name: schemas.py
# Description: Pydantic schemas for Document Repository and Document Dashboard.
# Created At: 2026-09-27
# Created By: Tam Khang
# Updated At: 2026-10-28
# Updated By: Tam Khang

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class DocumentCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Document title")
    subject_id: Optional[UUID] = Field(None, description="Associated subject UUID")
    grade: Optional[str] = Field("12", description="Grade level (10, 11, 12)")
    document_type: Optional[str] = Field("reference", description="Document type: lecture, exam, reference")
    description: Optional[str] = Field(None, description="Optional document summary")
    is_public: Optional[bool] = Field(False, description="Public visibility")


class DocumentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255, description="Document title")
    subject_id: Optional[UUID] = Field(None, description="Associated subject UUID")
    grade: Optional[str] = Field(None, description="Grade level (10, 11, 12)")
    document_type: Optional[str] = Field(None, description="Document type: lecture, exam, reference")
    description: Optional[str] = Field(None, description="Optional document summary")
    status: Optional[str] = Field(None, description="Document status")


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
