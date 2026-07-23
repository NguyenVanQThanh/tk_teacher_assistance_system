# File Name: repository.py
# Description: Repository layer for academic module — Subject, Class, Enrollment, and Teacher Assignment database operations.
# Created At: 2026-07-21
# Created By: Tam Khang
# Updated At: 2026-07-23
# Updated By: Tam Khang

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.modules.academic.models import Subject, Class, StudentClass, TeacherSubject


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


class EnrollmentRepository:
    @staticmethod
    def get_enrollment(db: Session, class_id: UUID, student_id: UUID) -> Optional[StudentClass]:
        """Retrieve an enrollment record by composite key (student_id, class_id)."""
        return db.query(StudentClass).filter(
            StudentClass.class_id == class_id,
            StudentClass.student_id == student_id
        ).first()

    @staticmethod
    def get_by_student_code(db: Session, student_code: str) -> Optional[StudentClass]:
        """Retrieve an enrollment record by unique student_code."""
        return db.query(StudentClass).filter(StudentClass.student_code == student_code).first()

    @staticmethod
    def list_by_class_id(db: Session, class_id: UUID) -> List[StudentClass]:
        """Retrieve all enrolled students for a specific class."""
        return db.query(StudentClass).filter(StudentClass.class_id == class_id).all()

    @staticmethod
    def create(
        db: Session,
        class_id: UUID,
        student_id: UUID,
        student_code: Optional[str] = None
    ) -> StudentClass:
        """Insert a new student enrollment record."""
        enrollment = StudentClass(
            class_id=class_id,
            student_id=student_id,
            student_code=student_code
        )
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
        return enrollment

    @staticmethod
    def delete(db: Session, enrollment: StudentClass) -> None:
        """Delete an enrollment record."""
        db.delete(enrollment)
        db.commit()


class TeacherAssignmentRepository:
    @staticmethod
    def get_assignment(
        db: Session,
        class_id: UUID,
        teacher_id: UUID,
        subject_id: UUID
    ) -> Optional[TeacherSubject]:
        """Retrieve a teacher assignment record by composite PK (teacher_id, class_id, subject_id)."""
        return db.query(TeacherSubject).filter(
            TeacherSubject.class_id == class_id,
            TeacherSubject.teacher_id == teacher_id,
            TeacherSubject.subject_id == subject_id
        ).first()

    @staticmethod
    def list_by_class_id(db: Session, class_id: UUID) -> List[TeacherSubject]:
        """Retrieve all teacher assignments for a specific class."""
        return db.query(TeacherSubject).filter(TeacherSubject.class_id == class_id).all()

    @staticmethod
    def create(
        db: Session,
        class_id: UUID,
        teacher_id: UUID,
        subject_id: UUID
    ) -> TeacherSubject:
        """Insert a new teacher assignment record."""
        assignment = TeacherSubject(
            class_id=class_id,
            teacher_id=teacher_id,
            subject_id=subject_id
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment

    @staticmethod
    def delete(db: Session, assignment: TeacherSubject) -> None:
        """Delete a teacher assignment record."""
        db.delete(assignment)
        db.commit()
