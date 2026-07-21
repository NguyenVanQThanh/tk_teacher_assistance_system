# File Name: test_subject_service.py
# Description: Unit tests for SubjectService — duplicate check logic.
# Created At: 2026-07-21
# Created By: Tam Khang
# Updated At: 2026-07-21
# Updated By: Tam Khang

import uuid
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.modules.academic.services.subject_service import SubjectService
from app.modules.academic.models import Subject


def _make_subject(name: str, subject_id: uuid.UUID = None) -> Subject:
    """Helper to build a Subject ORM mock."""
    s = Subject()
    s.subject_id = subject_id or uuid.uuid4()
    s.subject_name = name
    s.description = None
    return s


# ---------------------------------------------------------------------------
# create_subject
# ---------------------------------------------------------------------------
class TestCreateSubject:
    def test_create_success(self):
        """Tạo môn học với tên mới — thành công."""
        db = MagicMock()
        with patch("app.modules.academic.services.subject_service.SubjectRepository") as MockRepo:
            MockRepo.get_by_name.return_value = None
            created = _make_subject("Toán")
            MockRepo.create.return_value = created

            result = SubjectService.create_subject(db, "Toán", None)

            MockRepo.get_by_name.assert_called_once_with(db, "Toán")
            MockRepo.create.assert_called_once_with(db, "Toán", None)
            assert result.subject_name == "Toán"

    def test_create_duplicate_raises_409(self):
        """Tạo môn học với tên đã tồn tại — raise 409."""
        db = MagicMock()
        with patch("app.modules.academic.services.subject_service.SubjectRepository") as MockRepo:
            MockRepo.get_by_name.return_value = _make_subject("Toán")

            with pytest.raises(HTTPException) as exc_info:
                SubjectService.create_subject(db, "Toán", None)

            assert exc_info.value.status_code == 409
            assert exc_info.value.detail["code"] == "ERR-ACAD-SUBJECT_DUPLICATE_NAME"


# ---------------------------------------------------------------------------
# get_subject
# ---------------------------------------------------------------------------
class TestGetSubject:
    def test_get_success(self):
        """Lấy môn học tồn tại — thành công."""
        db = MagicMock()
        sid = uuid.uuid4()
        with patch("app.modules.academic.services.subject_service.SubjectRepository") as MockRepo:
            MockRepo.get_by_id.return_value = _make_subject("Lý", sid)
            result = SubjectService.get_subject(db, sid)
            assert result.subject_name == "Lý"

    def test_get_not_found_raises_404(self):
        """Lấy môn học không tồn tại — raise 404."""
        db = MagicMock()
        with patch("app.modules.academic.services.subject_service.SubjectRepository") as MockRepo:
            MockRepo.get_by_id.return_value = None
            with pytest.raises(HTTPException) as exc_info:
                SubjectService.get_subject(db, uuid.uuid4())
            assert exc_info.value.status_code == 404
            assert exc_info.value.detail["code"] == "ERR-ACAD-SUBJECT_NOT_FOUND"


# ---------------------------------------------------------------------------
# update_subject
# ---------------------------------------------------------------------------
class TestUpdateSubject:
    def test_update_success(self):
        """Cập nhật môn học với tên mới chưa dùng — thành công."""
        db = MagicMock()
        sid = uuid.uuid4()
        original = _make_subject("Hóa", sid)
        updated = _make_subject("Hóa Nâng Cao", sid)

        with patch("app.modules.academic.services.subject_service.SubjectRepository") as MockRepo:
            MockRepo.get_by_id.return_value = original
            MockRepo.get_by_name.return_value = None
            MockRepo.update.return_value = updated

            result = SubjectService.update_subject(db, sid, "Hóa Nâng Cao", None)
            assert result.subject_name == "Hóa Nâng Cao"

    def test_update_same_name_no_conflict(self):
        """Cập nhật chỉ description, giữ tên cũ — không false-positive 409 (EC-04)."""
        db = MagicMock()
        sid = uuid.uuid4()
        original = _make_subject("Tiếng Anh", sid)

        with patch("app.modules.academic.services.subject_service.SubjectRepository") as MockRepo:
            MockRepo.get_by_id.return_value = original
            # get_by_name trả về chính subject đó (cùng subject_id)
            MockRepo.get_by_name.return_value = original
            MockRepo.update.return_value = original

            # Should NOT raise even though name "exists" — same subject
            result = SubjectService.update_subject(db, sid, "Tiếng Anh", "Mô tả mới")
            assert result is not None

    def test_update_duplicate_name_raises_409(self):
        """Cập nhật tên trùng với môn khác — raise 409."""
        db = MagicMock()
        sid = uuid.uuid4()
        other_id = uuid.uuid4()
        original = _make_subject("Lịch Sử", sid)
        other = _make_subject("Địa Lý", other_id)

        with patch("app.modules.academic.services.subject_service.SubjectRepository") as MockRepo:
            MockRepo.get_by_id.return_value = original
            MockRepo.get_by_name.return_value = other  # conflict — different subject_id

            with pytest.raises(HTTPException) as exc_info:
                SubjectService.update_subject(db, sid, "Địa Lý", None)

            assert exc_info.value.status_code == 409
            assert exc_info.value.detail["code"] == "ERR-ACAD-SUBJECT_DUPLICATE_NAME"

    def test_update_subject_not_found_raises_404(self):
        """Cập nhật môn học không tồn tại — raise 404."""
        db = MagicMock()
        with patch("app.modules.academic.services.subject_service.SubjectRepository") as MockRepo:
            MockRepo.get_by_id.return_value = None
            with pytest.raises(HTTPException) as exc_info:
                SubjectService.update_subject(db, uuid.uuid4(), "Tên Mới", None)
            assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# delete_subject
# ---------------------------------------------------------------------------
class TestDeleteSubject:
    def test_delete_success(self):
        """Xóa môn học tồn tại — thành công."""
        db = MagicMock()
        sid = uuid.uuid4()
        subject = _make_subject("Công Nghệ", sid)

        with patch("app.modules.academic.services.subject_service.SubjectRepository") as MockRepo:
            MockRepo.get_by_id.return_value = subject
            SubjectService.delete_subject(db, sid)
            MockRepo.delete.assert_called_once_with(db, subject)

    def test_delete_not_found_raises_404(self):
        """Xóa môn học không tồn tại — raise 404."""
        db = MagicMock()
        with patch("app.modules.academic.services.subject_service.SubjectRepository") as MockRepo:
            MockRepo.get_by_id.return_value = None
            with pytest.raises(HTTPException) as exc_info:
                SubjectService.delete_subject(db, uuid.uuid4())
            assert exc_info.value.status_code == 404
