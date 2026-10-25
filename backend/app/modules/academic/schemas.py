# File Name: schemas.py
# Description: Pydantic schemas for the academic module with comprehensive validation and AcademicStatusEnum.
# Created At: 2026-07-21
# Created By: Tam Khang
# Updated At: 2026-09-01
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
    subject_name: str = Field(..., min_length=1, max_length=100, description="Subject name (must be unique)")
    description: Optional[str] = Field(None, max_length=500, description="Subject description")
    status: AcademicStatusEnum = Field(AcademicStatusEnum.ACTIVE, description="Subject status")

    @field_validator("subject_name")
    @classmethod
    def validate_subject_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Subject name cannot be empty or blank.")
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
    subject_name: Optional[str] = Field(None, min_length=1, max_length=100, description="New subject name")
    description: Optional[str] = Field(None, max_length=500, description="New description")
    status: Optional[AcademicStatusEnum] = Field(None, description="New status")

    @field_validator("subject_name")
    @classmethod
    def validate_subject_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Subject name cannot be empty or blank.")
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
    class_name: str = Field(..., min_length=1, max_length=50, description="Class name (must be unique)")
    school_year: Optional[str] = Field(None, max_length=20, description="Academic year (e.g., 2026-2027)")
    homeroom_teacher_id: Optional[UUID] = Field(None, description="UUID of Homeroom Teacher")
    status: AcademicStatusEnum = Field(AcademicStatusEnum.ACTIVE, description="Class status")

    @field_validator("class_name")
    @classmethod
    def validate_class_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Class name cannot be empty or blank.")
        return v

    @field_validator("school_year")
    @classmethod
    def validate_school_year(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                return None
            if not re.match(r"^\d{4}-\d{4}$", v):
                raise ValueError("Academic year must follow YYYY-YYYY format (e.g., 2025-2026).")
            return v
        return v


class ClassUpdate(BaseModel):
    """Schema for updating an existing class."""
    class_name: Optional[str] = Field(None, min_length=1, max_length=50, description="New class name")
    school_year: Optional[str] = Field(None, max_length=20, description="New academic year")
    homeroom_teacher_id: Optional[UUID] = Field(None, description="UUID of new Homeroom Teacher")
    status: Optional[AcademicStatusEnum] = Field(None, description="New status")

    @field_validator("class_name")
    @classmethod
    def validate_class_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Class name cannot be empty or blank.")
            return v

    @field_validator("school_year")
    @classmethod
    def validate_school_year(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                return None
            if not re.match(r"^\d{4}-\d{4}$", v):
                raise ValueError("Academic year must follow YYYY-YYYY format (e.g., 2025-2026).")
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
    student_id: UUID = Field(..., description="UUID of Student")
    student_code: Optional[str] = Field(None, max_length=50, description="Student code (unique if provided)")
    status: AcademicStatusEnum = Field(AcademicStatusEnum.ACTIVE, description="Enrollment status")

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
    student_name: Optional[str] = None
    status: AcademicStatusEnum = AcademicStatusEnum.ACTIVE

    model_config = {"from_attributes": True}


class TeacherAssignmentCreate(BaseModel):
    """Schema for assigning a teacher to a subject in a class."""
    teacher_id: UUID = Field(..., description="UUID of Teacher")
    subject_id: UUID = Field(..., description="UUID of Subject")
    status: AcademicStatusEnum = Field(AcademicStatusEnum.ACTIVE, description="Assignment status")


class TeacherAssignmentOut(BaseModel):
    """Schema for teacher assignment response output."""
    teacher_id: UUID
    class_id: UUID
    subject_id: UUID
    status: AcademicStatusEnum = AcademicStatusEnum.ACTIVE

    model_config = {"from_attributes": True}
