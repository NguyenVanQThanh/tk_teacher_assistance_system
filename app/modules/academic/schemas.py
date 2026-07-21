# File Name: schemas.py
# Description: Pydantic schemas for the academic module (Subject CRUD).
# Created At: 2026-07-21
# Created By: Tam Khang
# Updated At: 2026-07-21
# Updated By: Tam Khang

from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SubjectCreate(BaseModel):
    """Schema for creating a new subject."""
    subject_name: str = Field(..., max_length=100, description="Tên môn học (phải là duy nhất)")
    description: Optional[str] = Field(None, description="Mô tả môn học")


class SubjectUpdate(BaseModel):
    """Schema for updating an existing subject (all fields optional)."""
    subject_name: Optional[str] = Field(None, max_length=100, description="Tên môn học mới")
    description: Optional[str] = Field(None, description="Mô tả mới")


class SubjectOut(BaseModel):
    """Schema for subject response output."""
    subject_id: UUID
    subject_name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
