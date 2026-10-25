# File Name: subject_service.py
# Description: Service layer for Subject business logic — duplicate check, create, update, delete, restore, and list.
# Created At: 2026-07-21
# Created By: Tam Khang
# Updated At: 2026-07-26
# Updated By: Tam Khang

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.models import User
from app.modules.academic.models import Subject
from app.modules.academic.repository import SubjectRepository
from app.modules.academic.scoping import get_user_role_name, get_accessible_class_ids

logger = logging.getLogger("subject_service")


class SubjectService:
    @staticmethod
    def create_subject(db: Session, subject_name: str, description: Optional[str], status_val: str = "ACTIVE") -> Subject:
        """
        Create a new subject.
        Raises 409 if subject_name already exists.
        """
        existing = SubjectRepository.get_by_name(db, subject_name)
        if existing:
            logger.warning(
                "Domain Event: EVT-ACAD-SUBJECT_CREATED failed — duplicate name: %s", subject_name
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ERR-ACAD-SUBJECT_DUPLICATE_NAME",
                    "message": "Subject name already exists in the system."
                }
            )
        if status_val and status_val != "ACTIVE":
            subject = SubjectRepository.create(db, subject_name, description, status=status_val)
        else:
            subject = SubjectRepository.create(db, subject_name, description)
        logger.info(
            "Domain Event: EVT-ACAD-SUBJECT_CREATED - subject_id: %s, name: %s",
            subject.subject_id, subject.subject_name
        )
        return subject

    @staticmethod
    def list_subjects(
        db: Session,
        status_val: Optional[str] = None,
        current_user: Optional[User] = None
    ) -> List[Subject]:
        """
        Return subjects filtered by status.
        If student, can filter subjects relevant to their enrolled classes.
        """
        if current_user:
            role_name = get_user_role_name(db, current_user)
            if role_name == "Teacher":
                from app.modules.academic.repository import TeacherAssignmentRepository
                assignments = TeacherAssignmentRepository.filter_teacher_assignments(
                    db, teacher_id=current_user.user_id
                )
                subject_ids = list(set(a.subject_id for a in assignments))
                if subject_ids:
                    return SubjectRepository.filter_subjects(
                        db, subject_ids=subject_ids, status=status_val
                    )
            elif role_name == "Student":
                accessible_class_ids = get_accessible_class_ids(db, current_user, role_name)
                if accessible_class_ids is not None:
                    # Find subject_ids from teacher assignments of enrolled classes
                    from app.modules.academic.repository import TeacherAssignmentRepository
                    assignments = TeacherAssignmentRepository.filter_teacher_assignments(
                        db, class_ids=accessible_class_ids
                    )
                    subject_ids = list(set(a.subject_id for a in assignments))
                    if not subject_ids:
                        return []
                    return SubjectRepository.filter_subjects(
                        db, subject_ids=subject_ids, status=status_val
                    )

        if status_val:
            return SubjectRepository.filter_subjects(db, status=status_val)
        return SubjectRepository.filter_subjects(db)

    @staticmethod
    def get_subject(db: Session, subject_id: UUID) -> Subject:
        """
        Return a subject by ID.
        Raises 404 if not found.
        """
        subject = SubjectRepository.get_by_id(db, subject_id)
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-SUBJECT_NOT_FOUND",
                    "message": "Subject not found."
                }
            )
        return subject

    @staticmethod
    def update_subject(
        db: Session,
        subject_id: UUID,
        subject_name: Optional[str] = None,
        description: Optional[str] = None,
        status_val: Optional[str] = None
    ) -> Subject:
        """
        Update a subject.
        Raises 404 if not found.
        Raises 409 if new subject_name conflicts with another subject.
        """
        subject = SubjectService.get_subject(db, subject_id)

        # Check duplicate name — exclude the current subject itself
        if subject_name is not None:
            conflict = SubjectRepository.get_by_name(db, subject_name)
            if conflict and conflict.subject_id != subject.subject_id:
                logger.warning(
                    "Domain Event: EVT-ACAD-SUBJECT_UPDATED failed — duplicate name: %s", subject_name
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "ERR-ACAD-SUBJECT_DUPLICATE_NAME",
                        "message": "Subject name already exists in the system."
                    }
                )

        subject = SubjectRepository.update(db, subject, subject_name, description, status=status_val)
        logger.info(
            "Domain Event: EVT-ACAD-SUBJECT_UPDATED - subject_id: %s", subject.subject_id
        )
        return subject

    @staticmethod
    def delete_subject(db: Session, subject_id: UUID) -> None:
        """
        Delete a subject by ID.
        Raises 404 if not found.
        """
        subject = SubjectService.get_subject(db, subject_id)
        SubjectRepository.delete(db, subject)
        logger.info(
            "Domain Event: EVT-ACAD-SUBJECT_DELETED - subject_id: %s", subject_id
        )

    @staticmethod
    def restore_subject(db: Session, subject_id: UUID) -> Subject:
        """
        Restore a soft-deleted subject for Admin.
        Raises 404 if subject record does not exist.
        """
        results = SubjectRepository.filter_subjects(db, subject_id=subject_id, exclude_status=None)
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-SUBJECT_NOT_FOUND",
                    "message": "Subject not found."
                }
            )
        subject = results[0]
        SubjectRepository.restore(db, subject)
        logger.info("Domain Event: EVT-ACAD-SUBJECT_RESTORED - subject_id: %s", subject_id)
        return subject
