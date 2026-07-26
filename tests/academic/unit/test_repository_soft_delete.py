# File Name: test_repository_soft_delete.py
# Description: Unit tests verifying soft delete functionality across SubjectRepository, ClassRepository, EnrollmentRepository, and TeacherAssignmentRepository using status='DELETED'.
# Created At: 2026-07-25
# Created By: Tam Khang
# Updated At: 2026-07-26
# Updated By: Tam Khang

import uuid
import pytest
from sqlalchemy.orm import Session

from models.models import User, Role, Subject, Class, StudentClass, TeacherSubject
from app.modules.academic.repository import (
    SubjectRepository,
    ClassRepository,
    EnrollmentRepository,
    TeacherAssignmentRepository,
)


class TestSubjectSoftDelete:
    def test_subject_soft_delete(self, db_session: Session):
        """Verify soft deleting a subject sets status='DELETED' and excludes it from active queries."""
        subject = SubjectRepository.create(db_session, "Vật Lý SoftDelete", "Mô tả test")
        sid = subject.subject_id

        # Before delete: retrievable
        assert SubjectRepository.get_by_id(db_session, sid) is not None
        assert SubjectRepository.get_by_name(db_session, "Vật Lý SoftDelete") is not None
        assert any(s.subject_id == sid for s in SubjectRepository.list_all(db_session))

        # Perform delete
        SubjectRepository.delete(db_session, subject)

        # After soft delete: hidden from repo queries
        assert SubjectRepository.get_by_id(db_session, sid) is None
        assert SubjectRepository.get_by_name(db_session, "Vật Lý SoftDelete") is None
        assert not any(s.subject_id == sid for s in SubjectRepository.list_all(db_session))

        # Record still exists in database with status='DELETED'
        raw_record = db_session.query(Subject).filter(Subject.subject_id == sid).first()
        assert raw_record is not None
        assert raw_record.status == 'DELETED'


class TestClassSoftDelete:
    def test_class_soft_delete(self, db_session: Session):
        """Verify soft deleting a class sets status='DELETED' and excludes it from active queries."""
        cls = ClassRepository.create(db_session, "Lớp 12A-SoftDelete", "2025-2026")
        cid = cls.class_id

        # Before delete: retrievable
        assert ClassRepository.get_by_id(db_session, cid) is not None
        assert ClassRepository.get_by_name(db_session, "Lớp 12A-SoftDelete") is not None
        assert any(c.class_id == cid for c in ClassRepository.list_all(db_session))

        # Perform delete
        ClassRepository.delete(db_session, cls)

        # After soft delete: hidden from repo queries
        assert ClassRepository.get_by_id(db_session, cid) is None
        assert ClassRepository.get_by_name(db_session, "Lớp 12A-SoftDelete") is None
        assert not any(c.class_id == cid for c in ClassRepository.list_all(db_session))

        # Record still exists in database with status='DELETED'
        raw_record = db_session.query(Class).filter(Class.class_id == cid).first()
        assert raw_record is not None
        assert raw_record.status == 'DELETED'


class TestEnrollmentSoftDelete:
    def test_enrollment_soft_delete(self, db_session: Session):
        """Verify soft deleting an enrollment sets status='DELETED' and excludes it from active queries."""
        cls = ClassRepository.create(db_session, "Lớp 10B-SoftDelete")
        cid = cls.class_id

        # Create a test student user
        student_role = db_session.query(Role).filter(Role.name == "Student").first()
        student = User(
            user_id=uuid.uuid4(),
            phone="0911222333",
            email="softdelete_student@test.com",
            password_hash="hashed",
            full_name="SoftDelete Student",
            role_id=student_role.role_id,
            status="ACTIVE"
        )
        db_session.add(student)
        db_session.commit()

        enrollment = EnrollmentRepository.create(db_session, cid, student.user_id, "STU-SOFT-01")

        # Before delete: retrievable
        assert EnrollmentRepository.get_enrollment(db_session, cid, student.user_id) is not None
        assert EnrollmentRepository.get_by_student_code(db_session, "STU-SOFT-01") is not None
        assert len(EnrollmentRepository.list_by_class_id(db_session, cid)) == 1

        # Perform delete
        EnrollmentRepository.delete(db_session, enrollment)

        # After soft delete: hidden from repo queries
        assert EnrollmentRepository.get_enrollment(db_session, cid, student.user_id) is None
        assert EnrollmentRepository.get_by_student_code(db_session, "STU-SOFT-01") is None
        assert len(EnrollmentRepository.list_by_class_id(db_session, cid)) == 0

        # Record still exists in DB with status='DELETED'
        raw_record = db_session.query(StudentClass).filter(
            StudentClass.class_id == cid,
            StudentClass.student_id == student.user_id
        ).first()
        assert raw_record is not None
        assert raw_record.status == 'DELETED'


class TestTeacherAssignmentSoftDelete:
    def test_teacher_assignment_soft_delete(self, db_session: Session):
        """Verify soft deleting a teacher assignment sets status='DELETED' and excludes it from active queries."""
        cls = ClassRepository.create(db_session, "Lớp 11C-SoftDelete")
        subject = SubjectRepository.create(db_session, "Sinh Học SoftDelete", None)
        teacher_role = db_session.query(Role).filter(Role.name == "Teacher").first()
        teacher = User(
            user_id=uuid.uuid4(),
            phone="0944555666",
            email="softdelete_teacher@test.com",
            password_hash="hashed",
            full_name="SoftDelete Teacher",
            role_id=teacher_role.role_id,
            status="ACTIVE"
        )
        db_session.add(teacher)
        db_session.commit()

        assignment = TeacherAssignmentRepository.create(db_session, cls.class_id, teacher.user_id, subject.subject_id)

        # Before delete: retrievable
        assert TeacherAssignmentRepository.get_assignment(db_session, cls.class_id, teacher.user_id, subject.subject_id) is not None
        assert len(TeacherAssignmentRepository.list_by_class_id(db_session, cls.class_id)) == 1

        # Perform delete
        TeacherAssignmentRepository.delete(db_session, assignment)

        # After soft delete: hidden from repo queries
        assert TeacherAssignmentRepository.get_assignment(db_session, cls.class_id, teacher.user_id, subject.subject_id) is None
        assert len(TeacherAssignmentRepository.list_by_class_id(db_session, cls.class_id)) == 0

        # Record still exists in DB with status='DELETED'
        raw_record = db_session.query(TeacherSubject).filter(
            TeacherSubject.class_id == cls.class_id,
            TeacherSubject.teacher_id == teacher.user_id,
            TeacherSubject.subject_id == subject.subject_id
        ).first()
        assert raw_record is not None
        assert raw_record.status == 'DELETED'
