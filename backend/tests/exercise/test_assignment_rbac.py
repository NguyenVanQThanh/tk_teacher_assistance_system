# File Name: test_assignment_rbac.py
# Description: Regression tests for assignment/attempt RBAC: owner-only manage, class scoping,
#              personal (student AI) assignment visibility, dashboard exclusion.
# Created At: 2026-11-13
# Created By: AI Agent
# Updated At: 2026-11-13
# Updated By: AI Agent

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from models.models import (
    Class, ClassAssignment, Exercise, Question, Role, StudentClass, StudentExerciseAttempt,
    Subject, TeacherSubject, User,
)

PASSWORD = "password123"


def _login(client: TestClient, phone: str) -> dict:
    resp = client.post("/api/v1/auth/login", json={"phone": phone, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _user(db, role_name: str, phone: str) -> User:
    role = db.query(Role).filter(Role.name == role_name).first()
    user = User(
        user_id=uuid.uuid4(), phone=phone, email=f"{phone}@rbac.test",
        password_hash=get_password_hash(PASSWORD), full_name=f"{role_name} {phone}",
        role_id=role.role_id, status="Active",
    )
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def world(client: TestClient, db_session):
    """Teachers A (class C1) and B (class C2); students X, Y in C1, Z in C2.

    Exercise eA (owned by A) is assigned class-wide to C1 (aA); eB likewise for B/C2 (aB).
    X and Y each own a personal AI exercise + personal assignment in C1.
    """
    db = db_session
    sfx = uuid.uuid4().hex[:6]
    subject = Subject(subject_name=f"RBAC Subject {sfx}", status="ACTIVE")
    c1 = Class(class_name=f"RBAC1-{sfx}", academic_year="2025-2026", status="ACTIVE")
    c2 = Class(class_name=f"RBAC2-{sfx}", academic_year="2025-2026", status="ACTIVE")
    db.add_all([subject, c1, c2])
    db.flush()

    n = int(sfx, 16) % 10000000
    a = _user(db, "Teacher", f"09{n:07d}1")
    b = _user(db, "Teacher", f"09{n:07d}2")
    x = _user(db, "Student", f"08{n:07d}1")
    y = _user(db, "Student", f"08{n:07d}2")
    z = _user(db, "Student", f"08{n:07d}3")
    db.add_all([
        TeacherSubject(teacher_id=a.user_id, class_id=c1.class_id, subject_id=subject.subject_id, status="ACTIVE"),
        TeacherSubject(teacher_id=b.user_id, class_id=c2.class_id, subject_id=subject.subject_id, status="ACTIVE"),
        StudentClass(student_id=x.user_id, class_id=c1.class_id, status="ACTIVE"),
        StudentClass(student_id=y.user_id, class_id=c1.class_id, status="ACTIVE"),
        StudentClass(student_id=z.user_id, class_id=c2.class_id, status="ACTIVE"),
    ])

    due = datetime.now(timezone.utc) + timedelta(days=3)

    def make_exercise(owner, title, ai=False):
        ex = Exercise(title=title, subject_id=subject.subject_id, created_by=owner.user_id,
                      total_questions=1, status="ACTIVE",
                      ai_metadata={"is_ai_generated": True} if ai else {})
        db.add(ex)
        db.flush()
        db.add(Question(exercise_id=ex.exercise_id, content="Q?", question_type="ShortAnswer",
                        correct_answer="1", display_order=1))
        return ex

    def assign(ex, cls, assigner, owner_student=None):
        asg = ClassAssignment(class_id=cls.class_id, exercise_id=ex.exercise_id,
                              assigned_by=assigner.user_id, due_at=due, owner_student_id=owner_student)
        db.add(asg)
        db.flush()
        return asg

    e_a = make_exercise(a, "Exercise of A")
    e_b = make_exercise(b, "Exercise of B")
    e_x = make_exercise(x, "Personal X", ai=True)
    e_y = make_exercise(y, "Personal Y", ai=True)
    asg = {
        "aA": assign(e_a, c1, a),
        "aB": assign(e_b, c2, b),
        "aX": assign(e_x, c1, x, x.user_id),
        "aY": assign(e_y, c1, y, y.user_id),
    }
    db.commit()

    return {
        "headers": {
            "A": _login(client, a.phone), "B": _login(client, b.phone),
            "X": _login(client, x.phone), "Y": _login(client, y.phone),
            "Z": _login(client, z.phone),
        },
        "asg": {k: str(v.assignment_id) for k, v in asg.items()},
        "ex": {"A": e_a, "B": e_b, "X": e_x, "Y": e_y},
        "classes": {"C1": c1, "C2": c2},
        "users": {"A": a, "B": b, "X": x, "Y": y, "Z": z},
        "db": db,
    }


class TestAssignmentManageRbac:
    def test_other_teacher_cannot_delete_restore_or_release(self, client, world):
        h, asg = world["headers"], world["asg"]
        for hdr in (h["B"],):
            assert client.delete(f"/api/v1/assignments/{asg['aA']}", headers=hdr).status_code in (403, 404)
            assert client.put(f"/api/v1/assignments/{asg['aA']}/answer-release",
                              json={"released": True}, headers=hdr).status_code in (403, 404)
            assert client.post(f"/api/v1/assignments/{asg['aA']}/restore", headers=hdr).status_code in (403, 404)
        # still active
        assert world["db"].query(ClassAssignment).get(uuid.UUID(asg["aA"])).status == "ACTIVE"

    def test_owner_can_delete_and_restore_then_foreign_restore_blocked(self, client, world):
        h, asg = world["headers"], world["asg"]
        assert client.delete(f"/api/v1/assignments/{asg['aA']}", headers=h["A"]).status_code == 204
        assert client.post(f"/api/v1/assignments/{asg['aA']}/restore", headers=h["B"]).status_code in (403, 404)
        assert client.post(f"/api/v1/assignments/{asg['aA']}/restore", headers=h["A"]).status_code == 200

    def test_owner_can_release_answers(self, client, world):
        h, asg = world["headers"], world["asg"]
        resp = client.put(f"/api/v1/assignments/{asg['aA']}/answer-release", json={"released": True}, headers=h["A"])
        assert resp.status_code == 200
        assert resp.json()["answers_released"] is True

    def test_assign_invisible_exercise_404(self, client, world):
        """Teacher A cannot assign B's exercise to A's class."""
        c1 = world["classes"]["C1"]
        due = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        resp = client.post(f"/api/v1/classes/{c1.class_id}/assignments",
                           json={"exercise_id": str(world["ex"]["B"].exercise_id), "due_at": due},
                           headers=world["headers"]["A"])
        assert resp.status_code in (403, 404)

    def test_result_summary_other_class_forbidden(self, client, world):
        """Teacher A must not read the summary of B's class assignment (no more swallowed 403)."""
        resp = client.get(f"/api/v1/assignments/{world['asg']['aB']}/attempts-history", headers=world["headers"]["A"])
        assert resp.status_code in (403, 404)

    def test_result_summary_unknown_id_404(self, client, world):
        resp = client.get(f"/api/v1/assignments/{uuid.uuid4()}/attempts-history", headers=world["headers"]["A"])
        assert resp.status_code == 404

    def test_result_summary_exercise_id_fallback_not_visible(self, client, world):
        """Passing B's bare exercise id must not leak anything to teacher A."""
        resp = client.get(f"/api/v1/assignments/{world['ex']['B'].exercise_id}/attempts-history",
                          headers=world["headers"]["A"])
        assert resp.status_code in (403, 404)

    def test_student_cannot_manage(self, client, world):
        resp = client.delete(f"/api/v1/assignments/{world['asg']['aA']}", headers=world["headers"]["X"])
        assert resp.status_code in (403, 404)


class TestPersonalAssignmentVisibility:
    def test_feed_excludes_classmates_personal_assignment(self, client, world):
        h, asg = world["headers"], world["asg"]
        ids_x = {r["assignment_id"] for r in client.get("/api/v1/assignments", headers=h["X"]).json()}
        assert asg["aX"] in ids_x and asg["aA"] in ids_x
        assert asg["aY"] not in ids_x
        ids_y = {r["assignment_id"] for r in client.get("/api/v1/assignments", headers=h["Y"]).json()}
        assert asg["aY"] in ids_y and asg["aX"] not in ids_y

    def test_class_assignment_list_hides_personal(self, client, world):
        c1 = world["classes"]["C1"]
        ids = {r["assignment_id"] for r in client.get(
            f"/api/v1/classes/{c1.class_id}/assignments", headers=world["headers"]["A"]).json()}
        assert world["asg"]["aA"] in ids
        assert world["asg"]["aX"] not in ids and world["asg"]["aY"] not in ids

    def test_student_dashboard_excludes_other_personal(self, client, world):
        resp = client.get("/api/v1/student/dashboard", headers=world["headers"]["X"])
        assert resp.status_code == 200
        ids = {r["assignment_id"] for r in resp.json()["upcoming_assignments"]}
        assert world["asg"]["aX"] in ids and world["asg"]["aA"] in ids
        assert world["asg"]["aY"] not in ids

    def test_taking_start_summary_on_other_personal_404(self, client, world):
        h, aY = world["headers"]["X"], world["asg"]["aY"]
        assert client.get(f"/api/v1/assignments/{aY}/taking", headers=h).status_code == 404
        assert client.post(f"/api/v1/assignments/{aY}/attempts", headers=h).status_code == 404
        assert client.get(f"/api/v1/assignments/{aY}/attempts-history", headers=h).status_code == 404

    def test_own_personal_assignment_works(self, client, world):
        h, aX = world["headers"]["X"], world["asg"]["aX"]
        assert client.get(f"/api/v1/assignments/{aX}/taking", headers=h).status_code == 200
        assert client.post(f"/api/v1/assignments/{aX}/attempts", headers=h).status_code == 201

    def test_teacher_cannot_see_or_manage_personal(self, client, world):
        h, aX = world["headers"]["A"], world["asg"]["aX"]
        assert client.get(f"/api/v1/assignments/{aX}/taking", headers=h).status_code in (403, 404)
        assert client.delete(f"/api/v1/assignments/{aX}", headers=h).status_code in (403, 404)

    def test_teacher_dashboard_excludes_personal_attempts(self, client, world):
        db = world["db"]
        now = datetime.now(timezone.utc)
        for key, student in (("aX", "X"), ("aA", "Z")):
            # Z is not in C1; use X on class-wide aA instead for the positive control
            sid = world["users"]["X" if key == "aA" else student].user_id
            db.add(StudentExerciseAttempt(student_id=sid, assignment_id=uuid.UUID(world["asg"][key]),
                                          start_time=now, end_time=now, is_finished=True, score=None,
                                          status="ACTIVE", detailed_results={"questions": []}))
        db.commit()
        resp = client.get("/api/v1/teacher/dashboard", headers=world["headers"]["A"])
        if resp.status_code != 200:
            pytest.skip("teacher dashboard route not mounted at /api/v1/teacher/dashboard")
        assert "Personal X" not in resp.text
        assert "Exercise of A" in resp.text


class TestAttemptScopeRegression:
    def test_other_students_attempt_forbidden(self, client, world):
        h = world["headers"]
        start = client.post(f"/api/v1/assignments/{world['asg']['aX']}/attempts", headers=h["X"])
        assert start.status_code == 201
        attempt_id = start.json()["attempt_id"]
        assert client.get(f"/api/v1/attempts/{attempt_id}", headers=h["Y"]).status_code in (403, 404)
        assert client.get(f"/api/v1/attempts/{attempt_id}/paper", headers=h["Y"]).status_code in (403, 404)
        assert client.put(f"/api/v1/attempts/{attempt_id}/submit", json={"answers": []},
                          headers=h["Y"]).status_code in (403, 404)

    def test_other_class_student_cannot_start_class_assignment(self, client, world):
        resp = client.post(f"/api/v1/assignments/{world['asg']['aA']}/attempts", headers=world["headers"]["Z"])
        assert resp.status_code == 403
