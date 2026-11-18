# File Name: schemas.py
# Description: Pydantic schemas for auth module request and response validation with RBAC permissions list.
# Created At: 2026-07-11
# Created By: Tam Khang
# Updated At: 2026-11-15
# Updated By: AI Agent


from uuid import UUID
from typing import Dict, Optional, List
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.core.names import normalize_full_name

class LoginRequest(BaseModel):
    """
    Schema for login request.
    Only accepts a phone number (10 digits starting with 0) as the login credential.
    """
    phone: str = Field(
        ...,
        description="Phone number used for login (10 digits, starting with 0)",
        pattern=r"^0\d{9}$"
    )
    password: str = Field(
        ..., 
        description="User password",
        min_length=1,
        max_length=128
    )

class UserOut(BaseModel):
    """
    Schema for user information returned in login response.
    """
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    full_name: str
    role: str
    email_masked: Optional[str] = Field(None, description="Masked email address for privacy")
    phone_masked: Optional[str] = Field(None, description="Masked phone number for privacy")
    permissions: List[str] = Field(default_factory=list, description="Effective permission codes")
    is_guest: bool = Field(False, description="True for guest accounts")

class GuestRequest(BaseModel):
    """Schema for POST /auth/guest."""
    role: Literal["Teacher", "Student"] = Field(..., description="Guest role: Teacher or Student")
    guest_key: Optional[str] = Field(None, max_length=128, description="Secret returned on creation; used to resume")

class LoginResponse(BaseModel):
    """
    Schema for successful login response.
    """
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Access token type (bearer)")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserOut = Field(..., description="Authenticated user information")
    guest_key: Optional[str] = Field(None, description="Resume secret; only set when a guest account is created")

class UserProfileOut(BaseModel):
    """
    Schema for user profile returned from /me endpoint.
    """
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    full_name: str
    role: str
    email: Optional[str] = Field(None, description="User email address")
    phone: Optional[str] = Field(None, description="User phone number")
    status: str = Field(..., description="User account status")
    student_code: Optional[str] = Field(None, description="Student enrollment code if applicable")
    class_id: Optional[UUID] = Field(None, description="Enrolled or primary class ID")
    class_name: Optional[str] = Field(None, description="Enrolled or primary class name")
    teaching_subjects: Optional[List[str]] = Field(None, description="Assigned teaching subjects for teachers")
    permissions: List[str] = Field(default_factory=list, description="Effective permission codes")
    is_guest: bool = Field(False, description="True for guest accounts")
    guest_usage: Optional[Dict[str, Dict[str, int]]] = Field(
        None, description="Guest quota usage: {documents|ai|imports: {used, limit}}; null for regular users")
    current_academic_year: Optional[str] = Field(None, description="Current academic year, e.g. 2025-2026")

class UserProfileUpdateRequest(BaseModel):
    """
    Schema for updating current user profile details.
    """
    full_name: Optional[str] = Field(None, min_length=1, max_length=128)
    email: Optional[str] = Field(None, max_length=128)
    phone: Optional[str] = Field(None, min_length=10, max_length=15)

    @field_validator("full_name")
    @classmethod
    def _normalize_name(cls, v: Optional[str]) -> Optional[str]:
        return None if v is None else normalize_full_name(v, min_length=1)

class ChangePasswordRequest(BaseModel):
    """
    Schema for changing password request.
    """
    old_password: str = Field(..., description="Current password", min_length=1)
    new_password: str = Field(
        ..., 
        description="New password (must be at least 8 characters)",
        min_length=8,
        max_length=128
    )

class RegisterRequest(BaseModel):
    """
    Schema for register request.
    """
    full_name: str = Field(..., description="User full name", min_length=1, max_length=128)

    @field_validator("full_name")
    @classmethod
    def _normalize_name(cls, v: str) -> str:
        return normalize_full_name(v, min_length=1)

    phone: str = Field(
        ..., 
        description="Phone number used for registration",
        pattern=r"^0\d{9}$",
        min_length=10,
        max_length=10
    )
    password: str = Field(
        ..., 
        description="User password",
        min_length=8,
        max_length=128
    )