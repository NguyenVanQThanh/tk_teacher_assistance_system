# File Name: test_teacher_assignments.py
# Description: Integration tests for Teacher Assignment endpoints (F-ACAD-04).
# Created At: 2026-07-23
# Created By: Tam Khang
# Updated At: 2026-07-23
# Updated By: Tam Khang

import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.models import User
from app.core.database import get_db


def get_admin_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"phone": "0987654321", "password": "password123"}
    )
    return response.json()["access_token"]


def get_teacher_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"phone": "0912345678", "password": "password123"}
    )
    return response.json()["access_token"]


def get_student_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"phone": "0934567890", "password": "password123"}
    )
    return response.json()["access_token"]


def get_user_id_by_phone(client: TestClient, phone: str) -> str:
    """Helper to fetch user_id from DB by phone number."""
    db_gen = client.app.dependency_overrides[get_db]()
    db: Session = next(db_gen)
    user = db.query(User).filter(User.phone == phone).first()
    return str(user.user_id)


def create_test_class(client: TestClient, class_name: str = None) -> str:
    token = get_admin_token(client)
    name = class_name or f"Class_{uuid.uuid4().hex[:6]}"
    resp = client.post(
        "/api/v1/classes",
        json={"class_name": name, "school_year": "2026-2027"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_201_CREATED
    return resp.json()["class_id"]


def create_test_subject(client: TestClient, subject_name: str = None) -> str:
    token = get_admin_token(client)
    name = subject_name or f"Subject_{uuid.uuid4().hex[:6]}"
    resp = client.post(
        "/api/v1/subjects",
        json={"subject_name": name, "description": "Subject for test"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_201_CREATED
    return resp.json()["subject_id"]


# ---------------------------------------------------------------------------
# POST /api/v1/classes/{class_id}/teacher-subjects (Phân công GV)
# ---------------------------------------------------------------------------
def test_assign_teacher_success(client: TestClient):
    """AC-01: Admin phân công giáo viên hợp lệ dạy môn tại lớp -> 201 Created."""
    token = get_admin_token(client)
    class_id = create_test_class(client)
    subject_id = create_test_subject(client)
    teacher_id = get_user_id_by_phone(client, "0912345678")

    resp = client.post(
        f"/api/v1/classes/{class_id}/teacher-subjects",
        json={"teacher_id": teacher_id, "subject_id": subject_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["class_id"] == class_id
    assert data["teacher_id"] == teacher_id
    assert data["subject_id"] == subject_id


def test_assign_teacher_duplicate_raises_409(client: TestClient):
    """AC-02 & EC-05: Phân công trùng (teacher, class, subject) -> 409 ERR-ACAD-ASSIGNMENT_EXISTS."""
    token = get_admin_token(client)
    class_id = create_test_class(client)
    subject_id = create_test_subject(client)
    teacher_id = get_user_id_by_phone(client, "0912345678")

    # Assign first time
    client.post(
        f"/api/v1/classes/{class_id}/teacher-subjects",
        json={"teacher_id": teacher_id, "subject_id": subject_id},
        headers={"Authorization": f"Bearer {token}"}
    )

    # Assign second time
    resp = client.post(
        f"/api/v1/classes/{class_id}/teacher-subjects",
        json={"teacher_id": teacher_id, "subject_id": subject_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_409_CONFLICT
    assert resp.json()["detail"]["code"] == "ERR-ACAD-ASSIGNMENT_EXISTS"


def test_assign_student_role_raises_400(client: TestClient):
    """AC-03 & EC-03: teacher_id là role Student -> 400 ERR-ACAD-INVALID_TEACHER_ROLE."""
    token = get_admin_token(client)
    class_id = create_test_class(client)
    subject_id = create_test_subject(client)
    student_id = get_user_id_by_phone(client, "0934567890")

    resp = client.post(
        f"/api/v1/classes/{class_id}/teacher-subjects",
        json={"teacher_id": student_id, "subject_id": subject_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.json()["detail"]["code"] == "ERR-ACAD-INVALID_TEACHER_ROLE"


def test_assign_inactive_teacher_raises_400(client: TestClient):
    """AC-03 & EC-04: teacher_id có status Inactive -> 400 ERR-ACAD-INVALID_TEACHER_ROLE."""
    token = get_admin_token(client)
    class_id = create_test_class(client)
    subject_id = create_test_subject(client)
    inactive_id = get_user_id_by_phone(client, "0987654323")

    resp = client.post(
        f"/api/v1/classes/{class_id}/teacher-subjects",
        json={"teacher_id": inactive_id, "subject_id": subject_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.json()["detail"]["code"] == "ERR-ACAD-INVALID_TEACHER_ROLE"


def test_assign_non_existent_class_raises_404(client: TestClient):
    """AC-04 & EC-01: class_id không tồn tại -> 404 ERR-ACAD-CLASS_NOT_FOUND."""
    token = get_admin_token(client)
    fake_class_id = str(uuid.uuid4())
    subject_id = create_test_subject(client)
    teacher_id = get_user_id_by_phone(client, "0912345678")

    resp = client.post(
        f"/api/v1/classes/{fake_class_id}/teacher-subjects",
        json={"teacher_id": teacher_id, "subject_id": subject_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json()["detail"]["code"] == "ERR-ACAD-CLASS_NOT_FOUND"


def test_assign_non_existent_subject_raises_404(client: TestClient):
    """AC-05 & EC-02: subject_id không tồn tại -> 404 ERR-ACAD-SUBJECT_NOT_FOUND."""
    token = get_admin_token(client)
    class_id = create_test_class(client)
    fake_subject_id = str(uuid.uuid4())
    teacher_id = get_user_id_by_phone(client, "0912345678")

    resp = client.post(
        f"/api/v1/classes/{class_id}/teacher-subjects",
        json={"teacher_id": teacher_id, "subject_id": fake_subject_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json()["detail"]["code"] == "ERR-ACAD-SUBJECT_NOT_FOUND"


def test_assign_same_teacher_two_subjects_success(client: TestClient):
    """EC-06: Một GV được phân công dạy 2 môn khác nhau ở cùng 1 lớp -> 201 Created cho cả 2."""
    token = get_admin_token(client)
    class_id = create_test_class(client)
    subject1_id = create_test_subject(client)
    subject2_id = create_test_subject(client)
    teacher_id = get_user_id_by_phone(client, "0912345678")

    resp1 = client.post(
        f"/api/v1/classes/{class_id}/teacher-subjects",
        json={"teacher_id": teacher_id, "subject_id": subject1_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp1.status_code == status.HTTP_201_CREATED

    resp2 = client.post(
        f"/api/v1/classes/{class_id}/teacher-subjects",
        json={"teacher_id": teacher_id, "subject_id": subject2_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp2.status_code == status.HTTP_201_CREATED


def test_assign_forbidden_for_teacher_raises_403(client: TestClient):
    """AC-09 & EC-08: Teacher gọi POST /classes/{id}/teacher-subjects -> 403 ERR-AUTH-FORBIDDEN."""
    token = get_teacher_token(client)
    admin_token = get_admin_token(client)
    class_id = create_test_class(client)
    subject_id = create_test_subject(client)
    teacher_id = get_user_id_by_phone(client, "0912345678")

    resp = client.post(
        f"/api/v1/classes/{class_id}/teacher-subjects",
        json={"teacher_id": teacher_id, "subject_id": subject_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# GET /api/v1/classes/{class_id}/teacher-subjects (Liệt kê phân công)
# ---------------------------------------------------------------------------
def test_list_assignments_in_class_success(client: TestClient):
    """AC-06: GET /classes/{class_id}/teacher-subjects trả về danh sách phân công -> 200 OK."""
    token = get_admin_token(client)
    class_id = create_test_class(client)
    subject_id = create_test_subject(client)
    teacher_id = get_user_id_by_phone(client, "0912345678")

    client.post(
        f"/api/v1/classes/{class_id}/teacher-subjects",
        json={"teacher_id": teacher_id, "subject_id": subject_id},
        headers={"Authorization": f"Bearer {token}"}
    )

    resp = client.get(
        f"/api/v1/classes/{class_id}/teacher-subjects",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["teacher_id"] == teacher_id
    assert data[0]["subject_id"] == subject_id


def test_list_assignments_non_existent_class_raises_404(client: TestClient):
    """GET /classes/{fake_id}/teacher-subjects với class_id không tồn tại -> 404 ERR-ACAD-CLASS_NOT_FOUND."""
    token = get_admin_token(client)
    fake_class_id = str(uuid.uuid4())

    resp = client.get(
        f"/api/v1/classes/{fake_class_id}/teacher-subjects",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json()["detail"]["code"] == "ERR-ACAD-CLASS_NOT_FOUND"


# ---------------------------------------------------------------------------
# DELETE /api/v1/classes/{class_id}/teacher-subjects/{teacher_id}/{subject_id} (Hủy phân công)
# ---------------------------------------------------------------------------
def test_unassign_teacher_success(client: TestClient):
    """AC-07: Admin hủy phân công giáo viên -> 204 No Content."""
    token = get_admin_token(client)
    class_id = create_test_class(client)
    subject_id = create_test_subject(client)
    teacher_id = get_user_id_by_phone(client, "0912345678")

    # Assign
    client.post(
        f"/api/v1/classes/{class_id}/teacher-subjects",
        json={"teacher_id": teacher_id, "subject_id": subject_id},
        headers={"Authorization": f"Bearer {token}"}
    )

    # Unassign
    resp = client.delete(
        f"/api/v1/classes/{class_id}/teacher-subjects/{teacher_id}/{subject_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_204_NO_CONTENT

    # Verify list is empty
    list_resp = client.get(
        f"/api/v1/classes/{class_id}/teacher-subjects",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert len(list_resp.json()) == 0


def test_unassign_teacher_assignment_not_found_raises_404(client: TestClient):
    """AC-08 & EC-07: Hủy phân công không tồn tại -> 404 ERR-ACAD-ASSIGNMENT_NOT_FOUND."""
    token = get_admin_token(client)
    class_id = create_test_class(client)
    subject_id = create_test_subject(client)
    teacher_id = get_user_id_by_phone(client, "0912345678")

    resp = client.delete(
        f"/api/v1/classes/{class_id}/teacher-subjects/{teacher_id}/{subject_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json()["detail"]["code"] == "ERR-ACAD-ASSIGNMENT_NOT_FOUND"
