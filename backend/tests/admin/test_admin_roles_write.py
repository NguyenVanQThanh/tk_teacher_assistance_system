# File Name: test_admin_roles_write.py
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
    def test_roles_crud_permissions_members_and_export(self, client: TestClient, db_session):
        headers = _login_headers(client)
        student_headers = _login_headers(client, phone="0934567890")

        # Non-admin must be denied
        forbidden = client.get("/api/v1/admin/roles", headers=student_headers)
        assert forbidden.status_code == status.HTTP_403_FORBIDDEN

        # GET /api/v1/admin/roles
        res = client.get("/api/v1/admin/roles", headers=headers)
        assert res.status_code == status.HTTP_200_OK
        body = res.json()
        codes = [r["code"] for r in body["roles"]]
        assert {"admin", "head_teacher", "subject_teacher", "academic_staff", "student_parent"}.issubset(set(codes))
        assert "view_schedule" in body["permissions_matrix"]["admin"]

        # POST /api/v1/admin/roles (clone from subject_teacher)
        create_res = client.post(
            "/api/v1/admin/roles",
            headers=headers,
            json={
                "name": "Lab Assistant",
                "code": "lab_assistant",
                "description": "Supports science labs",
                "template_role_code": "subject_teacher",
            },
        )
        assert create_res.status_code == status.HTTP_201_CREATED
        assert create_res.json()["code"] == "lab_assistant"
        assert create_res.json()["permissions"]["ai_exercise"] is True

        # PUT /api/v1/admin/roles/{role_code}/permissions
        upd_res = client.put(
            "/api/v1/admin/roles/lab_assistant/permissions",
            headers=headers,
            json={"permissions": {"ai_exercise": False, "create_class": True}},
        )
        assert upd_res.status_code == status.HTTP_200_OK
        assert upd_res.json()["permissions"]["ai_exercise"] is False
        assert upd_res.json()["permissions"]["create_class"] is True

        created_role = db_session.query(Role).filter(Role.name == "lab_assistant").first()
        assert created_role is not None
        effective = PermissionService.get_role_permissions(db_session, created_role.role_id)
        assert "create_class" in effective
        assert "ai_exercise" not in effective

        # POST & GET /api/v1/admin/roles/{role_code}/members
        extra_user = User(
            user_id=uuid.uuid4(),
            full_name="Assistant Member",
            phone="0903000001",
            email="assistant@test.com",
            birthday=date(1992, 3, 10),
            role_id=db_session.query(Role).filter(Role.name == "Teacher").first().role_id,
            password_hash=get_password_hash("password123"),
            status="ACTIVE",
        )
        db_session.add(extra_user)
        db_session.commit()

        assign_res = client.post(
            "/api/v1/admin/roles/lab_assistant/members",
            headers=headers,
            json={"user_id": str(extra_user.user_id)},
        )
        assert assign_res.status_code == status.HTTP_200_OK

        members_res = client.get("/api/v1/admin/roles/lab_assistant/members", headers=headers)
        assert members_res.status_code == status.HTTP_200_OK
        assert any(m["full_name"] == "Assistant Member" for m in members_res.json()["items"])

        # Export JSON & CSV
        exp_json = client.get("/api/v1/admin/roles/export?format=json", headers=headers)
        assert exp_json.status_code == status.HTTP_200_OK
        assert "lab_assistant" in json.dumps(exp_json.json())

        exp_csv = client.get("/api/v1/admin/roles/export?format=csv", headers=headers)
        assert exp_csv.status_code == status.HTTP_200_OK
        assert "lab_assistant" in exp_csv.content.decode("utf-8-sig")



class TestAdminRolesWriteAuthorization:
    def test_non_admin_denied_on_write_endpoints(self, client: TestClient, db_session):
        student_headers = _login_headers(client, phone="0934567890")
        post = client.post("/api/v1/admin/roles", headers=student_headers, json={"name": "Hack"})
        put = client.put(
            "/api/v1/admin/roles/student_parent/permissions",
            headers=student_headers,
            json={"permissions": {"create_class": True}},
        )
        assign = client.post(
            "/api/v1/admin/roles/subject_teacher/members",
            headers=student_headers,
            json={"user_id": str(uuid.uuid4())},
        )
        assert post.status_code == status.HTTP_403_FORBIDDEN
        assert put.status_code == status.HTTP_403_FORBIDDEN
        assert assign.status_code == status.HTTP_403_FORBIDDEN

    def test_unknown_permission_code_rejected(self, client: TestClient, db_session):
        headers = _login_headers(client)
        res = client.put(
            "/api/v1/admin/roles/subject_teacher/permissions",
            headers=headers,
            json={"permissions": {"not_a_real_permission": True}},
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST
