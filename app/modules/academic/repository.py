# File Name: repository.py
# Description: Repository layer for academic module — Subject and Class database operations.
# Created At: 2026-07-21
# Created By: Tam Khang
# Updated At: 2026-07-22
# Updated By: Tam Khang

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.modules.academic.models import Subject, Class


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


class ClassRepository:
    @staticmethod
    def get_by_name(db: Session, class_name: str) -> Optional[Class]:
        """Retrieve a class by its unique name."""
        return db.query(Class).filter(Class.class_name == class_name).first()

    @staticmethod
    def get_by_id(db: Session, class_id: UUID) -> Optional[Class]:
        """Retrieve a class by its UUID."""
        return db.query(Class).filter(Class.class_id == class_id).first()

    @staticmethod
    def list_all(db: Session) -> List[Class]:
        """Retrieve all classes ordered by class_name."""
        return db.query(Class).order_by(Class.class_name).all()

    @staticmethod
    def create(
        db: Session,
        class_name: str,
        academic_year: Optional[str] = None,
        homeroom_teacher_id: Optional[UUID] = None
    ) -> Class:
        """Insert a new class record."""
        cls = Class(
            class_name=class_name,
            academic_year=academic_year,
            homeroom_teacher_id=homeroom_teacher_id
        )
        db.add(cls)
        db.commit()
        db.refresh(cls)
        return cls

    @staticmethod
    def update(
        db: Session,
        class_obj: Class,
        class_name: Optional[str] = None,
        academic_year: Optional[str] = None,
        homeroom_teacher_id: Optional[UUID] = None,
        update_homeroom_teacher: bool = False
    ) -> Class:
        """Update an existing class record."""
        if class_name is not None:
            class_obj.class_name = class_name
        if academic_year is not None:
            class_obj.academic_year = academic_year
        if update_homeroom_teacher:
            class_obj.homeroom_teacher_id = homeroom_teacher_id
        db.commit()
        db.refresh(class_obj)
        return class_obj

    @staticmethod
    def delete(db: Session, class_obj: Class) -> None:
        """Hard-delete a class record."""
        db.delete(class_obj)
        db.commit()

