# File Name: enrollment_service.py
# Description: Service layer for Enrollment business logic — validation of class, student role/status, duplicate checks, RBAC Data Scoping, CRUD, and restore operations.
# Created At: 2026-07-23
# Created By: Tam Khang
# Updated At: 2026-07-26
# Updated By: Tam Khang

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.models import User, Role
from app.modules.academic.models import StudentClass
from app.modules.academic.repository import ClassRepository, EnrollmentRepository
from app.modules.academic.scoping import check_class_access

logger = logging.getLogger("enrollment_service")


class EnrollmentService:
    @staticmethod
    def enroll_student(
        db: Session,
        class_id: UUID,
        student_id: UUID,
        student_code: Optional[str] = None,
        status_val: str = "ACTIVE"
    ) -> StudentClass:
        """
        Enroll a student into a class.
        Raises 404 ERR-ACAD-CLASS_NOT_FOUND if class does not exist.
        Raises 404 ERR-ACAD-STUDENT_NOT_FOUND if student user does not exist.
        Raises 400 ERR-ACAD-INVALID_STUDENT_ROLE if user is not role Student or status is not Active.
        Raises 409 ERR-ACAD-ALREADY_ENROLLED if student is already enrolled in this class.
        Raises 409 ERR-ACAD-DUPLICATE_STUDENT_CODE if student_code is already used.
        """
        # 1. Validate class_id exists
        cls = ClassRepository.get_by_id(db, class_id)
        if not cls:
            logger.warning("Enrollment failed — class_id not found: %s", class_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-CLASS_NOT_FOUND",
                    "message": "Class not found."
                }
            )

        # 2. Validate student_id exists
        user = db.query(User).filter(User.user_id == student_id).first()
        if not user:
            logger.warning("Enrollment failed — student_id not found: %s", student_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-STUDENT_NOT_FOUND",
                    "message": "Student does not exist in the system."
                }
            )

        # 3. Validate user role Student + status Active
        valid_student = (
            db.query(User)
            .join(Role, User.role_id == Role.role_id)
            .filter(
                User.user_id == student_id,
                Role.name == "Student",
                User.status.in_(["Active", "ACTIVE"])
            )
            .first()
        )
        if not valid_student:
            logger.warning(
                "Enrollment failed — user %s is not active Student", student_id
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "ERR-ACAD-INVALID_STUDENT_ROLE",
                    "message": "Invalid student (must have Student role and Active status)."
                }
            )

        # 4. Validate not already enrolled in this class
        existing = EnrollmentRepository.get_enrollment(db, class_id=class_id, student_id=student_id)
        if existing:
            logger.warning(
                "Enrollment failed — student %s already enrolled in class %s", student_id, class_id
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ERR-ACAD-ALREADY_ENROLLED",
                    "message": "Student is already enrolled in this class."
                }
            )

        # 5. Validate student_code uniqueness if provided
        if student_code:
            code_conflict = EnrollmentRepository.get_by_student_code(db, student_code)
            if code_conflict:
                logger.warning(
                    "Enrollment failed — duplicate student_code: %s", student_code
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "ERR-ACAD-DUPLICATE_STUDENT_CODE",
                        "message": "Student code already exists in the system."
                    }
                )

        # 6. Insert enrollment record
        kwargs = {}
        if status_val and status_val != "ACTIVE":
            kwargs["status"] = status_val

        enrollment = EnrollmentRepository.create(
            db=db,
            class_id=class_id,
            student_id=student_id,
            student_code=student_code,
            **kwargs
        )
        logger.info(
            "Domain Event: EVT-ACAD-STUDENT_ENROLLED - class_id: %s, student_id: %s",
            class_id, student_id
        )
        return enrollment

    @staticmethod
    def list_students_in_class(
        db: Session,
        class_id: UUID,
        status_val: Optional[str] = None,
        current_user: Optional[User] = None
    ) -> List[StudentClass]:
        """
        List enrolled students in a class with RBAC Data Scoping.
        Raises 404 ERR-ACAD-CLASS_NOT_FOUND if class does not exist.
        """
        cls = ClassRepository.get_by_id(db, class_id)
        if not cls:
            logger.warning("List enrollments failed — class_id not found: %s", class_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-CLASS_NOT_FOUND",
                    "message": "Class not found."
                }
            )

        if current_user:
            check_class_access(db, current_user, class_id)

        if status_val:
            return EnrollmentRepository.list_by_class_id(db, class_id, status=status_val)
        return EnrollmentRepository.list_by_class_id(db, class_id)

    @staticmethod
    def unenroll_student(db: Session, class_id: UUID, student_id: UUID) -> None:
        """
        Unenroll a student from a class.
        Raises 404 ERR-ACAD-CLASS_NOT_FOUND if class does not exist.
        Raises 404 ERR-ACAD-ENROLLMENT_NOT_FOUND if student is not enrolled in class.
        """
        cls = ClassRepository.get_by_id(db, class_id)
        if not cls:
            logger.warning("Unenroll failed — class_id not found: %s", class_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-CLASS_NOT_FOUND",
                    "message": "Class not found."
                }
            )

        enrollment = EnrollmentRepository.get_enrollment(db, class_id=class_id, student_id=student_id)
        if not enrollment:
            logger.warning(
                "Unenroll failed — student %s not enrolled in class %s", student_id, class_id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-ENROLLMENT_NOT_FOUND",
                    "message": "Enrollment record not found in class."
                }
            )

        EnrollmentRepository.delete(db, enrollment)
        logger.info(
            "Domain Event: EVT-ACAD-STUDENT_UNENROLLED - class_id: %s, student_id: %s",
            class_id, student_id
        )

    @staticmethod
    def restore_enrollment(db: Session, class_id: UUID, student_id: UUID) -> StudentClass:
        """
        Restore a soft-deleted student enrollment record for Admin.
        Raises 404 if enrollment record does not exist.
        """
        results = EnrollmentRepository.filter_enrollments(
            db, class_id=class_id, student_id=student_id, exclude_status=None
        )
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-ENROLLMENT_NOT_FOUND",
                    "message": "Enrollment record not found in class."
                }
            )
        enrollment = results[0]
        EnrollmentRepository.restore(db, enrollment)
        logger.info("Domain Event: EVT-ACAD-STUDENT_ENROLLMENT_RESTORED - class_id: %s, student_id: %s", class_id, student_id)
        return enrollment
