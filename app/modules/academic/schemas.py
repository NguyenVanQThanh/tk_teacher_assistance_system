# File Name: schemas.py
# Description: Pydantic schemas for the academic module with comprehensive validation and AcademicStatusEnum.
# Created At: 2026-07-21
# Created By: Tam Khang
# Updated At: 2026-07-26
# Updated By: Tam Khang

import re
from enum import Enum
from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class AcademicStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DRAFT = "DRAFT"
    DELETED = "DELETED"


class SubjectCreate(BaseModel):
    """Schema for creating a new subject."""
    subject_name: str = Field(..., min_length=1, max_length=100, description="Tên môn học (phải là duy nhất)")
    description: Optional[str] = Field(None, max_length=500, description="Mô tả môn học")
    status: AcademicStatusEnum = Field(AcademicStatusEnum.ACTIVE, description="Trạng thái môn học")

    @field_validator("subject_name")
    @classmethod
    def validate_subject_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Tên môn học không được để trống hoặc chỉ chứa khoảng trắng.")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v


class SubjectUpdate(BaseModel):
    """Schema for updating an existing subject."""
    subject_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Tên môn học mới")
    description: Optional[str] = Field(None, max_length=500, description="Mô tả mới")
    status: Optional[AcademicStatusEnum] = Field(None, description="Trạng thái mới")

    @field_validator("subject_name")
    @classmethod
    def validate_subject_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Tên môn học không được để trống hoặc chỉ chứa khoảng trắng.")
            return v
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v


class SubjectOut(BaseModel):
    """Schema for subject response output."""
    subject_id: UUID
    subject_name: str
    description: Optional[str]
    status: AcademicStatusEnum = AcademicStatusEnum.ACTIVE
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClassCreate(BaseModel):
    """Schema for creating a new class."""
    class_name: str = Field(..., min_length=1, max_length=50, description="Tên lớp học (phải là duy nhất)")
    school_year: Optional[str] = Field(None, max_length=20, description="Năm học (ví dụ: 2026-2027)")
    homeroom_teacher_id: Optional[UUID] = Field(None, description="UUID của Giáo viên chủ nhiệm")
    status: AcademicStatusEnum = Field(AcademicStatusEnum.ACTIVE, description="Trạng thái lớp học")

    @field_validator("class_name")
    @classmethod
    def validate_class_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Tên lớp học không được để trống hoặc chỉ chứa khoảng trắng.")
        return v

    @field_validator("school_year")
    @classmethod
    def validate_school_year(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                return None
            if not re.match(r"^\d{4}-\d{4}$", v):
                raise ValueError("Năm học phải theo định dạng YYYY-YYYY (ví dụ: 2025-2026).")
            return v
        return v


class ClassUpdate(BaseModel):
    """Schema for updating an existing class."""
    class_name: Optional[str] = Field(None, min_length=1, max_length=50, description="Tên lớp học mới")
    school_year: Optional[str] = Field(None, max_length=20, description="Năm học mới")
    homeroom_teacher_id: Optional[UUID] = Field(None, description="UUID của Giáo viên chủ nhiệm mới")
    status: Optional[AcademicStatusEnum] = Field(None, description="Trạng thái mới")

    @field_validator("class_name")
    @classmethod
    def validate_class_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Tên lớp học không được để trống hoặc chỉ chứa khoảng trắng.")
            return v
        return v

    @field_validator("school_year")
    @classmethod
    def validate_school_year(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                return None
            if not re.match(r"^\d{4}-\d{4}$", v):
                raise ValueError("Năm học phải theo định dạng YYYY-YYYY (ví dụ: 2025-2026).")
            return v
        return v


class ClassOut(BaseModel):
    """Schema for class response output."""
    class_id: UUID
    class_name: str
    school_year: Optional[str] = Field(None, validation_alias="academic_year")
    homeroom_teacher_id: Optional[UUID] = None
    status: AcademicStatusEnum = AcademicStatusEnum.ACTIVE
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class EnrollmentCreate(BaseModel):
    """Schema for enrolling a student into a class."""
    student_id: UUID = Field(..., description="UUID của học sinh")
    student_code: Optional[str] = Field(None, max_length=50, description="Mã số học sinh (duy nhất nếu có)")
    status: AcademicStatusEnum = Field(AcademicStatusEnum.ACTIVE, description="Trạng thái ghi danh")

    @field_validator("student_code")
    @classmethod
    def validate_student_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v


class EnrollmentOut(BaseModel):
    """Schema for enrollment response output."""
    student_id: UUID
    class_id: UUID
    student_code: Optional[str] = None
    status: AcademicStatusEnum = AcademicStatusEnum.ACTIVE

    model_config = {"from_attributes": True}


class TeacherAssignmentCreate(BaseModel):
    """Schema for assigning a teacher to a subject in a class."""
    teacher_id: UUID = Field(..., description="UUID của giáo viên")
    subject_id: UUID = Field(..., description="UUID của môn học")
    status: AcademicStatusEnum = Field(AcademicStatusEnum.ACTIVE, description="Trạng thái phân công")


class TeacherAssignmentOut(BaseModel):
    """Schema for teacher assignment response output."""
    teacher_id: UUID
    class_id: UUID
    subject_id: UUID
    status: AcademicStatusEnum = AcademicStatusEnum.ACTIVE

    model_config = {"from_attributes": True}
