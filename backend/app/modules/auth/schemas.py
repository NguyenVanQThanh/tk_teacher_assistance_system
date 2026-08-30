# File Name: schemas.py
# Description: Pydantic schemas for auth module request and response validation.
# Created At: 2026-07-11
# Created By: Thanh Nguyen
# Updated At: 2026-07-17
# Updated By: Tam Khang


from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class LoginRequest(BaseModel):
    """
    Schema for login request.
    Accepts phone as login credential.
    """
    phone: str = Field(
        ..., 
        description="Phone number used for login",
        pattern=r"^0\d{9}$",
        min_length=10,
        max_length=10
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

class LoginResponse(BaseModel):
    """
    Schema for successful login response.
    """
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Access token type (bearer)")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserOut = Field(..., description="Authenticated user information")

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