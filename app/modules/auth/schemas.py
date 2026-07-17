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
        description="Số điện thoại dùng để đăng nhập",
        pattern=r"^0\d{9}$",
        min_length=10,
        max_length=10
    )
    password: str = Field(
        ..., 
        description="Mật khẩu người dùng",
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
    email_masked: Optional[str] = Field(None, description="Địa chỉ email đã ẩn để bảo mật")
    phone_masked: Optional[str] = Field(None, description="Số điện thoại đã ẩn để bảo mật")

class LoginResponse(BaseModel):
    """
    Schema for successful login response.
    """
    access_token: str = Field(..., description="Mã truy cập JWT")
    token_type: str = Field("bearer", description="Loại mã truy cập, thường là bearer")
    expires_in: int = Field(..., description="Thời gian hết hạn của mã truy cập tính bằng giây")
    user: UserOut = Field(..., description="Thông tin người dùng đã xác thực")

class UserProfileOut(BaseModel):
    """
    Schema for user profile returned from /me endpoint.
    """
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    full_name: str
    role: str
    email: Optional[str] = Field(None, description="Địa chỉ email của người dùng")
    phone: Optional[str] = Field(None, description="Số điện thoại của người dùng")
    status: str = Field(..., description="Trạng thái tài khoản người dùng")

class ChangePasswordRequest(BaseModel):
    """
    Schema for changing password request.
    """
    old_password: str = Field(..., description="Mật khẩu hiện tại", min_length=1)
    new_password: str = Field(
        ..., 
        description="Mật khẩu mới (phải có ít nhất 8 ký tự)",
        min_length=8,
        max_length=128
    )
