# File Name: test_exercises.py
# Description: Integration & Unit tests for F-EXE-01 Exercise Bank module (CRUD, scoping, soft-delete, restore, validation).
# Created At: 2026-07-31
# Created By: Tam Khang
# Updated At: 2026-07-31
# Updated By: Tam Khang

import uuid
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


class TestExerciseBankModule:
    def test_full_exercise_lifecycle(self, client: TestClient):
        # 1. Login Admin
        admin_token = get_admin_token(client)
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 2. Create Subject
        sub_resp = client.post(
            "/api/v1/subjects",
            json={"subject_name": f"Toan {uuid.uuid4().hex[:6]}", "description": "Mon Toan test"},
            headers=admin_headers
        )
        assert sub_resp.status_code == status.HTTP_201_CREATED
        subject_id = sub_resp.json()["subject_id"]

        # 3. Create Exercise as Admin
        ex_resp = client.post(
            "/api/v1/exercises",
            json={"title": "  De thi giua ky Toan 10  ", "subject_id": subject_id},
            headers=admin_headers
        )
        assert ex_resp.status_code == status.HTTP_201_CREATED
        exercise_data = ex_resp.json()
        assert exercise_data["title"] == "De thi giua ky Toan 10"
        assert exercise_data["status"] == "ACTIVE"
        exercise_id = exercise_data["exercise_id"]

        # 4. Add MultipleChoice Question (Invalid: 0 correct options -> 422)
        q_inv1 = client.post(
            f"/api/v1/exercises/{exercise_id}/questions",
            json={
                "content": "1 + 1 = ?",
                "question_type": "MultipleChoice",
                "answer_options": [
                    {"content": "1", "is_correct": False},
                    {"content": "2", "is_correct": False}
                ]
            },
            headers=admin_headers
        )
        assert q_inv1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # 5. Add MultipleChoice Question (Valid: exactly 1 correct option -> 201)
        q_valid = client.post(
            f"/api/v1/exercises/{exercise_id}/questions",
            json={
                "content": "1 + 1 bằng mấy?",
                "question_type": "MultipleChoice",
                "difficulty": "NhanBiet",
                "explanation": "1 + 1 = 2 theo phép cộng cơ bản",
                "answer_options": [
                    {"content": "1", "is_correct": False},
                    {"content": "2", "is_correct": True},
                    {"content": "3", "is_correct": False},
                    {"content": "4", "is_correct": False}
                ]
            },
            headers=admin_headers
        )
        assert q_valid.status_code == status.HTTP_201_CREATED
        question_id = q_valid.json()["question_id"]
        assert q_valid.json()["content"] == "1 + 1 bằng mấy?"

        # 6. Detail Exercise includes total_questions = 1 and question
        detail_resp = client.get(f"/api/v1/exercises/{exercise_id}", headers=admin_headers)
        assert detail_resp.status_code == status.HTTP_200_OK
        assert detail_resp.json()["total_questions"] == 1
        assert len(detail_resp.json()["questions"]) == 1

        # 7. Update Question
        q_update = client.put(
            f"/api/v1/questions/{question_id}",
            json={
                "content": "1 + 1 bằng mấy? (Đã sửa)",
                "difficulty": "ThongHieu"
            },
            headers=admin_headers
        )
        assert q_update.status_code == status.HTTP_200_OK
        assert q_update.json()["content"] == "1 + 1 bằng mấy? (Đã sửa)"

        # 8. Soft Delete Question
        q_del = client.delete(f"/api/v1/questions/{question_id}", headers=admin_headers)
        assert q_del.status_code == status.HTTP_204_NO_CONTENT

        # 9. Total questions in Exercise updated to 0
        detail_after_q_del = client.get(f"/api/v1/exercises/{exercise_id}", headers=admin_headers)
        assert detail_after_q_del.status_code == status.HTTP_200_OK
        assert detail_after_q_del.json()["total_questions"] == 0

        # 10. Soft Delete Exercise
        ex_del = client.delete(f"/api/v1/exercises/{exercise_id}", headers=admin_headers)
        assert ex_del.status_code == status.HTTP_204_NO_CONTENT

        # 11. GET exercise detail after soft delete returns 404
        ex_get_del = client.get(f"/api/v1/exercises/{exercise_id}", headers=admin_headers)
        assert ex_get_del.status_code == status.HTTP_404_NOT_FOUND

        # 12. Restore Exercise
        ex_restore = client.post(f"/api/v1/exercises/{exercise_id}/restore", headers=admin_headers)
        assert ex_restore.status_code == status.HTTP_200_OK
        assert ex_restore.json()["status"] == "ACTIVE"

        # 13. GET exercise detail after restore returns 200 OK
        ex_get_res = client.get(f"/api/v1/exercises/{exercise_id}", headers=admin_headers)
        assert ex_get_res.status_code == status.HTTP_200_OK

    def test_teacher_scoping(self, client: TestClient):
        # 1. Login Admin and Teacher
        admin_token = get_admin_token(client)
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        teacher_token = get_teacher_token(client)
        teacher_headers = {"Authorization": f"Bearer {teacher_token}"}

        # Create Subject A
        s_resp = client.post(
            "/api/v1/subjects",
            json={"subject_name": f"Hoa Hoc {uuid.uuid4().hex[:6]}"},
            headers=admin_headers
        )
        subject_id = s_resp.json()["subject_id"]

        # 2. Teacher creates exercise for unassigned subject -> 403 ERR-EXE-INVALID_SUBJECT_SCOPE
        fail_ex = client.post(
            "/api/v1/exercises",
            json={"title": "De Hoa Hoc Unassigned", "subject_id": subject_id},
            headers=teacher_headers
        )
        assert fail_ex.status_code == status.HTTP_403_FORBIDDEN
        assert fail_ex.json()["detail"]["code"] == "ERR-EXE-INVALID_SUBJECT_SCOPE"
