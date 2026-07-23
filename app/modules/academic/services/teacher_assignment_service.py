# File Name: teacher_assignment_service.py
# Description: Service layer for Teacher Assignment business logic — validation of class, subject, teacher role/status, duplicate checks, CRUD.
# Created At: 2026-07-23
# Created By: Tam Khang
# Updated At: 2026-07-23
# Updated By: Tam Khang

import logging
from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.models import User, Role
from app.modules.academic.models import TeacherSubject
from app.modules.academic.repository import (
    ClassRepository,
    SubjectRepository,
    TeacherAssignmentRepository,
)

logger = logging.getLogger("teacher_assignment_service")


class TeacherAssignmentService:
    @staticmethod
    def assign_teacher(
        db: Session,
        class_id: UUID,
        teacher_id: UUID,
        subject_id: UUID
    ) -> TeacherSubject:
        """
        Assign a teacher to teach a subject in a class.
        Raises 404 ERR-ACAD-CLASS_NOT_FOUND if class does not exist.
        Raises 404 ERR-ACAD-SUBJECT_NOT_FOUND if subject does not exist.
        Raises 400 ERR-ACAD-INVALID_TEACHER_ROLE if user is not role Teacher or status is not Active.
        Raises 409 ERR-ACAD-ASSIGNMENT_EXISTS if assignment already exists.
        """
        # 1. Validate class_id exists
        cls = ClassRepository.get_by_id(db, class_id)
        if not cls:
            logger.warning("Teacher assignment failed — class_id not found: %s", class_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-CLASS_NOT_FOUND",
                    "message": "Lớp học không tồn tại."
                }
            )

        # 2. Validate subject_id exists
        subject = SubjectRepository.get_by_id(db, subject_id)
        if not subject:
            logger.warning("Teacher assignment failed — subject_id not found: %s", subject_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-SUBJECT_NOT_FOUND",
                    "message": "Môn học không tồn tại."
                }
            )

        # 3. Validate teacher_id role Teacher + status Active
        valid_teacher = (
            db.query(User)
            .join(Role, User.role_id == Role.role_id)
            .filter(
                User.user_id == teacher_id,
                Role.name == "Teacher",
                User.status == "Active"
            )
            .first()
        )
        if not valid_teacher:
            logger.warning(
                "Teacher assignment failed — user %s is not active Teacher", teacher_id
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "ERR-ACAD-INVALID_TEACHER_ROLE",
                    "message": "Giáo viên không hợp lệ (phải có vai trò Teacher và trạng thái Active)."
                }
            )

        # 4. Validate not already assigned
        existing = TeacherAssignmentRepository.get_assignment(
            db, class_id=class_id, teacher_id=teacher_id, subject_id=subject_id
        )
        if existing:
            logger.warning(
                "Teacher assignment failed — assignment exists for teacher %s, class %s, subject %s",
                teacher_id, class_id, subject_id
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ERR-ACAD-ASSIGNMENT_EXISTS",
                    "message": "Phân công giáo viên cho môn học ở lớp này đã tồn tại."
                }
            )

        # 5. Insert assignment record
        assignment = TeacherAssignmentRepository.create(
            db=db,
            class_id=class_id,
            teacher_id=teacher_id,
            subject_id=subject_id
        )
        logger.info(
            "Domain Event: EVT-ACAD-TEACHER_ASSIGNED - class_id: %s, teacher_id: %s, subject_id: %s",
            class_id, teacher_id, subject_id
        )
        return assignment

    @staticmethod
    def list_assignments_in_class(db: Session, class_id: UUID) -> List[TeacherSubject]:
        """
        List all teacher assignments for a specific class.
        Raises 404 ERR-ACAD-CLASS_NOT_FOUND if class does not exist.
        """
        cls = ClassRepository.get_by_id(db, class_id)
        if not cls:
            logger.warning("List teacher assignments failed — class_id not found: %s", class_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-CLASS_NOT_FOUND",
                    "message": "Lớp học không tồn tại."
                }
            )
        return TeacherAssignmentRepository.list_by_class_id(db, class_id)

    @staticmethod
    def unassign_teacher(
        db: Session,
        class_id: UUID,
        teacher_id: UUID,
        subject_id: UUID
    ) -> None:
        """
        Unassign a teacher from teaching a subject in a class.
        Raises 404 ERR-ACAD-CLASS_NOT_FOUND if class does not exist.
        Raises 404 ERR-ACAD-ASSIGNMENT_NOT_FOUND if assignment does not exist.
        """
        cls = ClassRepository.get_by_id(db, class_id)
        if not cls:
            logger.warning("Unassign teacher failed — class_id not found: %s", class_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-CLASS_NOT_FOUND",
                    "message": "Lớp học không tồn tại."
                }
            )

        assignment = TeacherAssignmentRepository.get_assignment(
            db, class_id=class_id, teacher_id=teacher_id, subject_id=subject_id
        )
        if not assignment:
            logger.warning(
                "Unassign teacher failed — assignment not found for teacher %s, class %s, subject %s",
                teacher_id, class_id, subject_id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-ASSIGNMENT_NOT_FOUND",
                    "message": "Bản ghi phân công không tồn tại."
                }
            )

        TeacherAssignmentRepository.delete(db, assignment)
        logger.info(
            "Domain Event: EVT-ACAD-TEACHER_UNASSIGNED - class_id: %s, teacher_id: %s, subject_id: %s",
            class_id, teacher_id, subject_id
        )
