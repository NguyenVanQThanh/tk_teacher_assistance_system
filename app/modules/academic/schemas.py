# File Name: schemas.py
# Description: Pydantic schemas for the academic module (Subject and Class CRUD).
# Created At: 2026-07-21
# Created By: Tam Khang
# Updated At: 2026-07-22
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


class ClassCreate(BaseModel):
    """Schema for creating a new class."""
    class_name: str = Field(..., max_length=50, description="Tên lớp học (phải là duy nhất)")
    school_year: Optional[str] = Field(None, max_length=20, description="Năm học (ví dụ: 2026-2027)")
    homeroom_teacher_id: Optional[UUID] = Field(None, description="UUID của Giáo viên chủ nhiệm")


class ClassUpdate(BaseModel):
    """Schema for updating an existing class (all fields optional)."""
    class_name: Optional[str] = Field(None, max_length=50, description="Tên lớp học mới")
    school_year: Optional[str] = Field(None, max_length=20, description="Năm học mới")
    homeroom_teacher_id: Optional[UUID] = Field(None, description="UUID của Giáo viên chủ nhiệm mới")


class ClassOut(BaseModel):
    """Schema for class response output."""
    class_id: UUID
    class_name: str
    school_year: Optional[str] = Field(None, validation_alias="academic_year")
    homeroom_teacher_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}

