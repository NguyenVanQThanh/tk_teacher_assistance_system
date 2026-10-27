# File Name: test_assignments.py
# Description: Unit & Integration tests for F-EXE-02 Class Assignments module (creation, scoping, feed, soft-delete, restore, validation).
# Created At: 2026-07-31
# Created By: Tam Khang
# Updated At: 2026-10-03
# Updated By: Tam Khang

import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi import status
from fastapi.testclient import TestClient


def get_admin_token(client: TestClient) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"phone": "0987654321", "password": "password123"}
    )
    return resp.json()["access_token"]


def get_teacher_token(client: TestClient) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"phone": "0912345678", "password": "password123"}
    )
    return resp.json()["access_token"]


def get_student_token(client: TestClient) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"phone": "0934567890", "password": "password123"}
    )
    return resp.json()["access_token"]


class TestClassAssignmentModule:
    def test_create_assignment_due_at_in_past_raises_422(self, client: TestClient):
        admin_token = get_admin_token(client)
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 1. Create Class
        class_resp = client.post(
            "/api/v1/classes",
            json={"class_name": f"Lop 10A{uuid.uuid4().hex[:4]}", "school_year": "2025-2026"},
            headers=admin_headers
        )
        assert class_resp.status_code == status.HTTP_201_CREATED
        class_id = class_resp.json()["class_id"]

        # 2. Try creating assignment with due_at in the past -> 422
        past_time = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        resp = client.post(
            f"/api/v1/classes/{class_id}/assignments",
            json={"exercise_id": str(uuid.uuid4()), "due_at": past_time},
            headers=admin_headers
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_assignment_lifecycle_and_scoping(self, client: TestClient):
        admin_token = get_admin_token(client)
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        teacher_token = get_teacher_token(client)
        teacher_headers = {"Authorization": f"Bearer {teacher_token}"}

        # 1. Admin creates Subject 1 and Subject 2
        s1 = client.post(
            "/api/v1/subjects",
            json={"subject_name": f"Vat Ly {uuid.uuid4().hex[:6]}"},
            headers=admin_headers
        ).json()["subject_id"]

        s2 = client.post(
            "/api/v1/subjects",
            json={"subject_name": f"Hoa Hoc {uuid.uuid4().hex[:6]}"},
            headers=admin_headers
        ).json()["subject_id"]

        # 2. Admin creates Class
        c1 = client.post(
            "/api/v1/classes",
            json={"class_name": f"10B{uuid.uuid4().hex[:4]}", "school_year": "2025-2026"},
            headers=admin_headers
        ).json()["class_id"]

        # 3. Admin assigns Teacher to Class c1 for Subject s1 (Vat Ly) only
        # Teacher ID for phone 0912345678 can be retrieved via me
        teacher_me = client.get("/api/v1/auth/me", headers=teacher_headers).json()
        teacher_id = teacher_me["user_id"]

        assign_resp = client.post(
            f"/api/v1/classes/{c1}/teacher-subjects",
            json={"teacher_id": teacher_id, "subject_id": s1},
            headers=admin_headers
        )

        assert assign_resp.status_code == status.HTTP_201_CREATED

        # 4. Create Exercise for Vat Ly (s1) and Exercise for Hoa Hoc (s2)
        ex_vat_ly = client.post(
            "/api/v1/exercises",
            json={"title": "Bai tap Vat Ly 1", "subject_id": s1},
            headers=admin_headers
        ).json()["exercise_id"]

        ex_hoa_hoc = client.post(
            "/api/v1/exercises",
            json={"title": "Bai tap Hoa Hoc 1", "subject_id": s2},
            headers=admin_headers
        ).json()["exercise_id"]

        # 5. Teacher tries to assign Hoa Hoc (s2) to Class c1 -> 403 (Teacher does not teach Hoa Hoc in c1)
        future_due = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        resp_403 = client.post(
            f"/api/v1/classes/{c1}/assignments",
            json={"exercise_id": ex_hoa_hoc, "due_at": future_due},
            headers=teacher_headers
        )
        assert resp_403.status_code == status.HTTP_403_FORBIDDEN
        assert resp_403.json()["detail"]["code"] == "ERR-EXE-CLASS_ACCESS_DENIED"

        # 6. Teacher assigns Vat Ly (s1) to Class c1 -> 201 CREATED
        resp_201 = client.post(
            f"/api/v1/classes/{c1}/assignments",
            json={"exercise_id": ex_vat_ly, "due_at": future_due},
            headers=teacher_headers
        )
        assert resp_201.status_code == status.HTTP_201_CREATED
        assignment_id = resp_201.json()["assignment_id"]
        assert resp_201.json()["status"] == "ACTIVE"

        # 7. Teacher tries to assign Vat Ly (ex_vat_ly) again to Class c1 -> 409 DUPLICATE
        resp_409 = client.post(
            f"/api/v1/classes/{c1}/assignments",
            json={"exercise_id": ex_vat_ly, "due_at": future_due},
            headers=teacher_headers
        )
        assert resp_409.status_code == status.HTTP_409_CONFLICT
        assert resp_409.json()["detail"]["code"] == "ERR-EXE-DUPLICATE_ASSIGNMENT"

        # 8. List assignments for class c1 as Teacher -> 200 OK (length 1)
        list_resp = client.get(f"/api/v1/classes/{c1}/assignments", headers=teacher_headers)
        assert list_resp.status_code == status.HTTP_200_OK
        assert len(list_resp.json()) == 1

        # 9. Teacher soft deletes assignment -> 204 NO CONTENT
        del_resp = client.delete(f"/api/v1/assignments/{assignment_id}", headers=teacher_headers)
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT

        # 10. List assignments for class c1 -> 0 (deleted not included)
        list_resp_after = client.get(f"/api/v1/classes/{c1}/assignments", headers=teacher_headers)
        assert list_resp_after.status_code == status.HTTP_200_OK
        assert len(list_resp_after.json()) == 0

        # 11. Restore assignment -> 200 OK (status ACTIVE)
        restore_resp = client.post(f"/api/v1/assignments/{assignment_id}/restore", headers=teacher_headers)
        assert restore_resp.status_code == status.HTTP_200_OK
        assert restore_resp.json()["status"] == "ACTIVE"

        # 12. List assignments after restore -> length 1
        list_resp_restored = client.get(f"/api/v1/classes/{c1}/assignments", headers=teacher_headers)
        assert list_resp_restored.status_code == status.HTTP_200_OK
        assert len(list_resp_restored.json()) == 1

        # 13. Test student feed (GET /api/v1/assignments)
        student_token = get_student_token(client)
        student_headers = {"Authorization": f"Bearer {student_token}"}
        student_me = client.get("/api/v1/auth/me", headers=student_headers).json()
        student_id = student_me["user_id"]

        # Enroll student in class c1
        client.post(
            f"/api/v1/classes/{c1}/students",
            json={"student_id": student_id, "student_code": f"STU{uuid.uuid4().hex[:6]}"},
            headers=admin_headers
        )

        # Student calls GET /api/v1/assignments
        feed_resp = client.get("/api/v1/assignments", headers=student_headers)
        assert feed_resp.status_code == status.HTTP_200_OK
        feed_data = feed_resp.json()
        assert len(feed_data) >= 1
        item = next((a for a in feed_data if a["assignment_id"] == assignment_id), None)
        assert item is not None
        assert item["exercise_title"] == "Bai tap Vat Ly 1"
        assert item["feed_status"] == "active"
        assert item["completed_attempts_count"] == 0

        # Test search filter
        search_resp = client.get("/api/v1/assignments?search=Vat+Ly", headers=student_headers)
        assert search_resp.status_code == status.HTTP_200_OK
        assert any(a["assignment_id"] == assignment_id for a in search_resp.json())

        no_match_resp = client.get("/api/v1/assignments?search=NonExistent12345", headers=student_headers)
        assert no_match_resp.status_code == status.HTTP_200_OK
        assert len(no_match_resp.json()) == 0

        # 14. Test assignment result & attempt history API (GET /api/v1/assignments/{id}/result)
        result_before = client.get(f"/api/v1/assignments/{assignment_id}/result", headers=student_headers)
        assert result_before.status_code == status.HTTP_200_OK
        res_data = result_before.json()
        assert res_data["assignment_id"] == assignment_id
        assert res_data["title"] == "Bai tap Vat Ly 1"
        assert res_data["attempts"] == []
        assert res_data["best_attempt"] is None

        # Start and submit an attempt
        start_att = client.post(f"/api/v1/assignments/{assignment_id}/attempts", headers=student_headers)
        assert start_att.status_code == status.HTTP_201_CREATED
        att_id = start_att.json()["attempt_id"]

        submit_resp = client.put(f"/api/v1/attempts/{att_id}/submit", json={"answers": []}, headers=student_headers)
        assert submit_resp.status_code == status.HTTP_200_OK

        # Call /result again
        result_after = client.get(f"/api/v1/assignments/{assignment_id}/result", headers=student_headers)
        assert result_after.status_code == status.HTTP_200_OK
        res_after_data = result_after.json()
        assert len(res_after_data["attempts"]) == 1
        assert res_after_data["best_attempt"] is not None
        assert res_after_data["attempts"][0]["badge_label"] == "Lần 1 (Mới nhất)"
        assert "cognitive" in res_after_data["attempts"][0]
        assert "recognition" in res_after_data["attempts"][0]["cognitive"]

        # Call /attempts route
        attempts_history = client.get(f"/api/v1/assignments/{assignment_id}/attempts", headers=student_headers)
        assert attempts_history.status_code == status.HTTP_200_OK
        assert attempts_history.json()["assignment_id"] == assignment_id

