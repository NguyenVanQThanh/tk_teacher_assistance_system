# File Name: subject_service.py
# Description: Service layer for Subject business logic — duplicate check, create, update, delete.
# Created At: 2026-07-21
# Created By: Tam Khang
# Updated At: 2026-07-21
# Updated By: Tam Khang

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.academic.models import Subject
from app.modules.academic.repository import SubjectRepository

logger = logging.getLogger("subject_service")


class SubjectService:
    @staticmethod
    def create_subject(db: Session, subject_name: str, description: Optional[str]) -> Subject:
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
                    "message": "Tên môn học đã tồn tại trong hệ thống."
                }
            )
        subject = SubjectRepository.create(db, subject_name, description)
        logger.info(
            "Domain Event: EVT-ACAD-SUBJECT_CREATED - subject_id: %s, name: %s",
            subject.subject_id, subject.subject_name
        )
        return subject

    @staticmethod
    def list_subjects(db: Session) -> List[Subject]:
        """Return all subjects."""
        return SubjectRepository.list_all(db)

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
                    "message": "Môn học không tồn tại."
                }
            )
        return subject

    @staticmethod
    def update_subject(
        db: Session,
        subject_id: UUID,
        subject_name: Optional[str],
        description: Optional[str]
    ) -> Subject:
        """
        Update a subject.
        Raises 404 if not found.
        Raises 409 if new subject_name conflicts with another subject.
        """
        subject = SubjectService.get_subject(db, subject_id)

        # Check duplicate name — exclude the current subject itself (EC-04)
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
                        "message": "Tên môn học đã tồn tại trong hệ thống."
                    }
                )

        subject = SubjectRepository.update(db, subject, subject_name, description)
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
