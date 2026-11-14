# File Name: test_admin_account_locks.py
# Description: Tests for Admin account restrictions: no new admins, no admin deletion, no self-blocking, locked admin permissions.
# Created At: 2026-11-15
# Created By: AI Agent
# Updated At: 2026-11-15
# Updated By: AI Agent

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.rate_limit import reset_login_failures

ADMIN_PHONE = "0987654321"


@pytest.fixture
def admin_headers(client: TestClient):
    reset_login_failures(ADMIN_PHONE)
    resp = client.post("/api/v1/auth/login", json={"phone": ADMIN_PHONE, "password": "password123"})
    assert resp.status_code == status.HTTP_200_OK
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _admin_id(client, headers) -> str:
    return client.get("/api/v1/auth/me", headers=headers).json()["user_id"]


def _new_phone() -> str:
    return f"09{uuid.uuid4().int % 100000000:08d}"


def _create_teacher(client, headers) -> str:
    resp = client.post(
        "/api/v1/admin/users",
        json={"full_name": "Lock Test Teacher", "role": "Teacher", "birthday": "1990-01-01", "phone": _new_phone()},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED, resp.text
    return str(resp.json()["user_id"])


def test_cannot_create_admin_user(client, admin_headers):
    resp = client.post(
        "/api/v1/admin/users",
        json={"full_name": "Second Admin", "role": "Admin", "phone": _new_phone()},
        headers=admin_headers,
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert resp.json()["detail"]["code"] == "ERR-ADMIN-ADMIN_ROLE_LOCKED"


def test_cannot_promote_user_to_admin(client, admin_headers):
    teacher_id = _create_teacher(client, admin_headers)
    resp = client.put(f"/api/v1/admin/users/{teacher_id}", json={"role": "Admin"}, headers=admin_headers)
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    resp = client.post("/api/v1/admin/roles/admin/members", json={"user_id": teacher_id}, headers=admin_headers)
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_cannot_demote_admin_via_user_edit(client, admin_headers):
    admin_id = _admin_id(client, admin_headers)
    resp = client.put(f"/api/v1/admin/users/{admin_id}", json={"role": "Teacher"}, headers=admin_headers)
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert resp.json()["detail"]["code"] == "ERR-ADMIN-ADMIN_ROLE_LOCKED"


def test_cannot_delete_or_block_self(client, admin_headers):
    admin_id = _admin_id(client, admin_headers)
    assert client.delete(f"/api/v1/admin/users/{admin_id}", headers=admin_headers).status_code == 403
    resp = client.patch(
        f"/api/v1/admin/users/{admin_id}/status", json={"status": "SUSPENDED"}, headers=admin_headers
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert resp.json()["detail"]["code"] == "ERR-ADMIN-SELF_BLOCK_LOCKED"


def test_admin_role_permissions_and_template_locked(client, admin_headers):
    resp = client.put(
        "/api/v1/admin/roles/admin/permissions", json={"permissions": {"view_schedule": False}}, headers=admin_headers
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    resp = client.post(
        "/api/v1/admin/roles", json={"name": "Clone Of Admin", "template_role_code": "admin"}, headers=admin_headers
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_non_admin_user_can_still_be_deleted(client, admin_headers):
    teacher_id = _create_teacher(client, admin_headers)
    assert client.delete(f"/api/v1/admin/users/{teacher_id}", headers=admin_headers).status_code == 200
