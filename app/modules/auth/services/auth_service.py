# File Name: auth_service.py
# Description: Service layer implementing login, password verification, and JWT token issuance.
# Created At: 2026-07-16
# Created By: Tam Khang
# Updated At: 2026-07-16
# Updated By: Tam Khang

import logging
from datetime import timedelta
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.models import User, Role
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import LoginResponse, UserOut
from app.core.security import create_access_token, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES

logger = logging.getLogger("auth_service")

class AuthService:
    @staticmethod
    def mask_email(email: Optional[str]) -> Optional[str]:
        """
        Mask email address for privacy (e.g., thanhnguyen@gmail.com -> t***@gmail.com).
        """
        if not email:
            return None
        try:
            parts = email.split("@")
            if len(parts) != 2:
                return email
            name, domain = parts
            if len(name) <= 1:
                masked_name = name + "***"
            else:
                masked_name = name[0] + "***"
            return f"{masked_name}@{domain}"
        except Exception:
            return email

    @staticmethod
    def authenticate_user(db: Session, identifier: str, password_plain: str) -> User:
        """
        Authenticate a user by checking email first, then phone number.
        Verifies the hashed password and checks the user status.
        """
        # 1. Search for user by email
        user = UserRepository.get_by_email(db, identifier)
        
        # 2. If not found by email, search by phone number
        if not user:
            user = UserRepository.get_by_phone(db, identifier)
            
        # 3. If user not found, raise invalid credentials error
        if not user:
            logger.warning("Domain Event: EVT-AUTH-LOGIN_FAILED - User not found for identifier: %s", identifier)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "ERR-AUTH-INVALID_CREDENTIALS",
                    "message": "Tên đăng nhập hoặc mật khẩu không chính xác."
                }
            )

        # 4. Verify password
        if not verify_password(password_plain, user.password_hash):
            logger.warning("Domain Event: EVT-AUTH-LOGIN_FAILED - Incorrect password for user_id: %s", user.user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "ERR-AUTH-INVALID_CREDENTIALS",
                    "message": "Tên đăng nhập hoặc mật khẩu không chính xác."
                }
            )

        # 5. Check user status
        if user.status == "Blocked":
            logger.warning("Domain Event: EVT-AUTH-LOGIN_FAILED - Blocked user attempted login: %s", user.user_id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "ERR-AUTH-ACCOUNT_BLOCKED",
                    "message": "Tài khoản của bạn đã bị khóa."
                }
            )
        elif user.status == "Inactive":
            logger.warning("Domain Event: EVT-AUTH-LOGIN_FAILED - Inactive user attempted login: %s", user.user_id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "ERR-AUTH-ACCOUNT_INACTIVE",
                    "message": "Tài khoản chưa được kích hoạt."
                }
            )

        return user

    @staticmethod
    def issue_access_token(db: Session, user: User) -> LoginResponse:
        """
        Issue a JWT access token and return the login response envelope.
        """
        # 1. Retrieve the role name from database
        role = db.query(Role).filter(Role.role_id == user.role_id).first()
        role_name = role.name if role else "User"

        # 2. Create access token
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.user_id,
            role=role_name,
            expires_delta=expires_delta
        )

        # 3. Mask user email for privacy in response
        email_masked = AuthService.mask_email(user.email)

        # 4. Construct user response info
        user_out = UserOut(
            user_id=user.user_id,
            full_name=user.full_name,
            role=role_name,
            email_masked=email_masked
        )

        # 5. Log success event
        logger.info("Domain Event: EVT-AUTH-USER_LOGGED_IN - Successfully authenticated user_id: %s", user.user_id)

        # 6. Return standard envelope response
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_out
        )
