# File Name: test_student_import_atomic.py
# Description: Tests that bulk student import is atomic per row and creates no usable default password.
# Created At: 2026-11-15
# Created By: AI Agent
# Updated At: 2026-11-15
# Updated By: AI Agent

import uuid

from app.core.security import verify_password
from app.modules.academic.services.enrollment_service import EnrollmentService
from models.models import Class, StudentClass, User


def _make_class(db_session) -> Class:
    cls = Class(class_name=f"IMP{uuid.uuid4().hex[:6]}", academic_year="2025-2026", status="ACTIVE")
    db_session.add(cls)
    db_session.commit()
    return cls


def _phone() -> str:
    return f"09{uuid.uuid4().int % 100000000:08d}"


def test_import_creates_user_and_enrollment_without_default_password(db_session):
    cls = _make_class(db_session)
    phone = _phone()
    result = EnrollmentService.import_students_from_rows(
        db_session, cls.class_id, [{"full_name": "Atomic Student", "phone": phone, "birthday": "2005-01-01"}]
    )
    assert result.imported_count == 1 and not result.errors
    user = db_session.query(User).filter(User.phone == phone).one()
    assert not verify_password("Student@1234", user.password_hash)
    assert db_session.query(StudentClass).filter(StudentClass.student_id == user.user_id).count() == 1


def test_failed_row_leaves_no_orphan_user_and_later_rows_still_import(db_session):
    cls = _make_class(db_session)
    dup_code = f"C{uuid.uuid4().hex[:8]}"
    good_phone, dup_phone, ok_phone = _phone(), _phone(), _phone()
    rows = [
        {"full_name": "First", "phone": good_phone, "student_code": dup_code, "birthday": "2005-01-01"},
        # Same student code in the same class: second row must be rejected as a unit.
        {"full_name": "Second", "phone": dup_phone, "student_code": dup_code, "birthday": "2005-01-01"},
        {"full_name": "Third", "phone": ok_phone, "birthday": "2005-01-01"},
    ]
    result = EnrollmentService.import_students_from_rows(db_session, cls.class_id, rows)
    assert result.imported_count == 2
    assert len(result.errors) == 1
    assert db_session.query(User).filter(User.phone == dup_phone).count() == 0
    assert db_session.query(User).filter(User.phone == ok_phone).count() == 1


def test_soft_deleted_email_is_reported_not_crashing(db_session):
    cls = _make_class(db_session)
    phone = _phone()
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    first = EnrollmentService.import_students_from_rows(
        db_session, cls.class_id,
        [{"full_name": "To Delete", "phone": phone, "email": email, "birthday": "2005-01-01"}],
    )
    assert first.imported_count == 1
    db_session.query(User).filter(User.phone == phone).update({"status": "DELETED"})
    db_session.commit()
    again = EnrollmentService.import_students_from_rows(
        db_session, cls.class_id,
        [{"full_name": "Reuse Email", "phone": _phone(), "email": email, "birthday": "2005-01-01"}],
    )
    assert again.imported_count == 0
    assert "deleted account" in again.errors[0].message
