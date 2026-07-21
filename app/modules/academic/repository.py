# File Name: repository.py
# Description: Repository layer for academic module — Subject database operations.
# Created At: 2026-07-21
# Created By: Tam Khang
# Updated At: 2026-07-21
# Updated By: Tam Khang

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.modules.academic.models import Subject


class SubjectRepository:
    @staticmethod
    def get_by_name(db: Session, subject_name: str) -> Optional[Subject]:
        """Retrieve a subject by its unique name."""
        return db.query(Subject).filter(Subject.subject_name == subject_name).first()

    @staticmethod
    def get_by_id(db: Session, subject_id: UUID) -> Optional[Subject]:
        """Retrieve a subject by its UUID."""
        return db.query(Subject).filter(Subject.subject_id == subject_id).first()

    @staticmethod
    def list_all(db: Session) -> List[Subject]:
        """Retrieve all subjects ordered by name."""
        return db.query(Subject).order_by(Subject.subject_name).all()

    @staticmethod
    def create(db: Session, subject_name: str, description: Optional[str]) -> Subject:
        """Insert a new subject record."""
        subject = Subject(subject_name=subject_name, description=description)
        db.add(subject)
        db.commit()
        db.refresh(subject)
        return subject

    @staticmethod
    def update(db: Session, subject: Subject, subject_name: Optional[str], description: Optional[str]) -> Subject:
        """Update an existing subject record."""
        if subject_name is not None:
            subject.subject_name = subject_name
        if description is not None:
            subject.description = description
        db.commit()
        db.refresh(subject)
        return subject

    @staticmethod
    def delete(db: Session, subject: Subject) -> None:
        """Hard-delete a subject record."""
        db.delete(subject)
        db.commit()
