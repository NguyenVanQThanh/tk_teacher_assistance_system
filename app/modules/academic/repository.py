# File Name: repository.py
# Description: Repository layer for academic module — Subject, Class, Enrollment, and Teacher Assignment database operations with soft-delete support.
# Created At: 2026-07-21
# Created By: Tam Khang
# Updated At: 2026-07-25
# Updated By: Tam Khang

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.modules.academic.models import Subject, Class, StudentClass, TeacherSubject


class SubjectRepository:
    @staticmethod
    def get_by_name(db: Session, subject_name: str) -> Optional[Subject]:
        """Retrieve an active subject by its unique name."""
        return db.query(Subject).filter(
            Subject.subject_name == subject_name,
            Subject.is_deleted == False
        ).first()

    @staticmethod
    def get_by_id(db: Session, subject_id: UUID) -> Optional[Subject]:
        """Retrieve an active subject by its UUID."""
        return db.query(Subject).filter(
            Subject.subject_id == subject_id,
            Subject.is_deleted == False
        ).first()

    @staticmethod
    def list_all(db: Session) -> List[Subject]:
        """Retrieve all active subjects ordered by name."""
        return db.query(Subject).filter(
            Subject.is_deleted == False
        ).order_by(Subject.subject_name).all()

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
        """Soft-delete a subject record."""
        subject.is_deleted = True
        db.commit()


class ClassRepository:
    @staticmethod
    def get_by_name(db: Session, class_name: str) -> Optional[Class]:
        """Retrieve an active class by its unique name."""
        return db.query(Class).filter(
            Class.class_name == class_name,
            Class.is_deleted == False
        ).first()

    @staticmethod
    def get_by_id(db: Session, class_id: UUID) -> Optional[Class]:
        """Retrieve an active class by its UUID."""
        return db.query(Class).filter(
            Class.class_id == class_id,
            Class.is_deleted == False
        ).first()

    @staticmethod
    def list_all(db: Session) -> List[Class]:
        """Retrieve all active classes ordered by class_name."""
        return db.query(Class).filter(
            Class.is_deleted == False
        ).order_by(Class.class_name).all()

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
        """Soft-delete a class record."""
        class_obj.is_deleted = True
        db.commit()


class EnrollmentRepository:
    @staticmethod
    def get_enrollment(db: Session, class_id: UUID, student_id: UUID) -> Optional[StudentClass]:
        """Retrieve an active enrollment record by composite key (student_id, class_id)."""
        return db.query(StudentClass).filter(
            StudentClass.class_id == class_id,
            StudentClass.student_id == student_id,
            StudentClass.is_deleted == False
        ).first()

    @staticmethod
    def get_by_student_code(db: Session, student_code: str) -> Optional[StudentClass]:
        """Retrieve an active enrollment record by unique student_code."""
        return db.query(StudentClass).filter(
            StudentClass.student_code == student_code,
            StudentClass.is_deleted == False
        ).first()

    @staticmethod
    def list_by_class_id(db: Session, class_id: UUID) -> List[StudentClass]:
        """Retrieve all active enrolled students for a specific class."""
        return db.query(StudentClass).filter(
            StudentClass.class_id == class_id,
            StudentClass.is_deleted == False
        ).all()

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
        """Soft-delete an enrollment record."""
        enrollment.is_deleted = True
        db.commit()


class TeacherAssignmentRepository:
    @staticmethod
    def get_assignment(
        db: Session,
        class_id: UUID,
        teacher_id: UUID,
        subject_id: UUID
    ) -> Optional[TeacherSubject]:
        """Retrieve an active teacher assignment record by composite PK (teacher_id, class_id, subject_id)."""
        return db.query(TeacherSubject).filter(
            TeacherSubject.class_id == class_id,
            TeacherSubject.teacher_id == teacher_id,
            TeacherSubject.subject_id == subject_id,
            TeacherSubject.is_deleted == False
        ).first()

    @staticmethod
    def list_by_class_id(db: Session, class_id: UUID) -> List[TeacherSubject]:
        """Retrieve all active teacher assignments for a specific class."""
        return db.query(TeacherSubject).filter(
            TeacherSubject.class_id == class_id,
            TeacherSubject.is_deleted == False
        ).all()

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
        """Soft-delete a teacher assignment record."""
        assignment.is_deleted = True
        db.commit()
