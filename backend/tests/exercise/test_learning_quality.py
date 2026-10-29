# File Name: test_learning_quality.py
# Description: Integration and unit tests for Homeroom Teacher Learning Quality radar analytics and grade-level comparison remarks.
# Created At: 2026-10-29
# Created By: Tam Khang
# Updated At: 2026-10-29
# Updated By: Tam Khang

import uuid
from datetime import datetime, timezone, timedelta
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.models import (
    User, Role, Class, Subject, TeacherSubject,
    Exercise, ClassAssignment, StudentExerciseAttempt, StudentClass
)
from app.modules.exercise.services.learning_quality_service import LearningQualityService


def test_learning_quality_service_calculation(db_session: Session):
    """
    Test LearningQualityService logic for computing class averages, grade averages,
    and generating comparative remarks comparing the homeroom class with the entire grade.
    """
    # 1. Setup roles and teacher
    teacher_role = db_session.query(Role).filter(Role.name == "Teacher").first()
    teacher = User(
        user_id=uuid.uuid4(),
        phone="0999888777",
        email="gvcn_test@school.com",
        password_hash="dummy_hashed_password",
        full_name="Thầy Test Chủ Nhiệm",
        role_id=teacher_role.role_id,
        status="ACTIVE"
    )
    db_session.add(teacher)
    db_session.flush()

    # 2. Setup classes: 12A1 (homeroom) and 12A2 (same grade 12)
    class_12a1 = Class(
        class_id=uuid.uuid4(),
        class_name="12A1",
        homeroom_teacher_id=teacher.user_id,
        academic_year="2026-2027",
        status="ACTIVE"
    )
    class_12a2 = Class(
        class_id=uuid.uuid4(),
        class_name="12A2",
        homeroom_teacher_id=None,
        academic_year="2026-2027",
        status="ACTIVE"
    )
    db_session.add_all([class_12a1, class_12a2])
    db_session.flush()

    # 3. Setup subject (Toán học) and exercise
    subject_math = db_session.query(Subject).filter(Subject.subject_name.ilike("%toán%")).first()
    if not subject_math:
        subject_math = Subject(
            subject_id=uuid.uuid4(),
            subject_name="Toán học",
            status="ACTIVE"
        )
        db_session.add(subject_math)
        db_session.flush()

    exercise_math = Exercise(
        exercise_id=uuid.uuid4(),
        title="Đề thi thử Toán học Khối 12",
        subject_id=subject_math.subject_id,
        created_by=teacher.user_id,
        status="ACTIVE"
    )
    db_session.add(exercise_math)
    db_session.flush()

    # 4. Assignments for both classes
    now = datetime.now(timezone.utc)
    assign_12a1 = ClassAssignment(
        assignment_id=uuid.uuid4(),
        class_id=class_12a1.class_id,
        exercise_id=exercise_math.exercise_id,
        assigned_by=teacher.user_id,
        assigned_at=now,
        due_at=now + timedelta(days=7),
        status="ACTIVE"
    )
    assign_12a2 = ClassAssignment(
        assignment_id=uuid.uuid4(),
        class_id=class_12a2.class_id,
        exercise_id=exercise_math.exercise_id,
        assigned_by=teacher.user_id,
        assigned_at=now,
        due_at=now + timedelta(days=7),
        status="ACTIVE"
    )
    db_session.add_all([assign_12a1, assign_12a2])
    db_session.flush()

    # 5. Attempts: 12A1 scores 9.0 and 8.0 (avg 8.5)
    #             12A2 scores 6.0 and 7.0 (avg 6.5)
    # Overall grade 12 math avg = (9.0 + 8.0 + 6.0 + 7.0) / 4 = 7.5
    student_role = db_session.query(Role).filter(Role.name == "Student").first()
    s1 = User(user_id=uuid.uuid4(), phone="0999000101", password_hash="dummy_hashed_password", full_name="Học sinh 1", role_id=student_role.role_id, status="ACTIVE")
    s2 = User(user_id=uuid.uuid4(), phone="0999000102", password_hash="dummy_hashed_password", full_name="Học sinh 2", role_id=student_role.role_id, status="ACTIVE")
    s3 = User(user_id=uuid.uuid4(), phone="0999000103", password_hash="dummy_hashed_password", full_name="Học sinh 3", role_id=student_role.role_id, status="ACTIVE")
    s4 = User(user_id=uuid.uuid4(), phone="0999000104", password_hash="dummy_hashed_password", full_name="Học sinh 4", role_id=student_role.role_id, status="ACTIVE")
    db_session.add_all([s1, s2, s3, s4])
    db_session.flush()

    att_1 = StudentExerciseAttempt(
        attempt_id=uuid.uuid4(), student_id=s1.user_id, assignment_id=assign_12a1.assignment_id,
        score=9.0, is_finished=True, status="approved"
    )
    att_2 = StudentExerciseAttempt(
        attempt_id=uuid.uuid4(), student_id=s2.user_id, assignment_id=assign_12a1.assignment_id,
        score=8.0, is_finished=True, status="approved"
    )
    att_3 = StudentExerciseAttempt(
        attempt_id=uuid.uuid4(), student_id=s3.user_id, assignment_id=assign_12a2.assignment_id,
        score=6.0, is_finished=True, status="approved"
    )
    att_4 = StudentExerciseAttempt(
        attempt_id=uuid.uuid4(), student_id=s4.user_id, assignment_id=assign_12a2.assignment_id,
        score=7.0, is_finished=True, status="approved"
    )
    db_session.add_all([att_1, att_2, att_3, att_4])
    db_session.commit()

    # 6. Execute service
    service = LearningQualityService(db_session)
    res = service.get_homeroom_learning_quality(teacher)

    assert "Lớp 12A1" in res["class_name"]
    assert res["grade_name"] == "Khối 12"
    assert len(res["radar_data"]) == 6
    assert len(res["feedback_notes"]) >= 3

    # Check that Math score in radar_data matches computed average
    math_radar = next((item for item in res["radar_data"] if item["subject_name"] == "Toán Học"), None)
    assert math_radar is not None
    assert math_radar["class_score"] == 8.5
    assert math_radar["grade_score"] == 7.5

    # Check feedback notes contain grade comparison
    notes_combined = " ".join(res["feedback_notes"])
    assert "Khối 12" in notes_combined
    assert "Lớp 12A1" in notes_combined


def test_teacher_dashboard_and_learning_quality_endpoints(client: TestClient, db_session: Session):
    """
    Test GET /api/v1/teacher/dashboard and GET /api/v1/teacher/learning-quality API endpoints.
    """
    # 1. Login with admin/teacher token
    login_res = client.post("/api/v1/auth/login", json={"phone": "0987654321", "password": "password123"})
    assert login_res.status_code == status.HTTP_200_OK
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test GET /api/v1/teacher/dashboard
    dash_res = client.get("/api/v1/teacher/dashboard", headers=headers)
    assert dash_res.status_code == status.HTTP_200_OK
    dash_data = dash_res.json()

    assert "metrics" in dash_data
    assert "learning_quality" in dash_data
    lq = dash_data["learning_quality"]
    assert "class_name" in lq
    assert "radar_data" in lq
    assert "feedback_notes" in lq
    assert len(lq["radar_data"]) > 0
    assert len(lq["feedback_notes"]) > 0

    # 3. Test GET /api/v1/teacher/learning-quality
    lq_res = client.get("/api/v1/teacher/learning-quality", headers=headers)
    assert lq_res.status_code == status.HTTP_200_OK
    lq_data = lq_res.json()

    assert "class_name" in lq_data
    assert "radar_data" in lq_data
    assert "feedback_notes" in lq_data
    for item in lq_data["radar_data"]:
        assert "subject_name" in item
        assert "class_score" in item
        assert "grade_score" in item
        assert item["class_score"] >= 0
        assert item["grade_score"] >= 0
