# File Name: test_admin_users.py
# Description: Integration tests for Admin User Management (F-ADMIN-01), validation rules, auto default password, and soft delete.
# Created At: 2026-09-29
# Created By: Tam Khang
# Updated At: 2026-09-29
# Updated By: Tam Khang

import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.rate_limit import reset_login_failures


@pytest.fixture(autouse=True)
def clear_rate_limits():
    reset_login_failures("0987654321")


def get_admin_token(client: TestClient) -> str:
    """Helper to authenticate as default test admin."""
    reset_login_failures("0987654321")
    resp = client.post(
        "/api/v1/auth/login",
        json={"phone": "0987654321", "password": "password123"}
    )
    assert resp.status_code == status.HTTP_200_OK
    return resp.json()["access_token"]


class TestAdminUserValidation:
    def test_create_user_student_under_16_fails(self, client: TestClient):
        """Verify student under 16 years old is rejected with 422."""
        token = get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.post(
            "/api/v1/admin/users",
            json={
                "full_name": "Young Student",
                "role": "Student",
                "birthday": "2015-01-01",
                "phone": f"09{uuid.uuid4().int % 100000000:08d}"
            },
            headers=headers
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail = resp.json()["detail"]
        assert "Student must be at least 16 years old" in detail["message"]

    def test_create_user_teacher_under_22_fails(self, client: TestClient):
        """Verify teacher under 22 years old is rejected with 422."""
        token = get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.post(
            "/api/v1/admin/users",
            json={
                "full_name": "Young Teacher",
                "role": "Teacher",
                "birthday": "2008-01-01",
                "phone": f"09{uuid.uuid4().int % 100000000:08d}"
            },
            headers=headers
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail = resp.json()["detail"]
        assert "Teacher must be at least 22 years old" in detail["message"]

    def test_create_user_future_birthday_fails(self, client: TestClient):
        """Verify birthday in the future is rejected with 422."""
        token = get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.post(
            "/api/v1/admin/users",
            json={
                "full_name": "Time Traveler",
                "role": "Student",
                "birthday": "2030-01-01"
            },
            headers=headers
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail = resp.json()["detail"]
        assert "Birthday cannot be in the future" in detail["message"]

    def test_create_user_invalid_phone_fails(self, client: TestClient):
        """Verify invalid Vietnamese phone format is rejected with 422."""
        token = get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.post(
            "/api/v1/admin/users",
            json={
                "full_name": "Invalid Phone User",
                "role": "Student",
                "birthday": "2006-01-01",
                "phone": "12345"
            },
            headers=headers
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_user_duplicate_phone_fails(self, client: TestClient):
        """Verify duplicate phone registration is rejected with 400."""
        token = get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.post(
            "/api/v1/admin/users",
            json={
                "full_name": "Dup Phone User",
                "role": "Student",
                "birthday": "2006-01-01",
                "phone": "0987654321"
            },
            headers=headers
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        detail = resp.json()["detail"]
        assert "already registered" in detail["message"]


class TestAutoPasswordAndNotification:
    def test_auto_generate_default_password_and_sms_notification(self, client: TestClient):
        """Verify default password is automatically generated and notification confirmation returned."""
        token = get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        unique_phone = f"09{uuid.uuid4().int % 100000000:08d}"
        unique_email = f"auto_user_{uuid.uuid4().hex[:6]}@school.com"

        resp = client.post(
            "/api/v1/admin/users",
            json={
                "full_name": "Auto Password Student",
                "role": "Student",
                "birthday": "2007-06-15",
                "phone": unique_phone,
                "email": unique_email
            },
            headers=headers
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()

        # Check auto-generated password structure
        temp_pwd = data.get("temporary_password")
        assert temp_pwd is not None
        assert temp_pwd.startswith("Edu@")
        assert len(temp_pwd) >= 8

        # Check notification confirmation
        assert data.get("notification_sent") is True
        assert "SMS" in data.get("notification_channel")

        # Verify new user can actually authenticate with this generated password
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"phone": unique_phone, "password": temp_pwd}
        )
        assert login_resp.status_code == status.HTTP_200_OK

    def test_reset_password_generates_new_default_and_notifies(self, client: TestClient):
        """Verify resetting password auto-generates temporary password and dispatches notification."""
        token = get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        unique_phone = f"09{uuid.uuid4().int % 100000000:08d}"
        create_resp = client.post(
            "/api/v1/admin/users",
            json={
                "full_name": "Reset Password Test User",
                "role": "Student",
                "birthday": "2007-01-01",
                "phone": unique_phone
            },
            headers=headers
        )
        assert create_resp.status_code == status.HTTP_201_CREATED
        user_id = create_resp.json()["id"]

        # Call reset-password
        reset_resp = client.post(
            f"/api/v1/admin/users/{user_id}/reset-password",
            json={},
            headers=headers
        )
        assert reset_resp.status_code == status.HTTP_200_OK
        data = reset_resp.json()
        assert data.get("temporary_password") is not None
        assert data.get("notification_sent") is True

        # Verify new login works with reset password
        new_pwd = data["temporary_password"]
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"phone": unique_phone, "password": new_pwd}
        )
        assert login_resp.status_code == status.HTTP_200_OK


class TestAdminUserLifecycleAndSoftDelete:
    def test_user_lifecycle_crud_status_and_soft_delete(self, client: TestClient):
        """Verify user list, update, status patch, soft delete, and restore flow."""
        token = get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        unique_phone = f"09{uuid.uuid4().int % 100000000:08d}"
        create_resp = client.post(
            "/api/v1/admin/users",
            json={
                "full_name": "Lifecycle Test User",
                "role": "Teacher",
                "birthday": "1990-05-20",
                "phone": unique_phone,
                "department": "Tổ Toán"
            },
            headers=headers
        )
        assert create_resp.status_code == status.HTTP_201_CREATED
        user_id = create_resp.json()["id"]

        # 1. Update user
        update_resp = client.put(
            f"/api/v1/admin/users/{user_id}",
            json={"full_name": "Updated Lifecycle User"},
            headers=headers
        )
        assert update_resp.status_code == status.HTTP_200_OK
        assert update_resp.json()["full_name"] == "Updated Lifecycle User"

        # 2. Update status to SUSPENDED
        patch_resp = client.patch(
            f"/api/v1/admin/users/{user_id}/status",
            json={"status": "SUSPENDED", "reason": "Administrative Review"},
            headers=headers
        )
        assert patch_resp.status_code == status.HTTP_200_OK
        assert patch_resp.json()["status"] == "SUSPENDED"

        # 3. Soft delete user (Must update status to DELETED, NOT hard delete)
        del_resp = client.delete(
            f"/api/v1/admin/users/{user_id}",
            headers=headers
        )
        assert del_resp.status_code == status.HTTP_200_OK
        assert del_resp.json()["status"] == "DELETED"

        # 4. Normal list must exclude DELETED user by default
        list_resp = client.get(
            f"/api/v1/admin/users?search=Updated%20Lifecycle%20User",
            headers=headers
        )
        assert list_resp.status_code == status.HTTP_200_OK
        items = list_resp.json()["items"]
        assert all(u["id"] != user_id for u in items)

        # 5. Restore user back to ACTIVE
        restore_resp = client.post(
            f"/api/v1/admin/users/{user_id}/restore",
            headers=headers
        )
        assert restore_resp.status_code == status.HTTP_200_OK
        assert restore_resp.json()["status"] == "ACTIVE"

        # 6. Verify restored user appears in active list again
        active_list_resp = client.get(
            f"/api/v1/admin/users?search=Updated%20Lifecycle%20User",
            headers=headers
        )
        assert active_list_resp.status_code == status.HTTP_200_OK
        assert any(u["id"] == user_id for u in active_list_resp.json()["items"])

    def test_export_users_csv(self, client: TestClient):
        """Verify export endpoint returns UTF-8 BOM CSV stream."""
        token = get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.get(
            "/api/v1/admin/users/export-excel",
            headers=headers
        )
        assert resp.status_code == status.HTTP_200_OK
        assert "text/csv" in resp.headers["content-type"]
        # Must start with UTF-8 BOM for Excel compatibility
        assert resp.content.startswith(b"\xef\xbb\xbf")
