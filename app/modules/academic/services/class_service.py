# File Name: class_service.py
# Description: Service layer for Class business logic — duplicate check, homeroom teacher validation, CRUD operations.
# Created At: 2026-07-22
# Created By: Tam Khang
# Updated At: 2026-07-22
# Updated By: Tam Khang

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.models import User, Role
from app.modules.academic.models import Class
from app.modules.academic.repository import ClassRepository

logger = logging.getLogger("class_service")


class ClassService:
    @staticmethod
    def _validate_homeroom_teacher(db: Session, teacher_id: UUID) -> None:
        """
        Validate that homeroom_teacher_id references an Active user with Teacher role.
        Raises 400 ERR-ACAD-INVALID_HOMEROOM_TEACHER if invalid.
        """
        teacher = (
            db.query(User)
            .join(Role, User.role_id == Role.role_id)
            .filter(
                User.user_id == teacher_id,
                Role.name == "Teacher",
                User.status == "Active"
            )
            .first()
        )
        if not teacher:
            logger.warning(
                "Homeroom teacher validation failed for user_id: %s", teacher_id
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "ERR-ACAD-INVALID_HOMEROOM_TEACHER",
                    "message": "Giáo viên chủ nhiệm không hợp lệ (phải có vai trò Teacher và trạng thái Active)."
                }
            )

    @staticmethod
    def create_class(
        db: Session,
        class_name: str,
        school_year: Optional[str] = None,
        homeroom_teacher_id: Optional[UUID] = None
    ) -> Class:
        """
        Create a new class.
        Raises 400 if homeroom_teacher_id is provided but invalid.
        Raises 409 if class_name already exists.
        """
        if homeroom_teacher_id is not None:
            ClassService._validate_homeroom_teacher(db, homeroom_teacher_id)

        existing = ClassRepository.get_by_name(db, class_name)
        if existing:
            logger.warning(
                "Domain Event: EVT-ACAD-CLASS_CREATED failed — duplicate name: %s", class_name
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ERR-ACAD-CLASS_DUPLICATE_NAME",
                    "message": "Tên lớp học đã tồn tại trong hệ thống."
                }
            )

        cls = ClassRepository.create(
            db=db,
            class_name=class_name,
            academic_year=school_year,
            homeroom_teacher_id=homeroom_teacher_id
        )
        logger.info(
            "Domain Event: EVT-ACAD-CLASS_CREATED - class_id: %s, name: %s",
            cls.class_id, cls.class_name
        )
        return cls

    @staticmethod
    def list_classes(db: Session) -> List[Class]:
        """Return all classes."""
        return ClassRepository.list_all(db)

    @staticmethod
    def get_class(db: Session, class_id: UUID) -> Class:
        """
        Return a class by ID.
        Raises 404 if not found.
        """
        cls = ClassRepository.get_by_id(db, class_id)
        if not cls:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-CLASS_NOT_FOUND",
                    "message": "Lớp học không tồn tại."
                }
            )
        return cls

    @staticmethod
    def update_class(
        db: Session,
        class_id: UUID,
        class_name: Optional[str] = None,
        school_year: Optional[str] = None,
        homeroom_teacher_id: Optional[UUID] = None,
        update_homeroom_teacher: bool = False
    ) -> Class:
        """
        Update a class.
        Raises 404 if not found.
        Raises 400 if homeroom_teacher_id is updated to an invalid teacher.
        Raises 409 if new class_name conflicts with another class.
        """
        cls = ClassService.get_class(db, class_id)

        if update_homeroom_teacher and homeroom_teacher_id is not None:
            ClassService._validate_homeroom_teacher(db, homeroom_teacher_id)

        if class_name is not None:
            conflict = ClassRepository.get_by_name(db, class_name)
            if conflict and conflict.class_id != cls.class_id:
                logger.warning(
                    "Domain Event: EVT-ACAD-CLASS_UPDATED failed — duplicate name: %s", class_name
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "ERR-ACAD-CLASS_DUPLICATE_NAME",
                        "message": "Tên lớp học đã tồn tại trong hệ thống."
                    }
                )

        cls = ClassRepository.update(
            db=db,
            class_obj=cls,
            class_name=class_name,
            academic_year=school_year,
            homeroom_teacher_id=homeroom_teacher_id,
            update_homeroom_teacher=update_homeroom_teacher
        )
        logger.info(
            "Domain Event: EVT-ACAD-CLASS_UPDATED - class_id: %s", cls.class_id
        )
        return cls

    @staticmethod
    def delete_class(db: Session, class_id: UUID) -> None:
        """
        Delete a class by ID.
        Raises 404 if not found.
        """
        cls = ClassService.get_class(db, class_id)
        ClassRepository.delete(db, cls)
        logger.info(
            "Domain Event: EVT-ACAD-CLASS_DELETED - class_id: %s", class_id
        )
