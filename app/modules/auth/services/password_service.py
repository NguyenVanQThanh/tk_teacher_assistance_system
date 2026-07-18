# File Name: password_service.py
# Description: Service layer implementing change password logic.
# Created At: 2026-07-17
# Created By: Tam Khang
# Updated At: 2026-07-17
# Updated By: Tam Khang

import logging
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.models import User
from app.core.security import verify_password, get_password_hash

logger = logging.getLogger("password_service")

class PasswordService:
    @staticmethod
    def change_password(db: Session, user: User, old_password: str, new_password: str) -> None:
        """
        Verifies old password, checks if new password is a reuse of old password,
        hashes the new password, and updates user credentials in database.
        """
        # 1. Verify old password matches DB hash
        if not verify_password(old_password, user.password_hash):
            logger.warning("Domain Event: EVT-AUTH-PASSWORD_CHANGE_FAILED - Incorrect old password for user_id: %s", user.user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "ERR-AUTH-INVALID_CREDENTIALS",
                    "message": "Mật khẩu cũ không chính xác."
                }
            )

        # 2. Check if new password is same as old password
        if verify_password(new_password, user.password_hash):
            logger.warning("Domain Event: EVT-AUTH-PASSWORD_CHANGE_FAILED - Attempted reuse of old password for user_id: %s", user.user_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "ERR-AUTH-PASSWORD_REUSE",
                    "message": "Mật khẩu mới không được trùng với mật khẩu cũ."
                }
            )

        # 3. Hash new password and update in DB
        user.password_hash = get_password_hash(new_password)
        db.commit()

        # 4. Log success event
        logger.info("Domain Event: EVT-AUTH-PASSWORD_CHANGED - Successfully changed password for user_id: %s", user.user_id)
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hashes a plaintext password.
        """
        return get_password_hash(password)
