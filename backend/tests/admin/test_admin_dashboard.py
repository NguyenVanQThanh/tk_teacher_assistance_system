# File Name: test_admin_dashboard.py
# Description: Integration tests for Admin Dashboard, statistics, approval requests, and audit logs.
# Created At: 2026-09-30
# Created By: Tam Khang
# Updated At: 2026-09-30
# Updated By: Tam Khang

import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.rate_limit import reset_login_failures
from models.models import ApprovalRequest, AuditLog
from tests.conftest import TestingSessionLocal


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


class TestAdminDashboard:
    def test_get_dashboard_stats(self, client: TestClient):
        """Verify dashboard statistics return correct KPI metrics."""
        token = get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.get("/api/v1/admin/dashboard/stats", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "total_students" in data
        assert "total_teachers" in data
        assert "total_classes" in data
        assert "attendance_rate" in data
        assert "lecture_views" in data
        assert "assignments_submitted" in data

    def test_get_activity_chart(self, client: TestClient):
        """Verify activity chart returns points for week and month."""
        token = get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        resp_week = client.get("/api/v1/admin/dashboard/activity-chart?timeframe=week", headers=headers)
        assert resp_week.status_code == status.HTTP_200_OK
        week_data = resp_week.json()
        assert len(week_data["points"]) == 7

        resp_month = client.get("/api/v1/admin/dashboard/activity-chart?timeframe=month", headers=headers)
        assert resp_month.status_code == status.HTTP_200_OK
        month_data = resp_month.json()
        assert len(month_data["points"]) == 4

    def test_approval_requests_flow(self, client: TestClient, db_session):
        """Verify approval request listing, approval, and rejection workflow."""
        token = get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Seed a test request
        req1 = ApprovalRequest(
            requester_name="Dr. Johnson",
            requester_sub="Mathematics",
            type="New Course Opening",
            status="pending"
        )
        req2 = ApprovalRequest(
            requester_name="Ms. Miller",
            requester_sub="Physics",
            type="Equipment Request",
            status="pending"
        )
        db_session.add_all([req1, req2])
        db_session.commit()
        db_session.refresh(req1)
        db_session.refresh(req2)
        req1_id = str(req1.request_id)
        req2_id = str(req2.request_id)

        # 1. List requests
        resp_list = client.get("/api/v1/admin/dashboard/requests", headers=headers)
        assert resp_list.status_code == status.HTTP_200_OK
        items = resp_list.json()
        assert any(item["id"] == req1_id for item in items)
        assert any(item["id"] == req2_id for item in items)

        # 2. Approve req1
        resp_approve = client.post(f"/api/v1/admin/dashboard/requests/{req1_id}/approve", headers=headers)
        assert resp_approve.status_code == status.HTTP_200_OK
        approve_data = resp_approve.json()
        assert approve_data["request"]["status"] == "approved"

        # 3. Reject req2
        resp_reject = client.post(f"/api/v1/admin/dashboard/requests/{req2_id}/reject", headers=headers)
        assert resp_reject.status_code == status.HTTP_200_OK
        reject_data = resp_reject.json()
        assert reject_data["request"]["status"] == "rejected"

    def test_audit_logs(self, client: TestClient):
        """Verify audit logs listing endpoint."""
        token = get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.get("/api/v1/admin/dashboard/audit-logs?limit=5", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        logs = resp.json()
        assert isinstance(logs, list)

    def test_unauthorized_access_fails(self, client: TestClient):
        """Verify requests without token are rejected with 401."""
        resp = client.get("/api/v1/admin/dashboard/stats")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
