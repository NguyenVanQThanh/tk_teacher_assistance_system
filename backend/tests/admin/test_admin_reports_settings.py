# File Name: test_admin_reports_settings.py
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


class TestAdminReportsRouter:
    def test_reports_analytics_export_custom_and_schedules(self, client: TestClient, db_session):
        headers = _login_headers(client)

        res = client.get(
            "/api/v1/admin/reports/analytics?academic_year=2025-2026&semester=HK1&grade=k10&department=all&timeframe=week",
            headers=headers,
        )
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert "kpis" in data
        assert len(data["grade_distributions"]) == 1
        assert data["grade_distributions"][0]["grade_code"] == "k10"
        assert len(data["time_series"]) == 7

        # Export CSV, JSON, HTML-PDF
        for fmt in ("csv", "json", "pdf"):
            exp = client.get(f"/api/v1/admin/reports/export?format={fmt}", headers=headers)
            assert exp.status_code == status.HTTP_200_OK
            assert len(exp.content) > 20

        # Custom report
        custom = client.post(
            "/api/v1/admin/reports/custom",
            headers=headers,
            json={
                "title": "Midterm AI Adoption Review",
                "metricType": "ai_usage",
                "format": "pdf",
                "frequency": "once",
            },
        )
        assert custom.status_code == status.HTTP_201_CREATED
        assert custom.json()["title"] == "Midterm AI Adoption Review"

        # Schedules GET/POST/DELETE (soft delete)
        sched = client.post(
            "/api/v1/admin/reports/schedules",
            headers=headers,
            json={
                "title": "Weekly Executive Summary",
                "frequency": "weekly",
                "format": "csv",
                "recipients": ["principal@smartlms.edu.vn"],
            },
        )
        assert sched.status_code == status.HTTP_201_CREATED
        sched_id = sched.json()["id"]

        listed = client.get("/api/v1/admin/reports/schedules", headers=headers)
        assert listed.status_code == status.HTTP_200_OK
        assert any(item["id"] == sched_id for item in listed.json()["items"])

        deleted = client.delete(f"/api/v1/admin/reports/schedules/{sched_id}", headers=headers)
        assert deleted.status_code == status.HTTP_200_OK
        listed_after = client.get("/api/v1/admin/reports/schedules", headers=headers)
        assert all(item["id"] != sched_id for item in listed_after.json()["items"])


class TestAdminSettingsRouter:
    def test_settings_persistence_ai_ping_and_backups(self, client: TestClient, db_session):
        headers = _login_headers(client)

        get_res = client.get("/api/v1/admin/settings", headers=headers)
        assert get_res.status_code == status.HTTP_200_OK
        init_data = get_res.json()
        assert {"general", "ai", "grading", "security", "maintenance"}.issubset(set(init_data.keys()))

        put_res = client.put(
            "/api/v1/admin/settings",
            headers=headers,
            json={
                "general": {"schoolName": "Updated Smart High School"},
                "ai": {"temperature": 0.5, "apiKey": "secret-test-key-9876"},
            },
        )
        assert put_res.status_code == status.HTTP_200_OK
        assert put_res.json()["general"]["schoolName"] == "Updated Smart High School"
        assert put_res.json()["ai"]["temperature"] == 0.5
        assert "secret-test-key" not in put_res.json()["ai"]["apiKey"]
        assert put_res.json()["ai"]["apiKey"].endswith("9876")

        # Verify persisted on subsequent GET
        get_after = client.get("/api/v1/admin/settings", headers=headers)
        assert get_after.status_code == status.HTTP_200_OK
        assert get_after.json()["general"]["schoolName"] == "Updated Smart High School"

        # AI Ping
        ping_res = client.post(
            "/api/v1/admin/settings/ai-ping",
            headers=headers,
            json={"provider": "google_gemini", "model": "gemini-2.5-flash"},
        )
        assert ping_res.status_code == status.HTTP_200_OK
        assert ping_res.json()["status"] == "connected"
        assert ping_res.json()["latency_ms"] >= 1

        # Backups create, list, download
        b_create = client.post("/api/v1/admin/settings/backups", headers=headers)
        assert b_create.status_code == status.HTTP_201_CREATED
        b_item = b_create.json()["item"]
        assert b_item["table_counts"]["users"] >= 1

        b_list = client.get("/api/v1/admin/settings/backups", headers=headers)
        assert b_list.status_code == status.HTTP_200_OK
        assert any(i["id"] == b_item["id"] for i in b_list.json()["items"])

        b_dl = client.get(f"/api/v1/admin/settings/backups/{b_item['id']}/download", headers=headers)
        assert b_dl.status_code == status.HTTP_200_OK
        dl_json = b_dl.json()
        assert "table_counts" in dl_json

        # Ensure internal state records are hidden from human-facing dashboard audit-logs
        audit_res = client.get("/api/v1/admin/dashboard/audit-logs?limit=20", headers=headers)
        assert audit_res.status_code == status.HTTP_200_OK
        titles = [row["title"] for row in audit_res.json()]
        assert "__SYS_SETTINGS__" not in titles
        assert "__BACKUP_SNAPSHOT__" not in titles
        assert "Updated System Settings" in titles


