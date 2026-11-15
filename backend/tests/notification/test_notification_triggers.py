# File Name: test_notification_triggers.py
# Description: Tests that business events create notifications for the right recipients, atomically.
# Created At: 2026-11-15
# Created By: AI Agent
# Updated At: 2026-11-15
# Updated By: AI Agent

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import status
from sqlalchemy import func

from app.core.rate_limit import reset_login_failures
from app.core.security import get_password_hash
from app.modules.notification import service
from models.models import Notification, Role, User

ADMIN, TEACHER, STUDENT = "0987654321", "0912345678", "0934567890"


def _h(client, phone):
    reset_login_failures(phone)
    r = client.post("/api/v1/auth/login", json={"phone": phone, "password": "password123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _uid(db, phone):
    return db.query(User).filter(User.phone == phone).one().user_id


def _types(db, phone):
    rows = db.query(Notification.type).filter(
        Notification.user_id == _uid(db, phone), Notification.status == "ACTIVE"
    ).all()
    return [r[0] for r in rows]


def _setup(client, db):
    """Class with the teacher assigned and the student enrolled; returns ids and headers."""
    a, t, s = _h(client, ADMIN), _h(client, TEACHER), _h(client, STUDENT)
    subj = client.post("/api/v1/subjects", json={"subject_name": f"Mon {uuid.uuid4().hex[:6]}"}, headers=a).json()["subject_id"]
    cls = client.post("/api/v1/classes", json={"class_name": f"L{uuid.uuid4().hex[:6]}", "school_year": "2025-2026"}, headers=a)
    assert cls.status_code == 201
    cid = cls.json()["class_id"]
    r = client.post(f"/api/v1/classes/{cid}/teacher-subjects",
                    json={"teacher_id": str(_uid(db, TEACHER)), "subject_id": subj}, headers=a)
    assert r.status_code == 201
    r = client.post(f"/api/v1/classes/{cid}/students",
                    json={"student_id": str(_uid(db, STUDENT)), "student_code": f"S{uuid.uuid4().hex[:6]}"}, headers=a)
    assert r.status_code == 201
    return {"a": a, "t": t, "s": s, "class_id": cid, "subject_id": subj}


def _assign(client, ctx):
    ex = client.post("/api/v1/exercises", json={"title": "BT thu", "subject_id": ctx["subject_id"]}, headers=ctx["t"]).json()["exercise_id"]
    due = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    r = client.post(f"/api/v1/classes/{ctx['class_id']}/assignments", json={"exercise_id": ex, "due_at": due}, headers=ctx["t"])
    assert r.status_code == 201, r.text
    return r.json()["assignment_id"]


def test_teacher_assigned_and_student_enrolled(client, db_session):
    _setup(client, db_session)
    assert "TEACHING_ASSIGNED" in _types(db_session, TEACHER)
    assert "ENROLLED" in _types(db_session, STUDENT)


def test_duplicate_enrollment_creates_no_extra_notification(client, db_session):
    ctx = _setup(client, db_session)
    before = _types(db_session, STUDENT).count("ENROLLED")
    r = client.post(f"/api/v1/classes/{ctx['class_id']}/students",
                    json={"student_id": str(_uid(db_session, STUDENT)), "student_code": "DUP1"}, headers=ctx["a"])
    assert r.status_code == 409
    assert _types(db_session, STUDENT).count("ENROLLED") == before


def test_assignment_notifies_students_and_release_once(client, db_session):
    ctx = _setup(client, db_session)
    aid = _assign(client, ctx)
    assert "ASSIGNMENT_CREATED" in _types(db_session, STUDENT)
    # The teacher who created it is not notified of their own action.
    assert "ASSIGNMENT_CREATED" not in _types(db_session, TEACHER)
    for _ in range(2):
        r = client.put(f"/api/v1/assignments/{aid}/answer-release", json={"released": True}, headers=ctx["t"])
        assert r.status_code == 200
    assert _types(db_session, STUDENT).count("ANSWERS_RELEASED") == 1


def test_duplicate_assignment_leaves_no_notification(client, db_session):
    ctx = _setup(client, db_session)
    _assign(client, ctx)
    count = _types(db_session, STUDENT).count("ASSIGNMENT_CREATED")
    ex = client.get("/api/v1/exercises", headers=ctx["t"]).json()
    ex_id = (ex["items"] if isinstance(ex, dict) else ex)[0]["exercise_id"]
    due = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    r = client.post(f"/api/v1/classes/{ctx['class_id']}/assignments", json={"exercise_id": ex_id, "due_at": due}, headers=ctx["t"])
    assert r.status_code == 409
    assert _types(db_session, STUDENT).count("ASSIGNMENT_CREATED") == count


def test_grade_notifies_student(client, db_session):
    ctx = _setup(client, db_session)
    aid = _assign(client, ctx)
    att = client.post(f"/api/v1/assignments/{aid}/attempts", headers=ctx["s"]).json()["attempt_id"]
    r = client.put(f"/api/v1/attempts/{att}/submit", json={"answers": []}, headers=ctx["s"])
    assert r.status_code == 200, r.text
    assert "ATTEMPT_GRADED" not in _types(db_session, STUDENT)
    r = client.put(f"/api/v1/attempts/{att}/grade", json={"score": 7.0}, headers=ctx["t"])
    assert r.status_code == 200, r.text
    assert "ATTEMPT_GRADED" in _types(db_session, STUDENT)


def test_homeroom_and_subject_head(client, db_session):
    ctx = _setup(client, db_session)
    tid = str(_uid(db_session, TEACHER))
    r = client.post("/api/v1/classes", json={"class_name": f"H{uuid.uuid4().hex[:6]}", "school_year": "2025-2026",
                                              "homeroom_teacher_id": tid}, headers=ctx["a"])
    assert r.status_code == 201, r.text
    assert _types(db_session, TEACHER).count("HOMEROOM_ASSIGNED") == 1
    # Updating the class without changing the homeroom teacher must not notify again.
    cid = r.json()["class_id"]
    r = client.put(f"/api/v1/classes/{cid}", json={"homeroom_teacher_id": tid, "school_year": "2025-2026"}, headers=ctx["a"])
    assert r.status_code == 200, r.text
    assert _types(db_session, TEACHER).count("HOMEROOM_ASSIGNED") == 1
    r = client.put(f"/api/v1/subjects/{ctx['subject_id']}/head-teacher", json={"teacher_id": tid}, headers=ctx["a"])
    assert r.status_code == 200, r.text
    assert "SUBJECT_HEAD_ASSIGNED" in _types(db_session, TEACHER)


def test_account_suspend_notifies_other_admins_only(client, db_session):
    admin_role = db_session.query(Role).filter(func.lower(Role.name) == "admin").one()
    other = User(user_id=uuid.uuid4(), phone="0900000011", full_name="Second Admin",
                 password_hash=get_password_hash("password123"), role_id=admin_role.role_id, status="ACTIVE")
    db_session.add(other)
    db_session.commit()
    a = _h(client, ADMIN)
    r = client.patch(f"/api/v1/admin/users/{_uid(db_session, STUDENT)}/status",
                     json={"status": "SUSPENDED", "reason": "test"}, headers=a)
    assert r.status_code == 200, r.text
    assert "ACCOUNT_STATUS_CHANGED" in _types(db_session, "0900000011")
    assert "ACCOUNT_STATUS_CHANGED" not in _types(db_session, ADMIN)


def test_notify_failure_does_not_break_caller(db_session, monkeypatch):
    uid = _uid(db_session, ADMIN)

    def boom(*a, **k):
        raise RuntimeError("insert failed")

    monkeypatch.setattr(db_session, "begin_nested", boom)
    assert service.notify(db_session, [uid], "T", "x") == 0
    # The session is still usable for the business data.
    assert db_session.query(User).count() > 0
