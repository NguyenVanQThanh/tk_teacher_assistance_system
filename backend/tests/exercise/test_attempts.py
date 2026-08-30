# File Name: test_attempts.py
# Description: Unit & Integration tests for F-EXE-03 Student Submission & F-EXE-04 Auto Grading module.
# Created At: 2026-08-05
# Created By: Tam Khang
# Updated At: 2026-08-05
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



class TestStudentSubmissionModule:
    def test_full_attempt_lifecycle_and_grading(self, client: TestClient):
        admin_token = get_admin_token(client)
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        teacher_token = get_teacher_token(client)
        teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
        student_token = get_student_token(client)
        student_headers = {"Authorization": f"Bearer {student_token}"}

        # 1. Setup Subject, Class, Teacher Assignment, Student Enrollment
        subject_resp = client.post(
            "/api/v1/subjects",
            json={"subject_name": f"Sinh Hoc {uuid.uuid4().hex[:6]}"},
            headers=admin_headers
        )
        assert subject_resp.status_code == status.HTTP_201_CREATED
        subject_id = subject_resp.json()["subject_id"]

        class_resp = client.post(
            "/api/v1/classes",
            json={"class_name": f"Lop 12C{uuid.uuid4().hex[:4]}", "school_year": "2025-2026"},
            headers=admin_headers
        )
        assert class_resp.status_code == status.HTTP_201_CREATED
        class_id = class_resp.json()["class_id"]

        teacher_id = client.get("/api/v1/auth/me", headers=teacher_headers).json()["user_id"]
        student_id = client.get("/api/v1/auth/me", headers=student_headers).json()["user_id"]

        # Assign Teacher to Class
        client.post(
            f"/api/v1/classes/{class_id}/teacher-subjects",
            json={"teacher_id": teacher_id, "subject_id": subject_id},
            headers=admin_headers
        )

        # Enroll Student in Class
        enroll_resp = client.post(
            f"/api/v1/classes/{class_id}/students",
            json={"student_id": student_id, "student_code": f"STU_{uuid.uuid4().hex[:4]}"},
            headers=admin_headers
        )
        assert enroll_resp.status_code == status.HTTP_201_CREATED


        # 2. Teacher creates Exercise with 2 MultipleChoice questions and 1 ShortAnswer question
        exercise_resp = client.post(
            "/api/v1/exercises",
            json={"title": f"Bai Kiem Tra Sinh {uuid.uuid4().hex[:4]}", "subject_id": subject_id},
            headers=teacher_headers
        )
        assert exercise_resp.status_code == status.HTTP_201_CREATED
        exercise_id = exercise_resp.json()["exercise_id"]

        # Add MC Question 1
        q1_resp = client.post(
            f"/api/v1/exercises/{exercise_id}/questions",
            json={
                "content": "Te bao la gi?",
                "question_type": "MultipleChoice",
                "display_order": 1,
                "answer_options": [
                    {"content": "Don vi cau tao co ban cua su song", "is_correct": True, "display_order": 1},
                    {"content": "Mot phan tu hoa hoc", "is_correct": False, "display_order": 2}
                ]
            },
            headers=teacher_headers
        )
        assert q1_resp.status_code == status.HTTP_201_CREATED
        q1 = q1_resp.json()
        q1_id = q1["question_id"]
        q1_correct_opt_id = next(opt["option_id"] for opt in q1["answer_options"] if opt["is_correct"])

        # Add MC Question 2
        q2_resp = client.post(
            f"/api/v1/exercises/{exercise_id}/questions",
            json={
                "content": "DNA co cau truc gi?",
                "question_type": "MultipleChoice",
                "display_order": 2,
                "answer_options": [
                    {"content": "Xoan kep", "is_correct": True, "display_order": 1},
                    {"content": "Xoan don", "is_correct": False, "display_order": 2}
                ]
            },
            headers=teacher_headers
        )
        assert q2_resp.status_code == status.HTTP_201_CREATED
        q2 = q2_resp.json()
        q2_id = q2["question_id"]
        q2_wrong_opt_id = next(opt["option_id"] for opt in q2["answer_options"] if not opt["is_correct"])

        # Add ShortAnswer Question 3
        q3_resp = client.post(
            f"/api/v1/exercises/{exercise_id}/questions",
            json={
                "content": "Mo ta qua trinh quang hop.",
                "question_type": "ShortAnswer",
                "correct_answer": "Quang hop la...",
                "display_order": 3
            },
            headers=teacher_headers
        )
        assert q3_resp.status_code == status.HTTP_201_CREATED
        q3_id = q3_resp.json()["question_id"]

        # 3. Teacher assigns exercise to Class
        due_time = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        assignment_resp = client.post(
            f"/api/v1/classes/{class_id}/assignments",
            json={"exercise_id": exercise_id, "due_at": due_time},
            headers=teacher_headers
        )
        assert assignment_resp.status_code == status.HTTP_201_CREATED
        assignment_id = assignment_resp.json()["assignment_id"]

        # 4. Student starts attempt
        start_resp = client.post(
            f"/api/v1/assignments/{assignment_id}/attempts",
            headers=student_headers
        )
        assert start_resp.status_code == status.HTTP_201_CREATED, f"Start attempt failed: {start_resp.json()}"

        attempt_start = start_resp.json()
        attempt_id = attempt_start["attempt_id"]
        assert attempt_start["is_finished"] is False

        # Try starting a second attempt while open -> 409 Conflict
        start_again_resp = client.post(
            f"/api/v1/assignments/{assignment_id}/attempts",
            headers=student_headers
        )
        assert start_again_resp.status_code == status.HTTP_409_CONFLICT

        # 5. Student submits attempt (Q1 correct, Q2 wrong, Q3 text answer)
        submit_payload = {
            "answers": [
                {"question_id": q1_id, "answer_option_id": q1_correct_opt_id},
                {"question_id": q2_id, "answer_option_id": q2_wrong_opt_id},
                {"question_id": q3_id, "answer_text": "Quang hop su dung anh sang mat troi..."}
            ]
        }
        submit_resp = client.put(
            f"/api/v1/attempts/{attempt_id}/submit",
            json=submit_payload,
            headers=student_headers
        )
        assert submit_resp.status_code == status.HTTP_200_OK
        attempt_result = submit_resp.json()

        assert attempt_result["is_finished"] is True
        # Score calculation: 2 MC questions = 5.0 points per question. 1 correct -> 5.0 score.
        assert attempt_result["score"] == 5.0
        assert attempt_result["total_time_seconds"] is not None

        detailed = attempt_result["detailed_results"]["questions"]
        assert len(detailed) == 3

        q1_res = next(r for r in detailed if r["question_id"] == q1_id)
        assert q1_res["is_correct"] is True

        q2_res = next(r for r in detailed if r["question_id"] == q2_id)
        assert q2_res["is_correct"] is False

        q3_res = next(r for r in detailed if r["question_id"] == q3_id)
        assert q3_res["pending_manual_grade"] is True

        # Try submitting again -> 409 Conflict
        resubmit_resp = client.put(
            f"/api/v1/attempts/{attempt_id}/submit",
            json=submit_payload,
            headers=student_headers
        )
        assert resubmit_resp.status_code == status.HTTP_409_CONFLICT

        # 6. View attempt results
        # Student owner can view
        get_student_resp = client.get(
            f"/api/v1/attempts/{attempt_id}",
            headers=student_headers
        )
        assert get_student_resp.status_code == status.HTTP_200_OK

        # Teacher teaching the class can view
        get_teacher_resp = client.get(
            f"/api/v1/attempts/{attempt_id}",
            headers=teacher_headers
        )
        assert get_teacher_resp.status_code == status.HTTP_200_OK

        # Admin can view
        get_admin_resp = client.get(
            f"/api/v1/attempts/{attempt_id}",
            headers=admin_headers
        )
        assert get_admin_resp.status_code == status.HTTP_200_OK
