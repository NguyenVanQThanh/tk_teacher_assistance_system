# File Name: test_enrollment_service.py
# Description: Unit tests for EnrollmentService — validation, duplicate checks, and CRUD logic.
# Created At: 2026-07-23
# Created By: Tam Khang
# Updated At: 2026-07-23
# Updated By: Tam Khang

import uuid
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.modules.academic.services.enrollment_service import EnrollmentService
from app.modules.academic.models import StudentClass, Class
from models.models import User


def _make_class(class_id: uuid.UUID = None, name: str = "10A1") -> Class:
    cls = Class()
    cls.class_id = class_id or uuid.uuid4()
    cls.class_name = name
    return cls


def _make_enrollment(
    class_id: uuid.UUID = None,
    student_id: uuid.UUID = None,
    student_code: str = None
) -> StudentClass:
    sc = StudentClass()
    sc.class_id = class_id or uuid.uuid4()
    sc.student_id = student_id or uuid.uuid4()
    sc.student_code = student_code
    return sc


class TestEnrollStudent:
    def test_enroll_class_not_found_raises_404(self):
        """Ghi danh vào class_id không tồn tại — raise 404 ERR-ACAD-CLASS_NOT_FOUND."""
        db = MagicMock()
        class_id = uuid.uuid4()
        student_id = uuid.uuid4()

        with patch("app.modules.academic.services.enrollment_service.ClassRepository") as MockClassRepo:
            MockClassRepo.get_by_id.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                EnrollmentService.enroll_student(db, class_id, student_id)

            assert exc_info.value.status_code == 404
            assert exc_info.value.detail["code"] == "ERR-ACAD-CLASS_NOT_FOUND"

    def test_enroll_student_not_found_raises_404(self):
        """Ghi danh với student_id không tồn tại — raise 404 ERR-ACAD-STUDENT_NOT_FOUND."""
        db = MagicMock()
        class_id = uuid.uuid4()
        student_id = uuid.uuid4()

        with patch("app.modules.academic.services.enrollment_service.ClassRepository") as MockClassRepo:
            MockClassRepo.get_by_id.return_value = _make_class(class_id)
            db.query.return_value.filter.return_value.first.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                EnrollmentService.enroll_student(db, class_id, student_id)

            assert exc_info.value.status_code == 404
            assert exc_info.value.detail["code"] == "ERR-ACAD-STUDENT_NOT_FOUND"

    def test_enroll_invalid_role_raises_400(self):
        """Ghi danh với user không phải role Student hoặc Inactive — raise 400 ERR-ACAD-INVALID_STUDENT_ROLE."""
        db = MagicMock()
        class_id = uuid.uuid4()
        student_id = uuid.uuid4()

        with patch("app.modules.academic.services.enrollment_service.ClassRepository") as MockClassRepo:
            MockClassRepo.get_by_id.return_value = _make_class(class_id)

            # User exists
            user_mock = MagicMock(spec=User)
            user_mock.user_id = student_id

            # User query returns user_mock, but join query returns None (not Student/Active)
            db.query.return_value.filter.return_value.first.return_value = user_mock
            db.query.return_value.join.return_value.filter.return_value.first.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                EnrollmentService.enroll_student(db, class_id, student_id)

            assert exc_info.value.status_code == 400
            assert exc_info.value.detail["code"] == "ERR-ACAD-INVALID_STUDENT_ROLE"

    def test_enroll_already_enrolled_raises_409(self):
        """Ghi danh học sinh đã có trong lớp — raise 409 ERR-ACAD-ALREADY_ENROLLED."""
        db = MagicMock()
        class_id = uuid.uuid4()
        student_id = uuid.uuid4()

        with patch("app.modules.academic.services.enrollment_service.ClassRepository") as MockClassRepo, \
             patch("app.modules.academic.services.enrollment_service.EnrollmentRepository") as MockEnrollRepo:

            MockClassRepo.get_by_id.return_value = _make_class(class_id)
            user_mock = MagicMock(spec=User)
            db.query.return_value.filter.return_value.first.return_value = user_mock
            db.query.return_value.join.return_value.filter.return_value.first.return_value = user_mock

            # Already enrolled
            MockEnrollRepo.get_enrollment.return_value = _make_enrollment(class_id, student_id)

            with pytest.raises(HTTPException) as exc_info:
                EnrollmentService.enroll_student(db, class_id, student_id)

            assert exc_info.value.status_code == 409
            assert exc_info.value.detail["code"] == "ERR-ACAD-ALREADY_ENROLLED"

    def test_enroll_duplicate_student_code_raises_409(self):
        """Ghi danh với student_code trùng — raise 409 ERR-ACAD-DUPLICATE_STUDENT_CODE."""
        db = MagicMock()
        class_id = uuid.uuid4()
        student_id = uuid.uuid4()
        student_code = "HS001"

        with patch("app.modules.academic.services.enrollment_service.ClassRepository") as MockClassRepo, \
             patch("app.modules.academic.services.enrollment_service.EnrollmentRepository") as MockEnrollRepo:

            MockClassRepo.get_by_id.return_value = _make_class(class_id)
            user_mock = MagicMock(spec=User)
            db.query.return_value.filter.return_value.first.return_value = user_mock
            db.query.return_value.join.return_value.filter.return_value.first.return_value = user_mock

            MockEnrollRepo.get_enrollment.return_value = None
            MockEnrollRepo.get_by_student_code.return_value = _make_enrollment(student_code=student_code)

            with pytest.raises(HTTPException) as exc_info:
                EnrollmentService.enroll_student(db, class_id, student_id, student_code)

            assert exc_info.value.status_code == 409
            assert exc_info.value.detail["code"] == "ERR-ACAD-DUPLICATE_STUDENT_CODE"

    def test_enroll_success(self):
        """Ghi danh học sinh hợp lệ — thành công."""
        db = MagicMock()
        class_id = uuid.uuid4()
        student_id = uuid.uuid4()
        student_code = "HS001"

        with patch("app.modules.academic.services.enrollment_service.ClassRepository") as MockClassRepo, \
             patch("app.modules.academic.services.enrollment_service.EnrollmentRepository") as MockEnrollRepo:

            MockClassRepo.get_by_id.return_value = _make_class(class_id)
            user_mock = MagicMock(spec=User)
            db.query.return_value.filter.return_value.first.return_value = user_mock
            db.query.return_value.join.return_value.filter.return_value.first.return_value = user_mock

            MockEnrollRepo.get_enrollment.return_value = None
            MockEnrollRepo.get_by_student_code.return_value = None

            created = _make_enrollment(class_id, student_id, student_code)
            MockEnrollRepo.create.return_value = created

            res = EnrollmentService.enroll_student(db, class_id, student_id, student_code)

            assert res.class_id == class_id
            assert res.student_id == student_id
            assert res.student_code == student_code
            MockEnrollRepo.create.assert_called_once_with(
                db=db,
                class_id=class_id,
                student_id=student_id,
                student_code=student_code
            )


class TestListStudentsInClass:
    def test_list_students_class_not_found_raises_404(self):
        """Liệt kê danh sách HS của lớp không tồn tại — raise 404 ERR-ACAD-CLASS_NOT_FOUND."""
        db = MagicMock()
        class_id = uuid.uuid4()

        with patch("app.modules.academic.services.enrollment_service.ClassRepository") as MockClassRepo:
            MockClassRepo.get_by_id.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                EnrollmentService.list_students_in_class(db, class_id)

            assert exc_info.value.status_code == 404
            assert exc_info.value.detail["code"] == "ERR-ACAD-CLASS_NOT_FOUND"

    def test_list_students_success(self):
        """Liệt kê danh sách HS của lớp hợp lệ — thành công."""
        db = MagicMock()
        class_id = uuid.uuid4()

        with patch("app.modules.academic.services.enrollment_service.ClassRepository") as MockClassRepo, \
             patch("app.modules.academic.services.enrollment_service.EnrollmentRepository") as MockEnrollRepo:

            MockClassRepo.get_by_id.return_value = _make_class(class_id)
            records = [_make_enrollment(class_id=class_id)]
            MockEnrollRepo.list_by_class_id.return_value = records

            res = EnrollmentService.list_students_in_class(db, class_id)

            assert res == records
            MockEnrollRepo.list_by_class_id.assert_called_once_with(db, class_id)


class TestUnenrollStudent:
    def test_unenroll_class_not_found_raises_404(self):
        """Hủy ghi danh từ lớp không tồn tại — raise 404 ERR-ACAD-CLASS_NOT_FOUND."""
        db = MagicMock()
        class_id = uuid.uuid4()
        student_id = uuid.uuid4()

        with patch("app.modules.academic.services.enrollment_service.ClassRepository") as MockClassRepo:
            MockClassRepo.get_by_id.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                EnrollmentService.unenroll_student(db, class_id, student_id)

            assert exc_info.value.status_code == 404
            assert exc_info.value.detail["code"] == "ERR-ACAD-CLASS_NOT_FOUND"

    def test_unenroll_enrollment_not_found_raises_404(self):
        """Hủy ghi danh HS chưa từng vào lớp — raise 404 ERR-ACAD-ENROLLMENT_NOT_FOUND."""
        db = MagicMock()
        class_id = uuid.uuid4()
        student_id = uuid.uuid4()

        with patch("app.modules.academic.services.enrollment_service.ClassRepository") as MockClassRepo, \
             patch("app.modules.academic.services.enrollment_service.EnrollmentRepository") as MockEnrollRepo:

            MockClassRepo.get_by_id.return_value = _make_class(class_id)
            MockEnrollRepo.get_enrollment.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                EnrollmentService.unenroll_student(db, class_id, student_id)

            assert exc_info.value.status_code == 404
            assert exc_info.value.detail["code"] == "ERR-ACAD-ENROLLMENT_NOT_FOUND"

    def test_unenroll_success(self):
        """Hủy ghi danh thành công."""
        db = MagicMock()
        class_id = uuid.uuid4()
        student_id = uuid.uuid4()

        with patch("app.modules.academic.services.enrollment_service.ClassRepository") as MockClassRepo, \
             patch("app.modules.academic.services.enrollment_service.EnrollmentRepository") as MockEnrollRepo:

            MockClassRepo.get_by_id.return_value = _make_class(class_id)
            existing = _make_enrollment(class_id, student_id)
            MockEnrollRepo.get_enrollment.return_value = existing

            EnrollmentService.unenroll_student(db, class_id, student_id)

            MockEnrollRepo.delete.assert_called_once_with(db, existing)
