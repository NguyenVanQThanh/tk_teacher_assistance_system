# File Name: test_classes.py
# Description: Integration tests for Class CRUD endpoints (F-ACAD-02).
# Created At: 2026-07-22
# Created By: Tam Khang
# Updated At: 2026-07-22
# Updated By: Tam Khang

import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.models import User, Role
from app.core.database import get_db


# ---------------------------------------------------------------------------
# Helpers for Auth Tokens
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# AC-01 / EC-03: POST /api/v1/classes — tạo lớp thành công
# ---------------------------------------------------------------------------
def test_create_class_success(client: TestClient):
    """AC-01 & EC-03: Admin tạo lớp học mới, tên chưa tồn tại → 201."""
    token = get_admin_token(client)
    teacher_id = get_user_id_by_phone(client, "0912345678")

    # Create class with homeroom teacher
    response = client.post(
        "/api/v1/classes",
        json={
            "class_name": "10A1",
            "school_year": "2026-2027",
            "homeroom_teacher_id": teacher_id
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["class_name"] == "10A1"
    assert data["school_year"] == "2026-2027"
    assert data["homeroom_teacher_id"] == teacher_id
    assert "class_id" in data

    # Create class without homeroom teacher (EC-03)
    response_no_teacher = client.post(
        "/api/v1/classes",
        json={"class_name": "10A2", "school_year": "2026-2027"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response_no_teacher.status_code == status.HTTP_201_CREATED
    assert response_no_teacher.json()["homeroom_teacher_id"] is None


# ---------------------------------------------------------------------------
# AC-02 / EC-04: POST — tên trùng → 409
# ---------------------------------------------------------------------------
def test_create_class_duplicate_name(client: TestClient):
    """AC-02 / EC-04: Tạo lớp học với tên đã tồn tại → 409 ERR-ACAD-CLASS_DUPLICATE_NAME."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/api/v1/classes", json={"class_name": "11B1"}, headers=headers)

    response = client.post("/api/v1/classes", json={"class_name": "11B1"}, headers=headers)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"]["code"] == "ERR-ACAD-CLASS_DUPLICATE_NAME"


# ---------------------------------------------------------------------------
# AC-03 / EC-01: POST — homeroom_teacher_id thuộc role Student → 400
# ---------------------------------------------------------------------------
def test_create_class_invalid_homeroom_student(client: TestClient):
    """EC-01 / AC-03: gán homeroom_teacher_id trỏ tới user role Student → 400."""
    token = get_admin_token(client)
    student_id = get_user_id_by_phone(client, "0934567890")

    response = client.post(
        "/api/v1/classes",
        json={
            "class_name": "10A3",
            "school_year": "2026-2027",
            "homeroom_teacher_id": student_id
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "ERR-ACAD-INVALID_HOMEROOM_TEACHER"


# ---------------------------------------------------------------------------
# AC-03 / EC-02: POST — homeroom_teacher_id thuộc Teacher nhưng status Inactive → 400
# ---------------------------------------------------------------------------
def test_create_class_invalid_homeroom_inactive(client: TestClient):
    """EC-02 / AC-03: gán homeroom_teacher_id trỏ tới Teacher Inactive → 400."""
    token = get_admin_token(client)

    # Create inactive teacher directly in DB
    db_gen = client.app.dependency_overrides[get_db]()
    db: Session = next(db_gen)
    teacher_role = db.query(Role).filter(Role.name == "Teacher").first()

    inactive_teacher = User(
        user_id=uuid.uuid4(),
        phone="0999888777",
        email="inactive_teacher@test.com",
        password_hash="dummy",
        full_name="Inactive Teacher",
        role_id=teacher_role.role_id,
        status="Inactive"
    )
    db.add(inactive_teacher)
    db.commit()

    response = client.post(
        "/api/v1/classes",
        json={
            "class_name": "10A4",
            "school_year": "2026-2027",
            "homeroom_teacher_id": str(inactive_teacher.user_id)
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "ERR-ACAD-INVALID_HOMEROOM_TEACHER"


# ---------------------------------------------------------------------------
# AC-04: GET /api/v1/classes — danh sách
# ---------------------------------------------------------------------------
def test_list_classes(client: TestClient):
    """AC-04: Xem danh sách N lớp → 200."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/api/v1/classes", json={"class_name": "12C1"}, headers=headers)

    response = client.get("/api/v1/classes", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


# ---------------------------------------------------------------------------
# AC-05 / EC-05: GET /api/v1/classes/{id} — không tồn tại → 404
# ---------------------------------------------------------------------------
def test_get_class_not_found(client: TestClient):
    """EC-05 / AC-05: Xem lớp học với class_id không tồn tại → 404."""
    token = get_admin_token(client)
    fake_id = str(uuid.uuid4())

    response = client.get(
        f"/api/v1/classes/{fake_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"]["code"] == "ERR-ACAD-CLASS_NOT_FOUND"


# ---------------------------------------------------------------------------
# AC-06: PUT /api/v1/classes/{id} — sửa lớp học thành công
# ---------------------------------------------------------------------------
def test_update_class_success(client: TestClient):
    """AC-06: Sửa lớp học, đổi tên và GVCN sang Teacher Active khác → 200."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    teacher_id = get_user_id_by_phone(client, "0912345678")

    # Create class
    create_resp = client.post("/api/v1/classes", json={"class_name": "12C2"}, headers=headers)
    class_id = create_resp.json()["class_id"]

    # Update class
    response = client.put(
        f"/api/v1/classes/{class_id}",
        json={
            "class_name": "12C2_Renamed",
            "school_year": "2027-2028",
            "homeroom_teacher_id": teacher_id
        },
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["class_name"] == "12C2_Renamed"
    assert data["school_year"] == "2027-2028"
    assert data["homeroom_teacher_id"] == teacher_id


# ---------------------------------------------------------------------------
# AC-07: DELETE /api/v1/classes/{id} — xóa lớp học
# ---------------------------------------------------------------------------
def test_delete_class_success(client: TestClient):
    """AC-07: Xóa lớp học tồn tại → 204."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post("/api/v1/classes", json={"class_name": "10A5"}, headers=headers)
    class_id = create_resp.json()["class_id"]

    delete_resp = client.delete(f"/api/v1/classes/{class_id}", headers=headers)
    assert delete_resp.status_code == status.HTTP_204_NO_CONTENT

    # Confirm deleted
    get_resp = client.get(f"/api/v1/classes/{class_id}", headers=headers)
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# AC-08 / EC-06: User không có permission → 403
# ---------------------------------------------------------------------------
def test_class_endpoints_forbidden_for_teacher(client: TestClient):
    """EC-06 / AC-08: User role Teacher gọi POST/PUT/DELETE → 403 ERR-AUTH-FORBIDDEN."""
    token = get_teacher_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # POST
    response = client.post("/api/v1/classes", json={"class_name": "ForbiddenClass"}, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"]["code"] == "ERR-AUTH-FORBIDDEN"

    # GET list (Teacher does not have ACAD_CLASS_VIEW permission by default in seed)
    response_get = client.get("/api/v1/classes", headers=headers)
    assert response_get.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# Unauthorized — không token → 401
# ---------------------------------------------------------------------------
def test_class_endpoints_unauthorized(client: TestClient):
    """Không có JWT token → 401."""
    response = client.get("/api/v1/classes")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
