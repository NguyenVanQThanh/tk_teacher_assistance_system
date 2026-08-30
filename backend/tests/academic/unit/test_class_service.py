# File Name: test_class_service.py
# Description: Unit tests for ClassService — validation, duplicate check, and CRUD logic.
# Created At: 2026-07-22
# Created By: Tam Khang
# Updated At: 2026-07-22
# Updated By: Tam Khang

import uuid
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.modules.academic.services.class_service import ClassService
from app.modules.academic.models import Class


def _make_class(
    name: str,
    class_id: uuid.UUID = None,
    academic_year: str = "2026-2027",
    homeroom_teacher_id: uuid.UUID = None
) -> Class:
    """Helper to build a Class ORM mock."""
    cls = Class()
    cls.class_id = class_id or uuid.uuid4()
    cls.class_name = name
    cls.academic_year = academic_year
    cls.homeroom_teacher_id = homeroom_teacher_id
    return cls


# ---------------------------------------------------------------------------
# create_class
# ---------------------------------------------------------------------------
class TestCreateClass:
    def test_create_success_without_teacher(self):
        """Tạo lớp học không gán GVCN — thành công."""
        db = MagicMock()
        with patch("app.modules.academic.services.class_service.ClassRepository") as MockRepo:
            MockRepo.get_by_name.return_value = None
            created = _make_class("10A1")
            MockRepo.create.return_value = created

            result = ClassService.create_class(db, "10A1", "2026-2027", None)

            MockRepo.get_by_name.assert_called_once_with(db, "10A1")
            MockRepo.create.assert_called_once_with(
                db=db,
                class_name="10A1",
                academic_year="2026-2027",
                homeroom_teacher_id=None
            )
            assert result.class_name == "10A1"

    def test_create_invalid_homeroom_teacher_raises_400(self):
        """Tạo lớp với homeroom_teacher_id không hợp lệ — raise 400."""
        db = MagicMock()
        teacher_id = uuid.uuid4()

        # Mock db query returning None for invalid teacher
        query_mock = db.query.return_value
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            ClassService.create_class(db, "10A2", "2026-2027", teacher_id)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["code"] == "ERR-ACAD-INVALID_HOMEROOM_TEACHER"

    def test_create_duplicate_raises_409(self):
        """Tạo lớp học với tên đã tồn tại — raise 409."""
        db = MagicMock()
        with patch("app.modules.academic.services.class_service.ClassRepository") as MockRepo:
            MockRepo.get_by_name.return_value = _make_class("10A1")

            with pytest.raises(HTTPException) as exc_info:
                ClassService.create_class(db, "10A1", "2026-2027", None)

            assert exc_info.value.status_code == 409
            assert exc_info.value.detail["code"] == "ERR-ACAD-CLASS_DUPLICATE_NAME"


# ---------------------------------------------------------------------------
# get_class & list_classes
# ---------------------------------------------------------------------------
class TestGetAndListClass:
    def test_get_success(self):
        """Lấy thông tin lớp học tồn tại — thành công."""
        db = MagicMock()
        cid = uuid.uuid4()
        with patch("app.modules.academic.services.class_service.ClassRepository") as MockRepo:
            MockRepo.get_by_id.return_value = _make_class("11B1", cid)
            result = ClassService.get_class(db, cid)
            assert result.class_name == "11B1"

    def test_get_not_found_raises_404(self):
        """Lấy thông tin lớp học không tồn tại — raise 404."""
        db = MagicMock()
        with patch("app.modules.academic.services.class_service.ClassRepository") as MockRepo:
            MockRepo.get_by_id.return_value = None
            with pytest.raises(HTTPException) as exc_info:
                ClassService.get_class(db, uuid.uuid4())
            assert exc_info.value.status_code == 404
            assert exc_info.value.detail["code"] == "ERR-ACAD-CLASS_NOT_FOUND"

    def test_list_classes(self):
        """Lấy danh sách tất cả lớp học."""
        db = MagicMock()
        with patch("app.modules.academic.services.class_service.ClassRepository") as MockRepo:
            MockRepo.list_all.return_value = [_make_class("10A1"), _make_class("10A2")]
            result = ClassService.list_classes(db)
            assert len(result) == 2


# ---------------------------------------------------------------------------
# update_class
# ---------------------------------------------------------------------------
class TestUpdateClass:
    def test_update_success(self):
        """Cập nhật tên lớp học mới — thành công."""
        db = MagicMock()
        cid = uuid.uuid4()
        original = _make_class("12C1", cid)
        updated = _make_class("12C1_Updated", cid)

        with patch("app.modules.academic.services.class_service.ClassRepository") as MockRepo:
            MockRepo.get_by_id.return_value = original
            MockRepo.get_by_name.return_value = None
            MockRepo.update.return_value = updated

            result = ClassService.update_class(db, cid, class_name="12C1_Updated")
            assert result.class_name == "12C1_Updated"

    def test_update_same_name_no_conflict(self):
        """Cập nhật không đổi tên — không bị trùng với chính nó."""
        db = MagicMock()
        cid = uuid.uuid4()
        original = _make_class("12C2", cid)

        with patch("app.modules.academic.services.class_service.ClassRepository") as MockRepo:
            MockRepo.get_by_id.return_value = original
            MockRepo.get_by_name.return_value = original
            MockRepo.update.return_value = original

            result = ClassService.update_class(db, cid, class_name="12C2", school_year="2027-2028")
            assert result is not None

    def test_update_duplicate_name_raises_409(self):
        """Cập nhật trùng tên với lớp khác — raise 409."""
        db = MagicMock()
        cid = uuid.uuid4()
        other_id = uuid.uuid4()
        original = _make_class("10A1", cid)
        other = _make_class("10A2", other_id)

        with patch("app.modules.academic.services.class_service.ClassRepository") as MockRepo:
            MockRepo.get_by_id.return_value = original
            MockRepo.get_by_name.return_value = other

            with pytest.raises(HTTPException) as exc_info:
                ClassService.update_class(db, cid, class_name="10A2")

            assert exc_info.value.status_code == 409
            assert exc_info.value.detail["code"] == "ERR-ACAD-CLASS_DUPLICATE_NAME"


# ---------------------------------------------------------------------------
# delete_class
# ---------------------------------------------------------------------------
class TestDeleteClass:
    def test_delete_success(self):
        """Xóa lớp học tồn tại — thành công."""
        db = MagicMock()
        cid = uuid.uuid4()
        cls = _make_class("10A3", cid)

        with patch("app.modules.academic.services.class_service.ClassRepository") as MockRepo:
            MockRepo.get_by_id.return_value = cls
            ClassService.delete_class(db, cid)
            MockRepo.delete.assert_called_once_with(db, cls)

    def test_delete_not_found_raises_404(self):
        """Xóa lớp học không tồn tại — raise 404."""
        db = MagicMock()
        with patch("app.modules.academic.services.class_service.ClassRepository") as MockRepo:
            MockRepo.get_by_id.return_value = None
            with pytest.raises(HTTPException) as exc_info:
                ClassService.delete_class(db, uuid.uuid4())
            assert exc_info.value.status_code == 404
