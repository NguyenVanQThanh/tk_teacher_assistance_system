# File Name: test_teacher_assignment_service.py
# Description: Unit tests for TeacherAssignmentService — validation, duplicate check, and CRUD logic.
# Created At: 2026-07-23
# Created By: Tam Khang
# Updated At: 2026-07-23
# Updated By: Tam Khang

import uuid
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.modules.academic.services.teacher_assignment_service import TeacherAssignmentService
from app.modules.academic.models import TeacherSubject, Class, Subject
from models.models import User


def _make_class(class_id: uuid.UUID = None, name: str = "10A1") -> Class:
    cls = Class()
    cls.class_id = class_id or uuid.uuid4()
    cls.class_name = name
    return cls


def _make_subject(subject_id: uuid.UUID = None, name: str = "Toan") -> Subject:
    subj = Subject()
    subj.subject_id = subject_id or uuid.uuid4()
    subj.subject_name = name
    return subj


def _make_assignment(
    class_id: uuid.UUID = None,
    teacher_id: uuid.UUID = None,
    subject_id: uuid.UUID = None
) -> TeacherSubject:
    ts = TeacherSubject()
    ts.class_id = class_id or uuid.uuid4()
    ts.teacher_id = teacher_id or uuid.uuid4()
    ts.subject_id = subject_id or uuid.uuid4()
    return ts


class TestAssignTeacher:
    def test_assign_teacher_class_not_found_raises_404(self):
        """Phân công vào class_id không tồn tại — raise 404 ERR-ACAD-CLASS_NOT_FOUND."""
        db = MagicMock()
        class_id = uuid.uuid4()
        teacher_id = uuid.uuid4()
        subject_id = uuid.uuid4()

        with patch("app.modules.academic.services.teacher_assignment_service.ClassRepository") as MockClassRepo:
            MockClassRepo.get_by_id.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                TeacherAssignmentService.assign_teacher(db, class_id, teacher_id, subject_id)

            assert exc_info.value.status_code == 404
            assert exc_info.value.detail["code"] == "ERR-ACAD-CLASS_NOT_FOUND"

    def test_assign_teacher_subject_not_found_raises_404(self):
        """Phân công với subject_id không tồn tại — raise 404 ERR-ACAD-SUBJECT_NOT_FOUND."""
        db = MagicMock()
        class_id = uuid.uuid4()
        teacher_id = uuid.uuid4()
        subject_id = uuid.uuid4()

        with patch("app.modules.academic.services.teacher_assignment_service.ClassRepository") as MockClassRepo, \
             patch("app.modules.academic.services.teacher_assignment_service.SubjectRepository") as MockSubjectRepo:

            MockClassRepo.get_by_id.return_value = _make_class(class_id)
            MockSubjectRepo.get_by_id.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                TeacherAssignmentService.assign_teacher(db, class_id, teacher_id, subject_id)

            assert exc_info.value.status_code == 404
            assert exc_info.value.detail["code"] == "ERR-ACAD-SUBJECT_NOT_FOUND"

    def test_assign_teacher_invalid_role_raises_400(self):
        """Phân công với user không phải Teacher hoặc Inactive — raise 400 ERR-ACAD-INVALID_TEACHER_ROLE."""
        db = MagicMock()
        class_id = uuid.uuid4()
        teacher_id = uuid.uuid4()
        subject_id = uuid.uuid4()

        with patch("app.modules.academic.services.teacher_assignment_service.ClassRepository") as MockClassRepo, \
             patch("app.modules.academic.services.teacher_assignment_service.SubjectRepository") as MockSubjectRepo:

            MockClassRepo.get_by_id.return_value = _make_class(class_id)
            MockSubjectRepo.get_by_id.return_value = _make_subject(subject_id)

            user_mock = MagicMock(spec=User)
            user_mock.user_id = teacher_id

            db.query.return_value.filter.return_value.first.return_value = user_mock
            db.query.return_value.join.return_value.filter.return_value.first.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                TeacherAssignmentService.assign_teacher(db, class_id, teacher_id, subject_id)

            assert exc_info.value.status_code == 400
            assert exc_info.value.detail["code"] == "ERR-ACAD-INVALID_TEACHER_ROLE"

    def test_assign_teacher_assignment_exists_raises_409(self):
        """Phân công (teacher, class, subject) đã tồn tại — raise 409 ERR-ACAD-ASSIGNMENT_EXISTS."""
        db = MagicMock()
        class_id = uuid.uuid4()
        teacher_id = uuid.uuid4()
        subject_id = uuid.uuid4()

        with patch("app.modules.academic.services.teacher_assignment_service.ClassRepository") as MockClassRepo, \
             patch("app.modules.academic.services.teacher_assignment_service.SubjectRepository") as MockSubjectRepo, \
             patch("app.modules.academic.services.teacher_assignment_service.TeacherAssignmentRepository") as MockAssignRepo:

            MockClassRepo.get_by_id.return_value = _make_class(class_id)
            MockSubjectRepo.get_by_id.return_value = _make_subject(subject_id)

            user_mock = MagicMock(spec=User)
            db.query.return_value.join.return_value.filter.return_value.first.return_value = user_mock

            MockAssignRepo.get_assignment.return_value = _make_assignment(class_id, teacher_id, subject_id)

            with pytest.raises(HTTPException) as exc_info:
                TeacherAssignmentService.assign_teacher(db, class_id, teacher_id, subject_id)

            assert exc_info.value.status_code == 409
            assert exc_info.value.detail["code"] == "ERR-ACAD-ASSIGNMENT_EXISTS"

    def test_assign_teacher_success(self):
        """Phân công giáo viên hợp lệ — thành công."""
        db = MagicMock()
        class_id = uuid.uuid4()
        teacher_id = uuid.uuid4()
        subject_id = uuid.uuid4()

        with patch("app.modules.academic.services.teacher_assignment_service.ClassRepository") as MockClassRepo, \
             patch("app.modules.academic.services.teacher_assignment_service.SubjectRepository") as MockSubjectRepo, \
             patch("app.modules.academic.services.teacher_assignment_service.TeacherAssignmentRepository") as MockAssignRepo:

            MockClassRepo.get_by_id.return_value = _make_class(class_id)
            MockSubjectRepo.get_by_id.return_value = _make_subject(subject_id)

            user_mock = MagicMock(spec=User)
            db.query.return_value.join.return_value.filter.return_value.first.return_value = user_mock

            MockAssignRepo.get_assignment.return_value = None
            created = _make_assignment(class_id, teacher_id, subject_id)
            MockAssignRepo.create.return_value = created

            res = TeacherAssignmentService.assign_teacher(db, class_id, teacher_id, subject_id)

            assert res.class_id == class_id
            assert res.teacher_id == teacher_id
            assert res.subject_id == subject_id
            MockAssignRepo.create.assert_called_once_with(
                db=db,
                class_id=class_id,
                teacher_id=teacher_id,
                subject_id=subject_id
            )


class TestListAssignmentsInClass:
    def test_list_assignments_class_not_found_raises_404(self):
        """Liệt kê phân công của class_id không tồn tại — raise 404 ERR-ACAD-CLASS_NOT_FOUND."""
        db = MagicMock()
        class_id = uuid.uuid4()

        with patch("app.modules.academic.services.teacher_assignment_service.ClassRepository") as MockClassRepo:
            MockClassRepo.get_by_id.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                TeacherAssignmentService.list_assignments_in_class(db, class_id)

            assert exc_info.value.status_code == 404
            assert exc_info.value.detail["code"] == "ERR-ACAD-CLASS_NOT_FOUND"

    def test_list_assignments_success(self):
        """Liệt kê phân công của lớp thành công."""
        db = MagicMock()
        class_id = uuid.uuid4()

        with patch("app.modules.academic.services.teacher_assignment_service.ClassRepository") as MockClassRepo, \
             patch("app.modules.academic.services.teacher_assignment_service.TeacherAssignmentRepository") as MockAssignRepo:

            MockClassRepo.get_by_id.return_value = _make_class(class_id)
            records = [_make_assignment(class_id=class_id)]
            MockAssignRepo.list_by_class_id.return_value = records

            res = TeacherAssignmentService.list_assignments_in_class(db, class_id)

            assert res == records
            MockAssignRepo.list_by_class_id.assert_called_once_with(db, class_id)


class TestUnassignTeacher:
    def test_unassign_teacher_class_not_found_raises_404(self):
        """Hủy phân công tại lớp không tồn tại — raise 404 ERR-ACAD-CLASS_NOT_FOUND."""
        db = MagicMock()
        class_id = uuid.uuid4()
        teacher_id = uuid.uuid4()
        subject_id = uuid.uuid4()

        with patch("app.modules.academic.services.teacher_assignment_service.ClassRepository") as MockClassRepo:
            MockClassRepo.get_by_id.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                TeacherAssignmentService.unassign_teacher(db, class_id, teacher_id, subject_id)

            assert exc_info.value.status_code == 404
            assert exc_info.value.detail["code"] == "ERR-ACAD-CLASS_NOT_FOUND"

    def test_unassign_teacher_assignment_not_found_raises_404(self):
        """Hủy phân công không tồn tại — raise 404 ERR-ACAD-ASSIGNMENT_NOT_FOUND."""
        db = MagicMock()
        class_id = uuid.uuid4()
        teacher_id = uuid.uuid4()
        subject_id = uuid.uuid4()

        with patch("app.modules.academic.services.teacher_assignment_service.ClassRepository") as MockClassRepo, \
             patch("app.modules.academic.services.teacher_assignment_service.TeacherAssignmentRepository") as MockAssignRepo:

            MockClassRepo.get_by_id.return_value = _make_class(class_id)
            MockAssignRepo.get_assignment.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                TeacherAssignmentService.unassign_teacher(db, class_id, teacher_id, subject_id)

            assert exc_info.value.status_code == 404
            assert exc_info.value.detail["code"] == "ERR-ACAD-ASSIGNMENT_NOT_FOUND"

    def test_unassign_teacher_success(self):
        """Hủy phân công giáo viên thành công."""
        db = MagicMock()
        class_id = uuid.uuid4()
        teacher_id = uuid.uuid4()
        subject_id = uuid.uuid4()

        with patch("app.modules.academic.services.teacher_assignment_service.ClassRepository") as MockClassRepo, \
             patch("app.modules.academic.services.teacher_assignment_service.TeacherAssignmentRepository") as MockAssignRepo:

            MockClassRepo.get_by_id.return_value = _make_class(class_id)
            existing = _make_assignment(class_id, teacher_id, subject_id)
            MockAssignRepo.get_assignment.return_value = existing

            TeacherAssignmentService.unassign_teacher(db, class_id, teacher_id, subject_id)

            MockAssignRepo.delete.assert_called_once_with(db, existing)
