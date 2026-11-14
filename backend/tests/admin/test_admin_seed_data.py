# File Name: test_admin_seed_data.py
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
from app.scripts.seed_admin_portal_data import seed_admin_portal_data
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


class TestAdminPortalSeedData:
    def test_seed_admin_portal_data_idempotent(self, client: TestClient, db_session):
        first_summary = seed_admin_portal_data(db_session)
        assert first_summary["users_created"] > 0
        assert first_summary["subjects_created"] == 7
        assert first_summary["classes_created"] == 9
        assert first_summary["enrollments_created"] == 24
        assert first_summary["teacher_subjects_created"] == 14
        assert first_summary["approvals_created"] == 6
        assert first_summary["tickets_created"] == 3
        assert first_summary["audit_logs_created"] == 10
        assert first_summary["exercises_created"] == 14
        assert first_summary["questions_created"] == 42
        assert first_summary["assignments_created"] == 14
        assert first_summary["attempts_created"] == 42
        assert first_summary["settings_created"] == 1
        assert first_summary["report_schedules_created"] == 3
        assert first_summary["custom_reports_created"] == 3
        assert first_summary["backups_created"] == 3

        tracked_models = (
            User,
            Role,
            Subject,
            Class,
            StudentClass,
            TeacherSubject,
            ApprovalRequest,
            SupportTicket,
            AuditLog,
            Exercise,
            Question,
            ClassAssignment,
            StudentExerciseAttempt,
        )
        counts_after_first = {model.__name__: db_session.query(model).count() for model in tracked_models}

        # Second call must be strictly idempotent with zero duplicate creations
        second_summary = seed_admin_portal_data(db_session)
        for key in (
            "users_created",
            "users_backfilled_birthday",
            "users_backfilled_gender",
            "subjects_created",
            "classes_created",
            "enrollments_created",
            "teacher_subjects_created",
            "approvals_created",
            "tickets_created",
            "audit_logs_created",
            "exercises_created",
            "questions_created",
            "assignments_created",
            "attempts_created",
            "settings_created",
            "report_schedules_created",
            "custom_reports_created",
            "backups_created",
            "accounts_json_updates",
        ):
            assert second_summary[key] == 0, f"Expected {key} == 0 on second run, got {second_summary[key]}"

        counts_after_second = {model.__name__: db_session.query(model).count() for model in tracked_models}
        assert counts_after_second == counts_after_first

        # Verify all Admin Portal endpoints return populated data from the seeded DB
        headers = _login_headers(client)

        stats_res = client.get("/api/v1/admin/dashboard/stats", headers=headers)
        assert stats_res.status_code == status.HTTP_200_OK
        stats_data = stats_res.json()
        assert stats_data["total_students"] > 0
        assert stats_data["total_teachers"] > 0
        assert stats_data["total_classes"] >= 9
        assert stats_data["assignments_submitted"] >= 42

        req_res = client.get("/api/v1/admin/dashboard/requests", headers=headers)
        assert req_res.status_code == status.HTTP_200_OK
        assert len(req_res.json()) >= 6

        logs_res = client.get("/api/v1/admin/dashboard/audit-logs", headers=headers)
        assert logs_res.status_code == status.HTTP_200_OK
        assert len(logs_res.json()) >= 10

        roles_res = client.get("/api/v1/admin/roles", headers=headers)
        assert roles_res.status_code == status.HTTP_200_OK
        roles_payload = roles_res.json()
        assert len(roles_payload["roles"]) >= 5
        head_role = next(r for r in roles_payload["roles"] if r["code"] == "head_teacher")
        assert head_role["memberCount"] >= 2

        head_members_res = client.get("/api/v1/admin/roles/head_teacher/members", headers=headers)
        assert head_members_res.status_code == status.HTTP_200_OK
        head_members = head_members_res.json()["items"]
        assert len(head_members) > 0
        assert head_role["memberCount"] == len(head_members)

        analytics_res = client.get("/api/v1/admin/reports/analytics", headers=headers)
        assert analytics_res.status_code == status.HTTP_200_OK
        analytics_data = analytics_res.json()
        assert analytics_data["kpis"]["total_exercises"] >= 14
        assert analytics_data["kpis"]["total_attempts"] >= 42
        assert len(analytics_data["grade_distributions"]) > 0
        assert len(analytics_data["time_series"]) > 0

        schedules_res = client.get("/api/v1/admin/reports/schedules", headers=headers)
        assert schedules_res.status_code == status.HTTP_200_OK
        assert len(schedules_res.json()["items"]) >= 3

        settings_res = client.get("/api/v1/admin/settings", headers=headers)
        assert settings_res.status_code == status.HTTP_200_OK
        settings_data = settings_res.json()
        assert {"general", "ai", "grading", "security", "maintenance"}.issubset(set(settings_data.keys()))
        assert settings_data["general"]["schoolName"]

        backups_res = client.get("/api/v1/admin/settings/backups", headers=headers)
        assert backups_res.status_code == status.HTTP_200_OK
        assert len(backups_res.json()["items"]) >= 3

        avail_res = client.get("/api/v1/classes/available-students", headers=headers)
        assert avail_res.status_code == status.HTTP_200_OK
        avail_items = avail_res.json()["items"]
        assert len(avail_items) >= 8
        avail_phones = {item["phone"] for item in avail_items}
        assert {f"099920000{i}" for i in range(2, 10)}.issubset(avail_phones)

