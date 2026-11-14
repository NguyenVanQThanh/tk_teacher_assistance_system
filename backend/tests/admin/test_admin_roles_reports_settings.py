# File Name: test_admin_roles_reports_settings.py
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


class TestAdminUserFiltersAndDashboardMetrics:
    def test_list_users_grade_and_department_filters(self, client: TestClient, db_session):
        headers = _login_headers(client)

        student_role = db_session.query(Role).filter(Role.name == "Student").first()
        teacher_role = db_session.query(Role).filter(Role.name == "Teacher").first()

        # Create grade 10 student and grade 12 student
        s10 = User(
            user_id=uuid.uuid4(),
            full_name="Student Grade Ten",
            phone="0901000010",
            email="s10_filter@test.com",
            birthday=date(2008, 1, 15),
            role_id=student_role.role_id,
            password_hash=get_password_hash("password123"),
            status="ACTIVE",
        )
        s12 = User(
            user_id=uuid.uuid4(),
            full_name="Student Grade Twelve",
            phone="0901000012",
            email="s12_filter@test.com",
            birthday=date(2006, 1, 15),
            role_id=student_role.role_id,
            password_hash=get_password_hash("password123"),
            status="ACTIVE",
        )
        t_math = User(
            user_id=uuid.uuid4(),
            full_name="Teacher Math Dept",
            phone="0902000001",
            email="tmath_filter@test.com",
            birthday=date(1990, 5, 20),
            role_id=teacher_role.role_id,
            password_hash=get_password_hash("password123"),
            status="ACTIVE",
        )
        t_phys = User(
            user_id=uuid.uuid4(),
            full_name="Teacher Physics Dept",
            phone="0902000002",
            email="tphys_filter@test.com",
            birthday=date(1990, 6, 20),
            role_id=teacher_role.role_id,
            password_hash=get_password_hash("password123"),
            status="ACTIVE",
        )
        db_session.add_all([s10, s12, t_math, t_phys])
        db_session.flush()

        c10 = Class(class_id=uuid.uuid4(), class_name="10A1", academic_year="2025-2026", status="ACTIVE")
        c12 = Class(class_id=uuid.uuid4(), class_name="12A1", academic_year="2025-2026", status="ACTIVE")
        subj_math = Subject(subject_id=uuid.uuid4(), subject_name="Toán", status="ACTIVE")
        subj_phys = Subject(subject_id=uuid.uuid4(), subject_name="Vật lý", status="ACTIVE")
        db_session.add_all([c10, c12, subj_math, subj_phys])
        db_session.flush()

        db_session.add_all([
            StudentClass(student_id=s10.user_id, class_id=c10.class_id, student_code="HS1001", status="ACTIVE"),
            StudentClass(student_id=s12.user_id, class_id=c12.class_id, student_code="HS1201", status="ACTIVE"),
            TeacherSubject(teacher_id=t_math.user_id, class_id=c10.class_id, subject_id=subj_math.subject_id, status="ACTIVE"),
            TeacherSubject(teacher_id=t_phys.user_id, class_id=c12.class_id, subject_id=subj_phys.subject_id, status="ACTIVE"),
        ])
        db_session.commit()

        # Grade filter "10" and "k10"
        res_g10 = client.get("/api/v1/admin/users?grade=10&page_size=50", headers=headers)
        assert res_g10.status_code == status.HTTP_200_OK
        names_g10 = [u["full_name"] for u in res_g10.json()["items"]]
        assert "Student Grade Ten" in names_g10
        assert "Student Grade Twelve" not in names_g10

        # Department filter "Toán" and "math"
        res_math = client.get("/api/v1/admin/users?department=math&page_size=50", headers=headers)
        assert res_math.status_code == status.HTTP_200_OK
        names_math = [u["full_name"] for u in res_math.json()["items"]]
        assert "Teacher Math Dept" in names_math
        assert "Teacher Physics Dept" not in names_math

    def test_dashboard_live_metrics_and_activity_chart(self, client: TestClient, db_session):
        headers = _login_headers(client)
        admin_user = db_session.query(User).filter(User.phone == "0987654321").first()
        student_user = db_session.query(User).filter(User.phone == "0934567890").first()

        subj = Subject(subject_id=uuid.uuid4(), subject_name="Chemistry", status="ACTIVE")
        cls = Class(class_id=uuid.uuid4(), class_name="11A2", academic_year="2025-2026", status="ACTIVE")
        db_session.add_all([subj, cls])
        db_session.flush()

        doc = Document(
            document_id=uuid.uuid4(),
            uploaded_by=admin_user.user_id,
            subject_id=subj.subject_id,
            title="Organic Chemistry Notes",
            file_url="https://example.com/chem.pdf",
            file_type="pdf",
            download_count=37,
            status="ACTIVE",
        )
        ex = Exercise(
            exercise_id=uuid.uuid4(),
            title="Quiz 1",
            subject_id=subj.subject_id,
            created_by=admin_user.user_id,
            total_questions=5,
            exercise_kind="ai_generated",
            status="ACTIVE",
        )
        db_session.add_all([doc, ex])
        db_session.flush()

        assign = ClassAssignment(
            assignment_id=uuid.uuid4(),
            exercise_id=ex.exercise_id,
            class_id=cls.class_id,
            assigned_by=admin_user.user_id,
            due_at=datetime.now(timezone.utc) + timedelta(days=3),
            status="ACTIVE",
        )
        db_session.add(assign)
        db_session.flush()

        attempt = StudentExerciseAttempt(
            attempt_id=uuid.uuid4(),
            student_id=student_user.user_id,
            assignment_id=assign.assignment_id,
            score=9.0,
            is_finished=True,
            status="ACTIVE",
        )
        db_session.add(attempt)
        db_session.commit()

        stats_res = client.get("/api/v1/admin/dashboard/stats", headers=headers)
        assert stats_res.status_code == status.HTTP_200_OK
        stats_data = stats_res.json()
        assert stats_data["lecture_views"] == 37
        assert stats_data["assignments_submitted"] == 1

        chart_week = client.get("/api/v1/admin/dashboard/activity-chart?timeframe=week", headers=headers)
        assert chart_week.status_code == status.HTTP_200_OK
        week_data = chart_week.json()
        assert len(week_data["points"]) == 7
        assert week_data["lecture_views"] == 37
        assert week_data["assignments_submitted"] == 1

        chart_month = client.get("/api/v1/admin/dashboard/activity-chart?timeframe=month", headers=headers)
        assert chart_month.status_code == status.HTTP_200_OK
        assert len(chart_month.json()["points"]) == 4


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
