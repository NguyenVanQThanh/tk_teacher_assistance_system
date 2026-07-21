# File Name: test_subjects.py
# Description: Integration tests for Subject CRUD endpoints (F-ACAD-01).
# Created At: 2026-07-21
# Created By: Tam Khang
# Updated At: 2026-07-21
# Updated By: Tam Khang

import pytest
from fastapi import status
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helper: get admin token (phone seed trong conftest.py)
# ---------------------------------------------------------------------------
def get_admin_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"phone": "0987654321", "password": "password123"}
    )
    return response.json()["access_token"]


def get_student_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"phone": "0934567890", "password": "password123"}
    )
    return response.json()["access_token"]


# ---------------------------------------------------------------------------
# AC-01: POST /api/v1/subjects — tạo thành công
# ---------------------------------------------------------------------------
def test_create_subject_success(client: TestClient):
    """AC-01: Admin tạo môn học mới, tên chưa tồn tại → 201."""
    token = get_admin_token(client)
    response = client.post(
        "/api/v1/subjects",
        json={"subject_name": "Toán học", "description": "Môn toán"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["subject_name"] == "Toán học"
    assert data["description"] == "Môn toán"
    assert "subject_id" in data
    assert "created_at" in data


# ---------------------------------------------------------------------------
# EC-01 / AC-02: POST — tên trùng → 409
# ---------------------------------------------------------------------------
def test_create_subject_duplicate_name(client: TestClient):
    """EC-01: Tạo môn học với tên đã tồn tại → 409 ERR-ACAD-SUBJECT_DUPLICATE_NAME."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    # First create
    client.post("/api/v1/subjects", json={"subject_name": "Vật Lý"}, headers=headers)
    # Second create with same name
    response = client.post("/api/v1/subjects", json={"subject_name": "Vật Lý"}, headers=headers)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"]["code"] == "ERR-ACAD-SUBJECT_DUPLICATE_NAME"


# ---------------------------------------------------------------------------
# AC-03: GET /api/v1/subjects — danh sách
# ---------------------------------------------------------------------------
def test_list_subjects(client: TestClient):
    """AC-03: Admin xem danh sách môn học → 200."""
    token = get_admin_token(client)
    # Create one subject first
    client.post(
        "/api/v1/subjects",
        json={"subject_name": "Hóa học"},
        headers={"Authorization": f"Bearer {token}"}
    )
    response = client.get(
        "/api/v1/subjects",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


# ---------------------------------------------------------------------------
# AC-04: GET /api/v1/subjects/{id} — không tồn tại → 404
# ---------------------------------------------------------------------------
def test_get_subject_not_found(client: TestClient):
    """EC-02 / AC-04: Xem môn học với ID không tồn tại → 404 ERR-ACAD-SUBJECT_NOT_FOUND."""
    token = get_admin_token(client)
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(
        f"/api/v1/subjects/{fake_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"]["code"] == "ERR-ACAD-SUBJECT_NOT_FOUND"


# ---------------------------------------------------------------------------
# AC-05: PUT — cập nhật thành công
# ---------------------------------------------------------------------------
def test_update_subject_success(client: TestClient):
    """AC-05: Admin sửa môn học, tên mới chưa trùng → 200."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    # Create
    create_resp = client.post("/api/v1/subjects", json={"subject_name": "Sinh học"}, headers=headers)
    subject_id = create_resp.json()["subject_id"]
    # Update
    response = client.put(
        f"/api/v1/subjects/{subject_id}",
        json={"subject_name": "Sinh học Nâng cao", "description": "Chương trình nâng cao"},
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["subject_name"] == "Sinh học Nâng cao"


# ---------------------------------------------------------------------------
# AC-06 / EC-01: PUT — tên trùng với môn khác → 409
# ---------------------------------------------------------------------------
def test_update_subject_duplicate_name(client: TestClient):
    """AC-06: Sửa môn học, tên mới trùng với môn khác → 409."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    # Create two subjects
    client.post("/api/v1/subjects", json={"subject_name": "Địa Lý"}, headers=headers)
    create_resp = client.post("/api/v1/subjects", json={"subject_name": "Lịch Sử"}, headers=headers)
    subject_id = create_resp.json()["subject_id"]
    # Try rename to existing name
    response = client.put(
        f"/api/v1/subjects/{subject_id}",
        json={"subject_name": "Địa Lý"},
        headers=headers
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"]["code"] == "ERR-ACAD-SUBJECT_DUPLICATE_NAME"


# ---------------------------------------------------------------------------
# EC-04: PUT — chỉ đổi description, giữ nguyên tên → không false-positive 409
# ---------------------------------------------------------------------------
def test_update_subject_same_name_no_conflict(client: TestClient):
    """EC-04: Sửa chỉ description, giữ nguyên subject_name → 200 (không 409)."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    create_resp = client.post("/api/v1/subjects", json={"subject_name": "Tiếng Anh"}, headers=headers)
    subject_id = create_resp.json()["subject_id"]
    # Update only description
    response = client.put(
        f"/api/v1/subjects/{subject_id}",
        json={"description": "Môn tiếng anh cập nhật"},
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["subject_name"] == "Tiếng Anh"
    assert response.json()["description"] == "Môn tiếng anh cập nhật"


# ---------------------------------------------------------------------------
# AC-07: DELETE — xóa thành công
# ---------------------------------------------------------------------------
def test_delete_subject_success(client: TestClient):
    """AC-07: Admin xóa môn học tồn tại → 204."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    create_resp = client.post("/api/v1/subjects", json={"subject_name": "Công Nghệ"}, headers=headers)
    subject_id = create_resp.json()["subject_id"]
    response = client.delete(f"/api/v1/subjects/{subject_id}", headers=headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    # Verify it's gone
    get_resp = client.get(f"/api/v1/subjects/{subject_id}", headers=headers)
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# EC-02: DELETE — ID không tồn tại → 404
# ---------------------------------------------------------------------------
def test_delete_subject_not_found(client: TestClient):
    """EC-02: Xóa môn học với ID không tồn tại → 404."""
    token = get_admin_token(client)
    fake_id = "00000000-0000-0000-0000-000000000001"
    response = client.delete(
        f"/api/v1/subjects/{fake_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"]["code"] == "ERR-ACAD-SUBJECT_NOT_FOUND"


# ---------------------------------------------------------------------------
# AC-08 / EC-03: Student gọi endpoint ghi → 403
# ---------------------------------------------------------------------------
def test_create_subject_forbidden_for_student(client: TestClient):
    """EC-03 / AC-08: User role Student gọi POST → 403 ERR-AUTH-FORBIDDEN."""
    token = get_student_token(client)
    response = client.post(
        "/api/v1/subjects",
        json={"subject_name": "Môn Bất Hợp Lệ"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"]["code"] == "ERR-AUTH-FORBIDDEN"


# ---------------------------------------------------------------------------
# Không có token → 401
# ---------------------------------------------------------------------------
def test_list_subjects_unauthorized(client: TestClient):
    """Gọi endpoint không có token → 401."""
    response = client.get("/api/v1/subjects")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
