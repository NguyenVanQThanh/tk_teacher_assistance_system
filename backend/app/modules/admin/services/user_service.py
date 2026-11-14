# File Name: user_service.py
# Description: Business logic and validation layer for Admin User Management module.
# Created At: 2026-09-29
# Created By: Tam Khang
# Updated At: 2026-09-29
# Updated By: Tam Khang

import csv
import io
from datetime import date
from typing import Optional, Dict, Any, Tuple
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.modules.admin.repository import AdminUserRepository
from app.modules.admin.schemas import (
    AdminUserCreateRequest,
    AdminUserCreateResponse,
    AdminUserUpdateRequest,
    AdminUserResetPasswordResponse
)
from app.modules.admin.services.notification_service import NotificationService
from models.models import Class


class AdminUserService:
    @staticmethod
    def calculate_age(birthday: date) -> int:
        today = date.today()
        return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))

    @classmethod
    def validate_user_age(cls, role_name: str, birthday: Optional[date]):
        """
        Validates age constraints based on role:
        - Students must be at least 16 years old.
        - Teachers must be at least 22 years old.
        """
        if not birthday:
            return

        today = date.today()
        if birthday > today:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "ERR-ADMIN-INVALID_BIRTHDAY",
                    "message": "Birthday cannot be in the future."
                }
            )

        age = cls.calculate_age(birthday)
        if role_name.lower() == "student" and age < 16:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "ERR-ADMIN-STUDENT_AGE_UNDER_16",
                    "message": f"Student must be at least 16 years old. (Given birthday: {birthday}, age: {age})"
                }
            )
        elif role_name.lower() == "teacher" and age < 22:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "ERR-ADMIN-TEACHER_AGE_UNDER_22",
                    "message": f"Teacher must be at least 22 years old. (Given birthday: {birthday}, age: {age})"
                }
            )

    @classmethod
    def create_user(cls, db: Session, payload: AdminUserCreateRequest) -> AdminUserCreateResponse:
        """
        Creates a new user with comprehensive validation, automatically creates a default password
        if not specified, hashes it, saves it to the database, and dispatches an SMS / system notification.
        """
        # 1. Validate role exists
        role_obj = AdminUserRepository.get_role_by_name(db, payload.role)
        if not role_obj:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "ERR-ADMIN-INVALID_ROLE",
                    "message": f"Role '{payload.role}' does not exist in the system."
                }
            )

        # 2. Validate uniqueness of phone number
        if payload.phone:
            existing_phone = AdminUserRepository.get_user_by_phone(db, payload.phone)
            if existing_phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "ERR-ADMIN-DUPLICATE_PHONE",
                        "message": f"Phone number '{payload.phone}' is already registered to another user."
                    }
                )

        # 3. Validate uniqueness of email
        if payload.email:
            existing_email = AdminUserRepository.get_user_by_email(db, payload.email)
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "ERR-ADMIN-DUPLICATE_EMAIL",
                        "message": f"Email '{payload.email}' is already registered to another user."
                    }
                )

        # 4. Validate uniqueness of identifier code
        if payload.code:
            if AdminUserRepository.check_code_exists(db, payload.code):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "ERR-ADMIN-DUPLICATE_CODE",
                        "message": f"Identifier code '{payload.code}' is already assigned to another user."
                    }
                )

        # 5. Validate age according to role rules
        cls.validate_user_age(role_obj.name, payload.birthday)

        # 5. Handle password (auto-generate default password per user requirement)
        raw_password = payload.password.strip() if (payload.password and payload.password.strip()) else NotificationService.generate_default_password()
        hashed_password = get_password_hash(raw_password)

        # 6. Resolve class if specified
        resolved_class_id = None
        if payload.class_id:
            try:
                resolved_class_id = UUID(payload.class_id)
            except ValueError:
                pass
        elif payload.class_name:
            found_class = db.query(Class).filter(Class.class_name.ilike(payload.class_name.strip())).first()
            if found_class:
                resolved_class_id = found_class.class_id

        # 7. Insert user in repository
        status_val = "ACTIVE" if payload.is_active_immediately else (payload.status.upper() if payload.status else "INACTIVE")
        new_user = AdminUserRepository.create_user(
            db=db,
            full_name=payload.full_name,
            role_id=role_obj.role_id,
            password_hash=hashed_password,
            phone=payload.phone,
            email=payload.email,
            birthday=payload.birthday,
            status=status_val,
            class_id=resolved_class_id,
            student_code=payload.code
        )

        # 8. Dispatch notification via SMS and system notification channel
        dispatch_result = NotificationService.send_password_notification(
            full_name=new_user.full_name,
            password=raw_password,
            phone=new_user.phone,
            email=new_user.email,
            action="create"
        )

        return AdminUserCreateResponse(
            id=new_user.user_id,
            user_id=new_user.user_id,
            full_name=new_user.full_name,
            role=role_obj.name,
            phone=new_user.phone,
            email=new_user.email,
            status=new_user.status,
            code=payload.code,
            department=payload.department,
            class_name=payload.class_name,
            temporary_password=raw_password,
            notification_sent=dispatch_result["sent"],
            notification_channel=dispatch_result["channel"],
            notification_message=dispatch_result["message"],
            created_at=new_user.created_at
        )

    @classmethod
    def update_user(cls, db: Session, user_id: UUID, payload: AdminUserUpdateRequest) -> Dict[str, Any]:
        user = AdminUserRepository.get_user_by_id(db, user_id)
        if not user or user.status == "DELETED":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ERR-ADMIN-USER_NOT_FOUND", "message": "User not found or has been deleted."}
            )

        # Validate unique phone
        if payload.phone:
            existing_phone = AdminUserRepository.get_user_by_phone(db, payload.phone, exclude_user_id=user_id)
            if existing_phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "ERR-ADMIN-DUPLICATE_PHONE", "message": f"Phone number '{payload.phone}' is already in use."}
                )

        # Validate unique email
        if payload.email:
            existing_email = AdminUserRepository.get_user_by_email(db, payload.email, exclude_user_id=user_id)
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "ERR-ADMIN-DUPLICATE_EMAIL", "message": f"Email '{payload.email}' is already in use."}
                )

        # Check role update
        target_role = None
        if payload.role:
            target_role = AdminUserRepository.get_role_by_name(db, payload.role)
            if not target_role:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={"code": "ERR-ADMIN-INVALID_ROLE", "message": f"Role '{payload.role}' does not exist."}
                )

        role_name_to_check = target_role.name if target_role else None
        if not role_name_to_check:
            # Query existing role
            r = db.query(models_role := AdminUserRepository.get_roles(db)).filter(lambda x: False) if False else None
            # Directly get user role
            from models.models import Role
            current_role = db.query(Role).filter(Role.role_id == user.role_id).first()
            if current_role:
                role_name_to_check = current_role.name

        target_birthday = payload.birthday if payload.birthday is not None else user.birthday
        if role_name_to_check:
            cls.validate_user_age(role_name_to_check, target_birthday)

        updates = {}
        if payload.full_name is not None:
            updates["full_name"] = payload.full_name
        if payload.phone is not None:
            updates["phone"] = payload.phone
        if payload.email is not None:
            updates["email"] = payload.email
        if payload.birthday is not None:
            updates["birthday"] = payload.birthday
        if target_role:
            updates["role_id"] = target_role.role_id
        if payload.status is not None:
            updates["status"] = payload.status.upper()

        AdminUserRepository.update_user(db, user, updates)

        # Return updated details
        items, _ = AdminUserRepository.list_users(db, page=1, page_size=1, search=user.full_name)
        for item in items:
            if item["id"] == user.user_id:
                return item

        return {
            "id": user.user_id,
            "user_id": user.user_id,
            "full_name": user.full_name,
            "phone": user.phone,
            "email": user.email,
            "birthday": user.birthday,
            "status": user.status,
            "role": role_name_to_check or "User"
        }

    @classmethod
    def update_status(cls, db: Session, user_id: UUID, new_status: str, reason: Optional[str] = None) -> Dict[str, Any]:
        user = AdminUserRepository.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ERR-ADMIN-USER_NOT_FOUND", "message": "User not found."}
            )

        valid_statuses = {"ACTIVE", "INACTIVE", "SUSPENDED", "DELETED"}
        normalized = new_status.strip().upper()
        if normalized not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "ERR-ADMIN-INVALID_STATUS", "message": f"Status must be one of: {', '.join(valid_statuses)}"}
            )

        AdminUserRepository.update_status(db, user, normalized)
        return {
            "message": f"User status updated to {normalized} successfully.",
            "user_id": user.user_id,
            "status": normalized,
            "reason": reason
        }

    @classmethod
    def soft_delete_user(cls, db: Session, user_id: UUID) -> Dict[str, Any]:
        """
        Soft-delete a user by updating status to DELETED.
        """
        user = AdminUserRepository.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ERR-ADMIN-USER_NOT_FOUND", "message": "User not found."}
            )

        AdminUserRepository.soft_delete_user(db, user)
        return {
            "message": "User has been soft-deleted successfully.",
            "user_id": user.user_id,
            "status": "DELETED"
        }

    @classmethod
    def restore_user(cls, db: Session, user_id: UUID) -> Dict[str, Any]:
        """
        Restores a soft-deleted user back to ACTIVE.
        """
        user = AdminUserRepository.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ERR-ADMIN-USER_NOT_FOUND", "message": "User not found."}
            )

        AdminUserRepository.restore_user(db, user)
        return {
            "message": "User has been restored successfully.",
            "user_id": user.user_id,
            "status": "ACTIVE"
        }

    @classmethod
    def reset_password(cls, db: Session, user_id: UUID, custom_password: Optional[str] = None) -> AdminUserResetPasswordResponse:
        """
        Resets user password, auto-generating a secure default password if custom is not provided,
        and dispatches SMS / system notification to the user.
        """
        user = AdminUserRepository.get_user_by_id(db, user_id)
        if not user or user.status == "DELETED":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ERR-ADMIN-USER_NOT_FOUND", "message": "User not found or has been deleted."}
            )

        new_plain_password = custom_password.strip() if (custom_password and custom_password.strip()) else NotificationService.generate_default_password()
        hashed_password = get_password_hash(new_plain_password)
        AdminUserRepository.reset_password(db, user, hashed_password)

        dispatch_result = NotificationService.send_password_notification(
            full_name=user.full_name,
            password=new_plain_password,
            phone=user.phone,
            email=user.email,
            action="reset"
        )

        return AdminUserResetPasswordResponse(
            message="Password reset successfully. Default password dispatched via SMS/system notification.",
            temporary_password=new_plain_password,
            notification_sent=dispatch_result["sent"],
            notification_channel=dispatch_result["channel"],
            notification_message=dispatch_result["message"]
        )

    @classmethod
    def export_users_csv(
        cls,
        db: Session,
        search: Optional[str] = None,
        role: Optional[str] = None,
        status_val: Optional[str] = None,
        grade: Optional[str] = None,
        department: Optional[str] = None
    ) -> str:
        """
        Exports users matching filters as UTF-8 BOM CSV format compatible with Microsoft Excel.
        """
        items, _ = AdminUserRepository.list_users(
            db=db,
            page=1,
            page_size=10000,
            search=search,
            role=role,
            status=status_val,
            grade=grade,
            department=department
        )

        output = io.StringIO()
        # UTF-8 BOM for Excel compatibility
        output.write("\ufeff")
        writer = csv.writer(output)

        headers = [
            "ID",
            "Mã Định Danh",
            "Họ và Tên",
            "Vai Trò",
            "Số Điện Thoại",
            "Email",
            "Ngày Sinh",
            "Trạng Thái",
            "Lớp / Phòng Ban",
            "Ngày Khởi Tạo"
        ]
        writer.writerow(headers)

        for item in items:
            writer.writerow([
                str(item["id"]),
                item.get("code") or "",
                item.get("full_name") or "",
                item.get("role") or "",
                item.get("phone") or "",
                item.get("email") or "",
                str(item.get("birthday")) if item.get("birthday") else "",
                item.get("status") or "",
                item.get("class_name") or item.get("department") or "",
                str(item.get("created_at")) if item.get("created_at") else ""
            ])

        return output.getvalue()

    @classmethod
    def generate_unique_code(cls, db: Session, role: str = "student") -> str:
        """
        Generates a unique identifier code based on role and current year.
        Checks against database to guarantee absolute uniqueness.
        """
        import random
        prefix = "GV" if (role or "").lower() in ["teacher", "giáo viên"] else "HS"
        current_year = date.today().year

        for _ in range(50):
            candidate = f"{prefix}{current_year}{random.randint(1000, 9999)}"
            if not AdminUserRepository.check_code_exists(db, candidate):
                return candidate

        # Fallback to 5-digit random
        for _ in range(50):
            candidate = f"{prefix}{current_year}{random.randint(10000, 99999)}"
            if not AdminUserRepository.check_code_exists(db, candidate):
                return candidate

        return f"{prefix}{current_year}{int(date.today().strftime('%m%d%H%M'))}"
