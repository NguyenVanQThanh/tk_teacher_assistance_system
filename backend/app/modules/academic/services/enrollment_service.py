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
        student_id: Optional[UUID] = None,
        student_code: Optional[str] = None,
        status_val: str = "ACTIVE",
        student_name: Optional[str] = None,
        birthday: Optional[object] = None,
        phone: Optional[str] = None,
        gender: Optional[str] = None
    ) -> StudentClass:
        """
        Enroll a student into a class, creating the student user first if not yet existing.
        Enforces age constraint: Student must be at least 16 years old.
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

        # 2. If student_id is not provided, auto-create student user
        from datetime import date
        if not student_id:
            if not student_name or not student_name.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "ERR-ACAD-MISSING_STUDENT_INFO",
                        "message": "Either student_id or student_name must be provided."
                    }
                )

            # Age validation (Student >= 16)
            if birthday:
                today = date.today()
                b_date = birthday if isinstance(birthday, date) else date.fromisoformat(str(birthday))
                age = today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
                if age < 16:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "code": "ERR-USER-INVALID_AGE_STUDENT",
                            "message": f"Student must be at least 16 years old. (Calculated age: {age})"
                        }
                    )

            import uuid as py_uuid
            from app.core.security import get_password_hash
            student_role = db.query(Role).filter(Role.name == "Student").first()
            if not student_role:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"code": "ERR-ACAD-ROLE_NOT_FOUND", "message": "Student role not found in system."}
                )

            new_user_id = py_uuid.uuid4()
            b_date_val = birthday if isinstance(birthday, date) else (date.fromisoformat(str(birthday)) if birthday else None)
            new_user = User(
                user_id=new_user_id,
                full_name=student_name.strip(),
                phone=phone or None,
                birthday=b_date_val,
                role_id=student_role.role_id,
                password_hash=get_password_hash("Student@1234"),
                status="ACTIVE"
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            student_id = new_user_id

        # 3. Validate student_id exists
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

        # 4. Validate user role Student + status Active
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
