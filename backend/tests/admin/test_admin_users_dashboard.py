# File Name: test_admin_users_dashboard.py
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


