# File Name: test_guest.py
# Description: Integration tests for guest access (POST /auth/guest), guest restrictions and guest AI/attempt flows.
# Created At: 2026-11-15
# Created By: AI Agent
# Updated At: 2026-11-15
# Updated By: AI Agent

import json
import uuid

import pytest

from app.core import config as app_config
from app.core.rate_limit import reset_login_failures
from app.modules.exercise.services.ai_generator_service import AiExerciseGeneratorService
from app.modules.exercise.services.rag_context_service import RagContextService
from app.modules.exercise.services.rag_retrieval_service import RagRetrievalService
from models.models import ClassAssignment, Subject, User

GUEST = "/api/v1/auth/guest"


@pytest.fixture(autouse=True)
def _relax_ip_limit(monkeypatch):
    monkeypatch.setattr(app_config, "GUEST_CREATE_PER_IP_HOUR", 100)
    reset_login_failures("0987654321")


def _guest(client, role="Student", key=None):
    body = {"role": role}
    if key:
        body["guest_key"] = key
    return client.post(GUEST, json=body)


def _h(resp):
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _admin(client):
    r = client.post("/api/v1/auth/login", json={"phone": "0987654321", "password": "password123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_create_then_resume_and_wrong_key(client, db_session):
    r = _guest(client)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["guest_key"] and body["user"]["is_guest"] is True and body["user"]["full_name"] == "Khách"
    user = db_session.query(User).filter(User.user_id == uuid.UUID(body["user"]["user_id"])).one()
    assert user.phone.startswith("guest_") and user.guest_key_hash != body["guest_key"]
    resumed = _guest(client, key=body["guest_key"])
    assert resumed.json()["guest_key"] is None
    assert resumed.json()["user"]["user_id"] == body["user"]["user_id"]
    other = _guest(client, key="wrong-key")
    assert other.json()["user"]["user_id"] != body["user"]["user_id"] and other.json()["guest_key"]
    # a Student guest key does not resume a Teacher guest
    assert _guest(client, "Teacher", key=body["guest_key"]).json()["user"]["user_id"] != body["user"]["user_id"]
    assert client.get("/api/v1/auth/me", headers=_h(r)).json()["is_guest"] is True


def test_ip_limit_admin_and_disabled(client, monkeypatch):
    monkeypatch.setattr(app_config, "GUEST_CREATE_PER_IP_HOUR", 1)
    assert _guest(client).status_code == 200
    limited = _guest(client)
    assert limited.status_code == 429 and limited.json()["detail"]["code"] == "ERR-AUTH-GUEST_RATE_LIMITED"
    assert client.post(GUEST, json={"role": "Admin"}).status_code in (403, 422)
    monkeypatch.setattr(app_config, "GUEST_ACCESS_ENABLED", False)
    d = _guest(client, "Teacher")
    assert d.status_code == 403 and d.json()["detail"]["code"] == "ERR-AUTH-GUEST_DISABLED"


def test_guest_forbidden_on_class_assignment_schedule(client):
    t = _h(_guest(client, "Teacher"))
    assert client.get("/api/v1/classes", headers=t).status_code == 403
    assert client.get("/api/v1/assignments", headers=t).status_code == 403
    assert client.get("/api/v1/teacher/schedule", headers=t).status_code == 403
    s = _h(_guest(client, "Student"))
    assert client.get("/api/v1/classes", headers=s).status_code == 403
    assert client.post("/api/v1/auth/change-password", headers=s,
                       json={"old_password": "x", "new_password": "longenough1"}).status_code == 403


def test_teacher_guest_creates_exercise_any_subject(client, db_session):
    subject = Subject(subject_name=f"Any {uuid.uuid4().hex[:6]}", status="ACTIVE")
    db_session.add(subject)
    db_session.flush()
    t = _h(_guest(client, "Teacher"))
    from app.modules.academic.services.subject_service import SubjectService
    guest = db_session.query(User).filter(User.is_guest.is_(True)).order_by(User.created_at.desc()).first()
    assert subject.subject_id in [x.subject_id for x in SubjectService.list_subjects(db_session, current_user=guest)]
    r = client.post("/api/v1/exercises", headers=t,
                    json={"title": "Guest ex", "subject_id": str(subject.subject_id)})
    assert r.status_code == 201, r.text


def _fake_questions(monkeypatch):
    def fake(cls, api_key, part, prompt, temperature):
        n = prompt.count("- Question ")
        if part == "Part1":
            return [{"content": f"M{i}", "answer_options": [
                {"content": c, "is_correct": c == "a"} for c in "abcd"]} for i in range(n)]
        if part == "Part2":
            return [{"content": f"T{i}", "segments": [
                {"key": k, "statement": f"s{k}", "is_correct": k in "ac"} for k in "abcd"]} for i in range(n)]
        return [{"content": f"S{i}", "correct_answer": "7"} for i in range(n)]
    monkeypatch.setattr(AiExerciseGeneratorService, "_call_gemini_part", classmethod(fake))
    monkeypatch.setattr("app.modules.exercise.services.ai_generator_service.GeminiVisionParserService.get_api_key",
                        lambda: "k")
    monkeypatch.setattr(RagRetrievalService, "resolve_sgk_filter", staticmethod(lambda *a: ["doc1"]))
    monkeypatch.setattr(RagRetrievalService, "list_chapters",
                        staticmethod(lambda db, ids: [{"chapter": "C1", "doc_id": "doc1", "page_start": 1}]))
    monkeypatch.setattr(RagContextService, "build_student_context", classmethod(lambda c, db, **kw: ("ctx", [])))


def test_student_guest_generate_and_attempt_without_class(client, db_session, monkeypatch):
    _fake_questions(monkeypatch)
    subject = Subject(subject_name=f"Hoa {uuid.uuid4().hex[:6]}", status="ACTIVE")
    db_session.add(subject)
    db_session.flush()
    s = _h(_guest(client, "Student"))
    ch = client.get(f"/api/v1/ai-exercises/chapters?subject_id={subject.subject_id}&grade=11", headers=s)
    assert ch.status_code == 200, ch.text
    payload = {"subject_id": str(subject.subject_id), "chapters": ["C1"], "grade": 11,
               "matrix": {"mcq": {"NhanBiet": 1, "ThongHieu": 0, "VanDung": 0},
                          "tf": {"NhanBiet": 0, "ThongHieu": 0, "VanDung": 0},
                          "short": {"NhanBiet": 0, "ThongHieu": 0, "VanDung": 0}}}
    r = client.post("/api/v1/ai-exercises/student", data={"payload": json.dumps(payload)}, headers=s)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["class_id"] is None and body["assignment_id"]
    a = db_session.query(ClassAssignment).filter(
        ClassAssignment.assignment_id == uuid.UUID(body["assignment_id"])).one()
    assert a.class_id is None and a.owner_student_id is not None
    feed = client.get("/api/v1/assignments", headers=s)
    assert feed.status_code == 200
    assert body["assignment_id"] in [str(x["assignment_id"]) for x in feed.json()]
    taking = client.get(f"/api/v1/assignments/{body['assignment_id']}/taking", headers=s)
    assert taking.status_code == 200, taking.text
    att = client.post(f"/api/v1/assignments/{body['assignment_id']}/attempts", headers=s)
    assert att.status_code in (200, 201), att.text
    aid = att.json()["attempt_id"]
    sub = client.put(f"/api/v1/attempts/{aid}/submit", headers=s, json={"answers": []})
    assert sub.status_code == 200, sub.text
    assert client.get(f"/api/v1/assignments/{body['assignment_id']}/attempts", headers=s).status_code == 200
    assert client.get("/api/v1/attempts", headers=s).status_code == 200
    assert client.get("/api/v1/student/dashboard", headers=s).status_code == 200


def test_guest_permissions_are_allow_list_only(client, db_session):
    from app.modules.auth.services.permission_service import PermissionService
    from app.scripts.rbac_seed import GUEST_ALLOWED_PERMISSIONS
    from models.models import Permission, RolePermission, User

    for role in ("Teacher", "Student"):
        body = _guest(client, role).json()
        user = db_session.query(User).filter(User.user_id == uuid.UUID(body["user"]["user_id"])).one()
        perms = PermissionService.get_effective_permissions(db_session, user.user_id, user.role_id)
        assert perms <= set(GUEST_ALLOWED_PERMISSIONS[role])

        # A permission added to the role later must not leak to existing guests.
        perm = Permission(permission_code=f"NEW_{uuid.uuid4().hex[:6].upper()}", name="New", description="x")
        db_session.add(perm)
        db_session.flush()
        db_session.add(RolePermission(role_id=user.role_id, permission_id=perm.permission_id))
        db_session.flush()
        PermissionService.invalidate_role_cache()
        assert perm.permission_code not in PermissionService.get_effective_permissions(
            db_session, user.user_id, user.role_id)


def test_student_guest_requires_grade(client, db_session, monkeypatch):
    _fake_questions(monkeypatch)
    subject = Subject(subject_name=f"Ly {uuid.uuid4().hex[:6]}", status="ACTIVE")
    db_session.add(subject)
    db_session.flush()
    s = _h(_guest(client, "Student"))
    r = client.get(f"/api/v1/ai-exercises/chapters?subject_id={subject.subject_id}", headers=s)
    assert r.status_code == 422 and "ERR-EXE-AI_GRADE_REQUIRED" in r.text
    payload = {"subject_id": str(subject.subject_id), "chapters": ["C1"],
               "matrix": {"mcq": {"NhanBiet": 1, "ThongHieu": 0, "VanDung": 0},
                          "tf": {"NhanBiet": 0, "ThongHieu": 0, "VanDung": 0},
                          "short": {"NhanBiet": 0, "ThongHieu": 0, "VanDung": 0}}}
    r = client.post("/api/v1/ai-exercises/student", data={"payload": json.dumps(payload)}, headers=s)
    assert r.status_code == 422 and "ERR-EXE-AI_GRADE_REQUIRED" in r.text


def test_teacher_guest_ai_generate_without_assignment(client, db_session, monkeypatch):
    _fake_questions(monkeypatch)
    monkeypatch.setattr(RagContextService, "build_context_with_sources",
                        classmethod(lambda c, db, **kw: ("", [])))
    subject = Subject(subject_name=f"Ly {uuid.uuid4().hex[:6]}", status="ACTIVE")
    db_session.add(subject)
    db_session.flush()
    t = _h(_guest(client, "Teacher"))
    r = client.post("/api/v1/exercises/ai-generate", headers=t, json={
        "subject_id": str(subject.subject_id), "topic_prompt": "x", "part1_count": 1,
        "part2_count": 0, "part3_count": 0})
    assert r.status_code == 201, r.text
    assert r.json()["assignment_id"] is None and r.json()["class_id"] is None

    monkeypatch.setattr(app_config, "GUEST_AI_LIMIT", 1)
    r = client.post("/api/v1/exercises/ai-generate", headers=t, json={
        "subject_id": str(subject.subject_id), "topic_prompt": "x", "part1_count": 1,
        "part2_count": 0, "part3_count": 0})
    assert r.status_code == 403 and "ERR-EXE-GUEST_AI_LIMIT" in r.text


def test_admin_list_stats_and_reset(client, db_session):
    admin = _admin(client)
    g = _guest(client, "Student")
    gid = g.json()["user"]["user_id"]
    before = client.get("/api/v1/admin/dashboard/stats", headers=admin).json()["total_students"]
    for _ in range(3):
        _guest(client, "Student")
    assert client.get("/api/v1/admin/dashboard/stats", headers=admin).json()["total_students"] == before
    lst = client.get("/api/v1/admin/users?is_guest=true&page_size=100", headers=admin).json()["items"]
    assert any(i["user_id"] == gid and i["is_guest"] and i["guest_ip"] for i in lst)
    assert all(i["is_guest"] for i in lst)
    r = client.post(f"/api/v1/admin/users/{gid}/reset-password", headers=admin)
    assert r.status_code == 403


def test_guest_phone_fits_column(client, db_session):
    """SQLite ignores VARCHAR length, so assert the generated phone fits users.phone explicitly."""
    uid = uuid.UUID(_guest(client, "Student").json()["user"]["user_id"])
    phone = db_session.query(User).filter(User.user_id == uid).one().phone
    assert len(phone) <= User.__table__.c.phone.type.length


def test_global_cap_and_xff_uses_last_entry(client, monkeypatch):
    monkeypatch.setattr(app_config, "GUEST_CREATE_GLOBAL_HOUR", 1)
    assert _guest(client).status_code == 200
    r = _guest(client)
    assert r.status_code == 429 and "ERR-AUTH-GUEST_RATE_LIMITED" in r.text

    class Req:
        client = None
        headers = {"x-forwarded-for": "6.6.6.6, 1.2.3.4"}
    monkeypatch.setattr(app_config, "TRUST_PROXY_HEADERS", True)
    assert app_config.client_ip(Req()) == "1.2.3.4"


def test_guest_student_cannot_read_or_start_class_assignment(client, db_session):
    """Guest students are enrolled nowhere: class assignments must stay 403/404, not be treated as enrolled."""
    from datetime import datetime, timedelta, timezone
    from models.models import Class, Exercise
    teacher = _guest(client, "Teacher").json()["user"]["user_id"]
    subject = Subject(subject_name=f"Ly {uuid.uuid4().hex[:6]}", status="ACTIVE")
    cls = Class(class_name=f"G{uuid.uuid4().hex[:6]}", status="ACTIVE")
    db_session.add_all([subject, cls])
    db_session.flush()
    ex = Exercise(title="E", subject_id=subject.subject_id, created_by=uuid.UUID(teacher), status="ACTIVE")
    db_session.add(ex)
    db_session.flush()
    asg = ClassAssignment(class_id=cls.class_id, exercise_id=ex.exercise_id, assigned_by=uuid.UUID(teacher),
                          due_at=datetime.now(timezone.utc) + timedelta(days=1), status="ACTIVE")
    db_session.add(asg)
    db_session.flush()
    s = _h(_guest(client, "Student"))
    aid = asg.assignment_id
    assert client.get(f"/api/v1/assignments/{aid}/taking", headers=s).status_code in (403, 404)
    assert client.post(f"/api/v1/assignments/{aid}/attempts", headers=s).status_code in (403, 404)


def test_guest_routes_use_only_allowed_permissions():
    """Every require_perm code on guest-facing routes must be in the guest allow-list."""
    import re
    from pathlib import Path
    from app.scripts.rbac_seed import GUEST_ALLOWED_PERMISSIONS
    root = Path(__file__).resolve().parents[3] / "app" / "modules" / "exercise" / "routers"
    allowed = set(GUEST_ALLOWED_PERMISSIONS["Student"])
    for name in ("ai_generation.py", "student_dashboard.py"):
        used = set(re.findall(r'require_perm\("([A-Z_]+)"\)', (root / name).read_text(encoding="utf-8")))
        assert used <= allowed, (name, used - allowed)


def test_xff_respects_trusted_hops(monkeypatch):
    class Req:
        client = None
        headers = {"x-forwarded-for": "6.6.6.6, 1.2.3.4, 10.0.0.1"}
    monkeypatch.setattr(app_config, "TRUST_PROXY_HEADERS", True)
    monkeypatch.setattr(app_config, "TRUSTED_PROXY_HOPS", 2)
    assert app_config.client_ip(Req()) == "1.2.3.4"
    monkeypatch.setattr(app_config, "TRUSTED_PROXY_HOPS", 9)
    assert app_config.client_ip(Req()) == "6.6.6.6"


def test_purge_stale_guests_soft_deletes_only_old_guests(client, db_session):
    from datetime import datetime, timedelta, timezone
    from app.scripts.purge_stale_guests import purge_stale_guests
    old = uuid.UUID(_guest(client).json()["user"]["user_id"])
    new = uuid.UUID(_guest(client).json()["user"]["user_id"])
    db_session.query(User).filter(User.user_id == old).update(
        {"created_at": datetime.now(timezone.utc) - timedelta(days=40)})
    db_session.flush()
    assert purge_stale_guests(db_session, 30) >= 1
    assert db_session.query(User).filter(User.user_id == old).one().status == "DELETED"
    assert db_session.query(User).filter(User.user_id == new).one().status == "ACTIVE"
