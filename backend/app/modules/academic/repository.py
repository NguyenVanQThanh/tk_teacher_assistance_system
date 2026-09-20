# File Name: repository.py
# Description: Repository layer for academic module — Subject, Class, Enrollment, and Teacher Assignment database operations with flexible optional filtering and restore support.
# Created At: 2026-07-21
# Created By: Tam Khang
# Updated At: 2026-07-26
# Updated By: Tam Khang

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session, joinedload

from app.modules.academic.models import Subject, Class, StudentClass, TeacherSubject


class SubjectRepository:
    @staticmethod
    def filter_subjects(
        db: Session,
        subject_id: Optional[UUID] = None,
        subject_name: Optional[str] = None,
        subject_ids: Optional[List[UUID]] = None,
        status: Optional[str] = None,
        exclude_status: Optional[str] = 'DELETED'
    ) -> List[Subject]:
        """Flexible multi-field filter for subjects."""
        query = db.query(Subject)
        if subject_id is not None:
            query = query.filter(Subject.subject_id == subject_id)
        if subject_name is not None:
            query = query.filter(Subject.subject_name == subject_name)
        if subject_ids is not None:
            query = query.filter(Subject.subject_id.in_(subject_ids))
        if status is not None:
            query = query.filter(Subject.status == status)
        elif exclude_status is not None:
            query = query.filter(Subject.status != exclude_status)
        return query.order_by(Subject.subject_name).all()

    @staticmethod
    def get_by_name(db: Session, subject_name: str) -> Optional[Subject]:
        """Retrieve a non-deleted subject by its unique name."""
        results = SubjectRepository.filter_subjects(db, subject_name=subject_name)
        return results[0] if results else None

    @staticmethod
    def get_by_id(db: Session, subject_id: UUID) -> Optional[Subject]:
        """Retrieve a non-deleted subject by its UUID."""
        results = SubjectRepository.filter_subjects(db, subject_id=subject_id)
        return results[0] if results else None

    @staticmethod
    def list_all(db: Session, status: Optional[str] = None) -> List[Subject]:
        """Retrieve subjects filtered by status or all non-deleted subjects."""
        return SubjectRepository.filter_subjects(db, status=status)

    @staticmethod
    def create(db: Session, subject_name: str, description: Optional[str], status: str = "ACTIVE") -> Subject:
        """Insert a new subject record."""
        subject = Subject(subject_name=subject_name, description=description, status=status)
        db.add(subject)
        db.commit()
        db.refresh(subject)
        return subject

    @staticmethod
    def update(
        db: Session,
        subject: Subject,
        subject_name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None
    ) -> Subject:
        """Update an existing subject record."""
        if subject_name is not None:
            subject.subject_name = subject_name
        if description is not None:
            subject.description = description
        if status is not None:
            subject.status = status
        db.commit()
        db.refresh(subject)
        return subject

    @staticmethod
    def delete(db: Session, subject: Subject) -> None:
        """Soft-delete a subject record by setting status to DELETED."""
        subject.status = 'DELETED'
        db.commit()

    @staticmethod
    def restore(db: Session, subject: Subject, new_status: str = 'ACTIVE') -> Subject:
        """Restore a soft-deleted subject record."""
        subject.status = new_status
        db.commit()
        db.refresh(subject)
        return subject


class ClassRepository:
    @staticmethod
    def filter_classes(
        db: Session,
        class_id: Optional[UUID] = None,
        class_name: Optional[str] = None,
        academic_year: Optional[str] = None,
        homeroom_teacher_id: Optional[UUID] = None,
        class_ids: Optional[List[UUID]] = None,
        status: Optional[str] = None,
        exclude_status: Optional[str] = 'DELETED'
    ) -> List[Class]:
        """Flexible multi-field filter for classes."""
        query = db.query(Class)
        if class_id is not None:
            query = query.filter(Class.class_id == class_id)
        if class_name is not None:
            query = query.filter(Class.class_name == class_name)
        if academic_year is not None:
            query = query.filter(Class.academic_year == academic_year)
        if homeroom_teacher_id is not None:
            query = query.filter(Class.homeroom_teacher_id == homeroom_teacher_id)
        if class_ids is not None:
            query = query.filter(Class.class_id.in_(class_ids))

        if status is not None:
            query = query.filter(Class.status == status)
        elif exclude_status is not None:
            query = query.filter(Class.status != exclude_status)

        return query.order_by(Class.class_name).all()

    @staticmethod
    def get_by_name(db: Session, class_name: str) -> Optional[Class]:
        """Retrieve a non-deleted class by its unique name."""
        results = ClassRepository.filter_classes(db, class_name=class_name)
        return results[0] if results else None

    @staticmethod
    def get_by_id(db: Session, class_id: UUID) -> Optional[Class]:
        """Retrieve a non-deleted class by its UUID."""
        results = ClassRepository.filter_classes(db, class_id=class_id)
        return results[0] if results else None

    @staticmethod
    def list_all(db: Session, status: Optional[str] = None) -> List[Class]:
        """Retrieve all classes filtered by status."""
        return ClassRepository.filter_classes(db, status=status)

    @staticmethod
    def create(
        db: Session,
        class_name: str,
        academic_year: Optional[str] = None,
        homeroom_teacher_id: Optional[UUID] = None,
        status: str = "ACTIVE"
    ) -> Class:
        """Insert a new class record."""
        cls = Class(
            class_name=class_name,
            academic_year=academic_year,
            homeroom_teacher_id=homeroom_teacher_id,
            status=status
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
        update_homeroom_teacher: bool = False,
        status: Optional[str] = None
    ) -> Class:
        """Update an existing class record."""
        if class_name is not None:
            class_obj.class_name = class_name
        if academic_year is not None:
            class_obj.academic_year = academic_year
        if update_homeroom_teacher:
            class_obj.homeroom_teacher_id = homeroom_teacher_id
        if status is not None:
            class_obj.status = status
        db.commit()
        db.refresh(class_obj)
        return class_obj

    @staticmethod
    def delete(db: Session, class_obj: Class) -> None:
        """Soft-delete a class record by setting status to DELETED."""
        class_obj.status = 'DELETED'
        db.commit()

    @staticmethod
    def restore(db: Session, class_obj: Class, new_status: str = 'ACTIVE') -> Class:
        """Restore a soft-deleted class record."""
        class_obj.status = new_status
        db.commit()
        db.refresh(class_obj)
        return class_obj


class EnrollmentRepository:
    @staticmethod
    def filter_enrollments(
        db: Session,
        class_id: Optional[UUID] = None,
        student_id: Optional[UUID] = None,
        student_code: Optional[str] = None,
        class_ids: Optional[List[UUID]] = None,
        status: Optional[str] = None,
        exclude_status: Optional[str] = 'DELETED'
    ) -> List[StudentClass]:
        """Flexible multi-field filter for enrollments."""
        query = db.query(StudentClass).options(joinedload(StudentClass.student))
        if class_id is not None:
            query = query.filter(StudentClass.class_id == class_id)
        if student_id is not None:
            query = query.filter(StudentClass.student_id == student_id)
        if student_code is not None:
            query = query.filter(StudentClass.student_code == student_code)
        if class_ids is not None:
            query = query.filter(StudentClass.class_id.in_(class_ids))

        if status is not None:
            query = query.filter(StudentClass.status == status)
        elif exclude_status is not None:
            query = query.filter(StudentClass.status != exclude_status)

        return query.all()

    @staticmethod
    def get_enrollment(db: Session, class_id: UUID, student_id: UUID) -> Optional[StudentClass]:
        """Retrieve a non-deleted enrollment record by composite key (student_id, class_id)."""
        results = EnrollmentRepository.filter_enrollments(db, class_id=class_id, student_id=student_id)
        return results[0] if results else None

    @staticmethod
    def get_by_student_code(db: Session, student_code: str) -> Optional[StudentClass]:
        """Retrieve a non-deleted enrollment record by unique student_code."""
        results = EnrollmentRepository.filter_enrollments(db, student_code=student_code)
        return results[0] if results else None

    @staticmethod
    def list_by_class_id(db: Session, class_id: UUID, status: Optional[str] = None) -> List[StudentClass]:
        """Retrieve enrolled students for a specific class filtered by status."""
        return EnrollmentRepository.filter_enrollments(db, class_id=class_id, status=status)

    @staticmethod
    def create(
        db: Session,
        class_id: UUID,
        student_id: UUID,
        student_code: Optional[str] = None,
        status: str = "ACTIVE"
    ) -> StudentClass:
        """Insert a new student enrollment record."""
        enrollment = StudentClass(
            class_id=class_id,
            student_id=student_id,
            student_code=student_code,
            status=status
        )
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
        return enrollment

    @staticmethod
    def delete(db: Session, enrollment: StudentClass) -> None:
        """Soft-delete an enrollment record by setting status to DELETED."""
        enrollment.status = 'DELETED'
        db.commit()

    @staticmethod
    def restore(db: Session, enrollment: StudentClass, new_status: str = 'ACTIVE') -> StudentClass:
        """Restore a soft-deleted enrollment record."""
        enrollment.status = new_status
        db.commit()
        db.refresh(enrollment)
        return enrollment


class TeacherAssignmentRepository:
    @staticmethod
    def filter_teacher_assignments(
        db: Session,
        class_id: Optional[UUID] = None,
        teacher_id: Optional[UUID] = None,
        subject_id: Optional[UUID] = None,
        class_ids: Optional[List[UUID]] = None,
        status: Optional[str] = None,
        exclude_status: Optional[str] = 'DELETED'
    ) -> List[TeacherSubject]:
        """Flexible multi-field filter for teacher assignments."""
        query = db.query(TeacherSubject)
        if class_id is not None:
            query = query.filter(TeacherSubject.class_id == class_id)
        if teacher_id is not None:
            query = query.filter(TeacherSubject.teacher_id == teacher_id)
        if subject_id is not None:
            query = query.filter(TeacherSubject.subject_id == subject_id)
        if class_ids is not None:
            query = query.filter(TeacherSubject.class_id.in_(class_ids))

        if status is not None:
            query = query.filter(TeacherSubject.status == status)
        elif exclude_status is not None:
            query = query.filter(TeacherSubject.status != exclude_status)

        return query.all()

    @staticmethod
    def get_assignment(
        db: Session,
        class_id: UUID,
        teacher_id: UUID,
        subject_id: UUID
    ) -> Optional[TeacherSubject]:
        """Retrieve a non-deleted teacher assignment record by composite PK."""
        results = TeacherAssignmentRepository.filter_teacher_assignments(
            db, class_id=class_id, teacher_id=teacher_id, subject_id=subject_id
        )
        return results[0] if results else None

    @staticmethod
    def list_by_class_id(db: Session, class_id: UUID, status: Optional[str] = None) -> List[TeacherSubject]:
        """Retrieve teacher assignments for a specific class filtered by status."""
        return TeacherAssignmentRepository.filter_teacher_assignments(db, class_id=class_id, status=status)

    @staticmethod
    def create(
        db: Session,
        class_id: UUID,
        teacher_id: UUID,
        subject_id: UUID,
        status: str = "ACTIVE"
    ) -> TeacherSubject:
        """Insert a new teacher assignment record."""
        assignment = TeacherSubject(
            class_id=class_id,
            teacher_id=teacher_id,
            subject_id=subject_id,
            status=status
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment

    @staticmethod
    def delete(db: Session, assignment: TeacherSubject) -> None:
        """Soft-delete a teacher assignment record by setting status to DELETED."""
        assignment.status = 'DELETED'
        db.commit()

    @staticmethod
    def restore(db: Session, assignment: TeacherSubject, new_status: str = 'ACTIVE') -> TeacherSubject:
        """Restore a soft-deleted teacher assignment record."""
        assignment.status = new_status
        db.commit()
        db.refresh(assignment)
        return assignment
