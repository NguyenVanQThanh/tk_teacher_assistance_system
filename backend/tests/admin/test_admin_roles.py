# File Name: test_admin_roles.py
# Description: Integration tests for Admin user filters, live dashboard metrics, RBAC roles, analytics reports, and settings APIs.
# Created At: 2026-11-14
# Created By: Tam Khang
# Updated At: 2026-11-14
# Updated By: Tam Khang

import io
import json
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.rate_limit import reset_login_failures
from app.core.security import get_password_hash
from app.modules.auth.services.permission_service import PermissionService
from models.models import (
    ApprovalRequest,
    AuditLog,
    Class,
    ClassAssignment,
    Document,
    Exercise,
    Question,
    Role,
    RolePermission,
    StudentClass,
    StudentExerciseAttempt,
    Subject,
    SupportTicket,
    TeacherSubject,
    User,
)


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    for phone in ("0987654321", "0912345678", "0934567890"):
        reset_login_failures(phone)


def _login_headers(client: TestClient, phone: str = "0987654321") -> dict:
    res = client.post("/api/v1/auth/login", json={"phone": phone, "password": "password123"})
    assert res.status_code == status.HTTP_200_OK
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


class TestAdminRolesRouter:
    def test_roles_list_matrix_and_export(self, client: TestClient, db_session):
        headers = _login_headers(client)
        student_headers = _login_headers(client, phone="0934567890")

        # Non-admin must be denied
        forbidden = client.get("/api/v1/admin/roles", headers=student_headers)
        assert forbidden.status_code == status.HTTP_403_FORBIDDEN

        res = client.get("/api/v1/admin/roles", headers=headers)
        assert res.status_code == status.HTTP_200_OK
        body = res.json()
        codes = [r["code"] for r in body["roles"]]
        assert {"admin", "head_teacher", "subject_teacher", "academic_staff", "student_parent"}.issubset(set(codes))
        assert "view_schedule" in body["permissions_matrix"]["admin"]

        members_res = client.get("/api/v1/admin/roles/subject_teacher/members", headers=headers)
        assert members_res.status_code == status.HTTP_200_OK
        assert "items" in members_res.json()

        exp_json = client.get("/api/v1/admin/roles/export?format=json", headers=headers)
        assert exp_json.status_code == status.HTTP_200_OK
        assert "subject_teacher" in json.dumps(exp_json.json())

        exp_csv = client.get("/api/v1/admin/roles/export?format=csv", headers=headers)
        assert exp_csv.status_code == status.HTTP_200_OK
        assert "subject_teacher" in exp_csv.content.decode("utf-8-sig")
