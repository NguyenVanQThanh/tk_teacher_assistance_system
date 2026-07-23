# File Name: test_enrollments.py
# Description: Integration tests for Enrollment endpoints (F-ACAD-03).
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
    """Helper to create a class and return its class_id."""
    token = get_admin_token(client)
    name = class_name or f"Class_{uuid.uuid4().hex[:6]}"
    resp = client.post(
        "/api/v1/classes",
        json={"class_name": name, "school_year": "2026-2027"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_201_CREATED
    return resp.json()["class_id"]


# ---------------------------------------------------------------------------
# POST /api/v1/classes/{class_id}/students (Ghi danh)
# ---------------------------------------------------------------------------
def test_enroll_student_success(client: TestClient):
    """AC-01: Admin ghi danh học sinh hợp lệ vào lớp -> 201 Created."""
    token = get_admin_token(client)
    class_id = create_test_class(client)
    student_id = get_user_id_by_phone(client, "0934567890")

    resp = client.post(
        f"/api/v1/classes/{class_id}/students",
        json={"student_id": student_id, "student_code": "HS_TEST_01"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["class_id"] == class_id
    assert data["student_id"] == student_id
    assert data["student_code"] == "HS_TEST_01"


def test_enroll_duplicate_raises_409(client: TestClient):
    """AC-02 & EC-05: Ghi danh học sinh đã có trong lớp -> 409 ERR-ACAD-ALREADY_ENROLLED."""
    token = get_admin_token(client)
    class_id = create_test_class(client)
    student_id = get_user_id_by_phone(client, "0934567890")

    # Enroll first time
    client.post(
        f"/api/v1/classes/{class_id}/students",
        json={"student_id": student_id, "student_code": "HS_DUP_01"},
        headers={"Authorization": f"Bearer {token}"}
    )

    # Enroll second time
    resp = client.post(
        f"/api/v1/classes/{class_id}/students",
        json={"student_id": student_id, "student_code": "HS_DUP_02"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_409_CONFLICT
    assert resp.json()["detail"]["code"] == "ERR-ACAD-ALREADY_ENROLLED"


def test_enroll_teacher_role_raises_400(client: TestClient):
    """AC-03 & EC-03: student_id là role Teacher -> 400 ERR-ACAD-INVALID_STUDENT_ROLE."""
    token = get_admin_token(client)
    class_id = create_test_class(client)
    teacher_id = get_user_id_by_phone(client, "0912345678")

    resp = client.post(
        f"/api/v1/classes/{class_id}/students",
        json={"student_id": teacher_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.json()["detail"]["code"] == "ERR-ACAD-INVALID_STUDENT_ROLE"


def test_enroll_inactive_student_raises_400(client: TestClient):
    """AC-03 & EC-04: student_id có status Inactive -> 400 ERR-ACAD-INVALID_STUDENT_ROLE."""
    token = get_admin_token(client)
    class_id = create_test_class(client)
    inactive_id = get_user_id_by_phone(client, "0987654323")

    resp = client.post(
        f"/api/v1/classes/{class_id}/students",
        json={"student_id": inactive_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.json()["detail"]["code"] == "ERR-ACAD-INVALID_STUDENT_ROLE"


def test_enroll_non_existent_student_raises_404(client: TestClient):
    """AC-04 & EC-02: student_id không tồn tại -> 404 ERR-ACAD-STUDENT_NOT_FOUND."""
    token = get_admin_token(client)
    class_id = create_test_class(client)
    fake_student_id = str(uuid.uuid4())

    resp = client.post(
        f"/api/v1/classes/{class_id}/students",
        json={"student_id": fake_student_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json()["detail"]["code"] == "ERR-ACAD-STUDENT_NOT_FOUND"


def test_enroll_non_existent_class_raises_404(client: TestClient):
    """AC-10 & EC-01: class_id không tồn tại -> 404 ERR-ACAD-CLASS_NOT_FOUND."""
    token = get_admin_token(client)
    fake_class_id = str(uuid.uuid4())
    student_id = get_user_id_by_phone(client, "0934567890")

    resp = client.post(
        f"/api/v1/classes/{fake_class_id}/students",
        json={"student_id": student_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json()["detail"]["code"] == "ERR-ACAD-CLASS_NOT_FOUND"


def test_enroll_duplicate_student_code_raises_409(client: TestClient):
    """AC-05 & EC-06: student_code đã được dùng bởi HS khác -> 409 ERR-ACAD-DUPLICATE_STUDENT_CODE."""
    token = get_admin_token(client)
    class_id1 = create_test_class(client)
    class_id2 = create_test_class(client)

    student_id = get_user_id_by_phone(client, "0934567890")
    student_allow_id = get_user_id_by_phone(client, "0934567891")

    # Enroll student 1 with student_code HS_CODE_UNIQUE
    client.post(
        f"/api/v1/classes/{class_id1}/students",
        json={"student_id": student_id, "student_code": "HS_CODE_UNIQUE"},
        headers={"Authorization": f"Bearer {token}"}
    )

    # Enroll student 2 with the same student_code
    resp = client.post(
        f"/api/v1/classes/{class_id2}/students",
        json={"student_id": student_allow_id, "student_code": "HS_CODE_UNIQUE"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_409_CONFLICT
    assert resp.json()["detail"]["code"] == "ERR-ACAD-DUPLICATE_STUDENT_CODE"


def test_enroll_forbidden_for_teacher_raises_403(client: TestClient):
    """AC-09 & EC-08: Teacher gọi POST /classes/{id}/students -> 403 ERR-AUTH-FORBIDDEN."""
    token = get_teacher_token(client)
    class_id = create_test_class(client)
    student_id = get_user_id_by_phone(client, "0934567890")

    resp = client.post(
        f"/api/v1/classes/{class_id}/students",
        json={"student_id": student_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# GET /api/v1/classes/{class_id}/students (Liệt kê HS trong lớp)
# ---------------------------------------------------------------------------
def test_list_students_in_class_success(client: TestClient):
    """AC-06: GET /classes/{class_id}/students trả về danh sách học sinh -> 200 OK."""
    token = get_admin_token(client)
    class_id = create_test_class(client)
    student_id = get_user_id_by_phone(client, "0934567890")

    client.post(
        f"/api/v1/classes/{class_id}/students",
        json={"student_id": student_id, "student_code": "HS_LIST_01"},
        headers={"Authorization": f"Bearer {token}"}
    )

    resp = client.get(
        f"/api/v1/classes/{class_id}/students",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["student_id"] == student_id


def test_list_students_non_existent_class_raises_404(client: TestClient):
    """GET /classes/{fake_id}/students với class_id không tồn tại -> 404 ERR-ACAD-CLASS_NOT_FOUND."""
    token = get_admin_token(client)
    fake_class_id = str(uuid.uuid4())

    resp = client.get(
        f"/api/v1/classes/{fake_class_id}/students",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json()["detail"]["code"] == "ERR-ACAD-CLASS_NOT_FOUND"


# ---------------------------------------------------------------------------
# DELETE /api/v1/classes/{class_id}/students/{student_id} (Hủy ghi danh)
# ---------------------------------------------------------------------------
def test_unenroll_student_success(client: TestClient):
    """AC-07: Admin hủy ghi danh học sinh -> 204 No Content."""
    token = get_admin_token(client)
    class_id = create_test_class(client)
    student_id = get_user_id_by_phone(client, "0934567890")

    # Enroll
    client.post(
        f"/api/v1/classes/{class_id}/students",
        json={"student_id": student_id},
        headers={"Authorization": f"Bearer {token}"}
    )

    # Unenroll
    resp = client.delete(
        f"/api/v1/classes/{class_id}/students/{student_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_204_NO_CONTENT

    # Verify list is now empty
    list_resp = client.get(
        f"/api/v1/classes/{class_id}/students",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert len(list_resp.json()) == 0


def test_unenroll_student_not_found_raises_404(client: TestClient):
    """AC-08 & EC-07: Hủy ghi danh học sinh chưa từng ghi danh lớp này -> 404 ERR-ACAD-ENROLLMENT_NOT_FOUND."""
    token = get_admin_token(client)
    class_id = create_test_class(client)
    student_id = get_user_id_by_phone(client, "0934567890")

    resp = client.delete(
        f"/api/v1/classes/{class_id}/students/{student_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json()["detail"]["code"] == "ERR-ACAD-ENROLLMENT_NOT_FOUND"


def test_unenroll_non_existent_class_raises_404(client: TestClient):
    """Hủy ghi danh từ class_id không tồn tại -> 404 ERR-ACAD-CLASS_NOT_FOUND."""
    token = get_admin_token(client)
    fake_class_id = str(uuid.uuid4())
    student_id = get_user_id_by_phone(client, "0934567890")

    resp = client.delete(
        f"/api/v1/classes/{fake_class_id}/students/{student_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json()["detail"]["code"] == "ERR-ACAD-CLASS_NOT_FOUND"
