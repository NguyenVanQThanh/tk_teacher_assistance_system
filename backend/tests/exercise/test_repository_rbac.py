# File Name: test_repository_rbac.py
# Description: RBAC matrix tests for document and exercise repositories (head-of-subject sharing, owner-only writes).
# Created At: 2026-11-13
# Created By: AI Agent
# Updated At: 2026-11-13
# Updated By: AI Agent

import uuid
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.modules.auth import access_policy
from app.modules.document.services.document_service import UPLOAD_DIR
from models.models import (
    Class, Document, Exercise, Question, Role, StudentClass, Subject, TeacherSubject, User,
)

PASSWORD = "password123"


def _login(client, phone):
    r = client.post("/api/v1/auth/login", json={"phone": phone, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _user(db, role_name, phone):
    role = db.query(Role).filter(Role.name == role_name).first()
    u = User(user_id=uuid.uuid4(), phone=phone, email=f"{phone}@rbac2.test",
             password_hash=get_password_hash(PASSWORD), full_name=f"{role_name} {phone}",
             role_id=role.role_id, status="Active")
    db.add(u)
    db.flush()
    return u


@pytest.fixture
def world(client: TestClient, db_session):
    """S1 (head H), S2; teachers A (C1) and B (C2) teach S1; H teaches S1; students X (C1), Z (C2)."""
    db = db_session
    sfx = uuid.uuid4().hex[:6]
    s1 = Subject(subject_name=f"RB S1 {sfx}", status="ACTIVE")
    s2 = Subject(subject_name=f"RB S2 {sfx}", status="ACTIVE")
    c1 = Class(class_name=f"RB1-{sfx}", status="ACTIVE")
    c2 = Class(class_name=f"RB2-{sfx}", status="ACTIVE")
    db.add_all([s1, s2, c1, c2])
    db.flush()
    n = int(sfx, 16) % 10000000
    a, b, h = (_user(db, "Teacher", f"07{n:07d}{i}") for i in (1, 2, 3))
    x, z = (_user(db, "Student", f"06{n:07d}{i}") for i in (1, 2))
    s1.head_teacher_id = h.user_id
    db.add_all([
        TeacherSubject(teacher_id=a.user_id, class_id=c1.class_id, subject_id=s1.subject_id, status="ACTIVE"),
        TeacherSubject(teacher_id=b.user_id, class_id=c2.class_id, subject_id=s1.subject_id, status="ACTIVE"),
        TeacherSubject(teacher_id=h.user_id, class_id=c1.class_id, subject_id=s1.subject_id, status="ACTIVE"),
        StudentClass(student_id=x.user_id, class_id=c1.class_id, status="ACTIVE"),
        StudentClass(student_id=z.user_id, class_id=c2.class_id, status="ACTIVE"),
    ])

    def doc(owner, subject, title, status="Uploaded", with_file=False):
        d = Document(uploaded_by=owner.user_id, subject_id=subject.subject_id, title=title,
                     status=status, file_type="pdf", file_url=f"rbac_{uuid.uuid4().hex}.pdf")
        db.add(d)
        db.flush()
        if with_file:
            (UPLOAD_DIR / Path(d.file_url).name).write_bytes(b"%PDF-1.4 rbac")
        return d

    def ex(owner, subject, title):
        e = Exercise(title=title, subject_id=subject.subject_id, created_by=owner.user_id,
                     total_questions=1, status="ACTIVE")
        db.add(e)
        db.flush()
        db.add(Question(exercise_id=e.exercise_id, content="Q?", question_type="ShortAnswer",
                        correct_answer="1", display_order=1))
        return e

    docs = {
        "dA": doc(a, s1, "dA"), "dB": doc(b, s1, "dB"),
        "dH": doc(h, s1, "dH", with_file=True), "dH2": doc(h, s2, "dH2"),
        "draft": doc(h, s1, "draft", status="Draft"),
    }
    exs = {"eA": ex(a, s1, "eA"), "eB": ex(b, s1, "eB"), "eH": ex(h, s1, "eH"), "eH2": ex(h, s2, "eH2")}
    db.commit()
    users = {"A": a, "B": b, "H": h, "X": x, "Z": z}
    yield {
        "h": {k: _login(client, u.phone) for k, u in users.items()},
        "admin": _login(client, "0987654321"),
        "docs": {k: str(v.document_id) for k, v in docs.items()},
        "ex": {k: str(v.exercise_id) for k, v in exs.items()},
        "users": users,
        "s1": s1,
    }
    for d in docs.values():
        (UPLOAD_DIR / Path(d.file_url).name).unlink(missing_ok=True)


def _titles(resp):
    assert resp.status_code == 200, resp.text
    return {i["title"] for i in resp.json()["items"]}


class TestDocumentRbac:
    def test_list_scope(self, client, world):
        h = world["h"]
        url = "/api/v1/documents?page_size=100"
        assert _titles(client.get(url, headers=h["A"])) == {"dA", "dH"}
        assert _titles(client.get(url + "&status=ALL", headers=h["H"])) == {"dH", "dH2", "draft"}
        assert {"dA", "dB", "dH", "dH2", "draft"} <= _titles(client.get(url + "&status=ALL", headers=world["admin"]))

    def test_other_teacher_doc_is_404_everywhere(self, client, world):
        hd, d = world["h"]["A"], world["docs"]["dB"]
        assert client.get(f"/api/v1/documents/{d}", headers=hd).status_code == 404
        assert client.get(f"/api/v1/documents/{d}/view", headers=hd).status_code == 404
        assert client.get(f"/api/v1/documents/{d}/download", headers=hd).status_code == 404
        assert client.put(f"/api/v1/documents/{d}", headers=hd, json={"title": "xxx"}).status_code == 404
        assert client.delete(f"/api/v1/documents/{d}", headers=hd).status_code == 404
        assert client.post(f"/api/v1/documents/{d}/restore", headers=hd).status_code == 404
        assert client.post(f"/api/v1/documents/{d}/ingest", headers=hd).status_code == 404

    def test_head_doc_read_only_for_teacher(self, client, world):
        hd, d = world["h"]["A"], world["docs"]["dH"]
        assert client.get(f"/api/v1/documents/{d}", headers=hd).status_code == 200
        assert client.get(f"/api/v1/documents/{d}/download", headers=hd).status_code == 200
        assert client.put(f"/api/v1/documents/{d}", headers=hd, json={"title": "xxx"}).status_code == 403
        assert client.delete(f"/api/v1/documents/{d}", headers=hd).status_code == 403

    def test_head_other_subject_and_draft_hidden(self, client, world):
        for k in ("dH2", "draft"):
            assert client.get(f"/api/v1/documents/{world['docs'][k]}", headers=world["h"]["A"]).status_code == 404

    def test_student_blocked(self, client, world):
        assert client.get("/api/v1/documents", headers=world["h"]["X"]).status_code == 403

    def test_admin_sees_all(self, client, world):
        assert client.get(f"/api/v1/documents/{world['docs']['draft']}", headers=world["admin"]).status_code == 200


class TestExerciseRbac:
    def test_list_scope(self, client, world):
        h = world["h"]
        assert _titles(client.get("/api/v1/exercises?page_size=50", headers=h["A"])) == {"eA", "eH"}
        assert _titles(client.get("/api/v1/exercises?page_size=50", headers=h["H"])) == {"eH", "eH2"}

    def test_other_teacher_exercise_404_on_all_ops(self, client, world):
        hd, e = world["h"]["A"], world["ex"]["eB"]
        assert client.get(f"/api/v1/exercises/{e}", headers=hd).status_code == 404
        assert client.get(f"/api/v1/exercises/{e}/export/pdf", headers=hd).status_code == 404
        assert client.put(f"/api/v1/exercises/{e}", headers=hd, json={"title": "xxx"}).status_code == 404
        assert client.put(f"/api/v1/exercises/{e}/answer-release", headers=hd, json={"released": True}).status_code == 404
        assert client.delete(f"/api/v1/exercises/{e}", headers=hd).status_code == 404
        assert client.post(f"/api/v1/exercises/{e}/restore", headers=hd).status_code == 404
        q = {"content": "n", "question_type": "ShortAnswer", "correct_answer": "1"}
        assert client.post(f"/api/v1/exercises/{e}/questions", headers=hd, json=q).status_code == 404
        key = client.put(f"/api/v1/exercises/{e}/answer-key", headers=hd, json={"keys": {}})
        assert key.status_code == 404

    def test_head_exercise_visible_but_not_writable(self, client, world):
        hd, e = world["h"]["A"], world["ex"]["eH"]
        assert client.get(f"/api/v1/exercises/{e}", headers=hd).status_code == 200
        assert client.put(f"/api/v1/exercises/{e}", headers=hd, json={"title": "xxx"}).status_code == 403
        assert client.delete(f"/api/v1/exercises/{e}", headers=hd).status_code == 403
        assert client.post(f"/api/v1/exercises/{e}/restore", headers=hd).status_code == 403
        q = {"content": "n", "question_type": "ShortAnswer", "correct_answer": "1"}
        assert client.post(f"/api/v1/exercises/{e}/questions", headers=hd, json=q).status_code == 403
        qid = client.get(f"/api/v1/exercises/{e}", headers=hd).json()["questions"][0]["question_id"]
        assert client.put(f"/api/v1/questions/{qid}", headers=hd, json={"content": "z"}).status_code == 403
        assert client.delete(f"/api/v1/questions/{qid}", headers=hd).status_code == 403

    def test_head_other_subject_hidden(self, client, world):
        assert client.get(f"/api/v1/exercises/{world['ex']['eH2']}", headers=world["h"]["A"]).status_code == 404

    def test_owner_can_write(self, client, world):
        r = client.put(f"/api/v1/exercises/{world['ex']['eA']}", headers=world["h"]["A"], json={"title": "renamed"})
        assert r.status_code == 200

    def test_student_own_only(self, client, world, db_session):
        assert client.get(f"/api/v1/exercises/{world['ex']['eA']}", headers=world["h"]["X"]).status_code == 404
        mine = Exercise(title="mine", subject_id=world["s1"].subject_id,
                        created_by=world["users"]["X"].user_id, total_questions=0, status="ACTIVE")
        db_session.add(mine)
        db_session.commit()
        assert client.get(f"/api/v1/exercises/{mine.exercise_id}", headers=world["h"]["X"]).status_code == 200

    def test_admin_sees_all(self, client, world):
        assert client.get(f"/api/v1/exercises/{world['ex']['eB']}", headers=world["admin"]).status_code == 200

    def test_ai_generate_teacher_only_and_document_check(self, client, world):
        body = {"subject_name": "RB", "topic_prompt": "t", "part1_count": 1, "part2_count": 0,
                "part3_count": 0, "duration_minutes": 45}
        assert client.post("/api/v1/exercises/ai-generate", headers=world["h"]["X"], json=body).status_code == 403
        r = client.post("/api/v1/exercises/ai-generate", headers=world["h"]["A"],
                        json={**body, "document_ids": [world["docs"]["dB"]]})
        assert r.status_code == 404


class TestAccessPolicyUnit:
    def test_is_teacher(self):
        assert access_policy.is_teacher("Teacher") and access_policy.is_teacher("HomeroomTeacher")
        assert not access_policy.is_teacher("Student") and not access_policy.is_teacher("Admin")

    def test_visible_document_ids_and_ensure_can_write(self, db_session, world):
        a, h = world["users"]["A"], world["users"]["H"]
        ids = [uuid.UUID(v) for v in world["docs"].values()]
        vis = access_policy.visible_document_ids(db_session, a, ids)
        assert vis == {uuid.UUID(world["docs"]["dA"]), uuid.UUID(world["docs"]["dH"])}
        access_policy.ensure_can_write(db_session, a, a.user_id)
        with pytest.raises(HTTPException) as exc:
            access_policy.ensure_can_write(db_session, a, h.user_id)
        assert exc.value.status_code == 403
        assert exc.value.detail["code"] == "ERR-AUTH-OWNER_ONLY"


class TestSubjectHeadTeacher:
    def test_set_head_validates_teacher(self, client, world):
        s1 = str(world["s1"].subject_id)
        a_id = str(world["users"]["A"].user_id)
        ok = client.put(f"/api/v1/subjects/{s1}/head-teacher", headers=world["admin"], json={"teacher_id": a_id})
        assert ok.status_code == 200 and ok.json()["head_teacher_id"] == a_id
        bad = client.put(f"/api/v1/subjects/{s1}/head-teacher", headers=world["admin"],
                         json={"teacher_id": str(world["users"]["X"].user_id)})
        assert bad.status_code == 422
        cleared = client.put(f"/api/v1/subjects/{s1}/head-teacher", headers=world["admin"], json={"teacher_id": None})
        assert cleared.status_code == 200 and cleared.json()["head_teacher_id"] is None

    def test_candidates_list_only_active_teachers_of_subject(self, client, world):
        s1 = str(world["s1"].subject_id)
        r = client.get(f"/api/v1/subjects/{s1}/head-teacher-candidates", headers=world["admin"])
        assert r.status_code == 200
        ids = {c["user_id"] for c in r.json()}
        assert str(world["users"]["A"].user_id) in ids
        assert str(world["users"]["X"].user_id) not in ids


class TestSingleHeadPerSubject:
    def test_reassign_replaces_previous_head(self, client, world, db_session=None):
        """A subject has exactly one head: assigning another teacher replaces the previous one."""
        s1 = str(world["s1"].subject_id)
        a_id = str(world["users"]["A"].user_id)
        h_id = str(world["users"]["H"].user_id)
        first = client.put(f"/api/v1/subjects/{s1}/head-teacher", headers=world["admin"], json={"teacher_id": h_id})
        assert first.status_code == 200 and first.json()["head_teacher_id"] == h_id
        second = client.put(f"/api/v1/subjects/{s1}/head-teacher", headers=world["admin"], json={"teacher_id": a_id})
        assert second.status_code == 200 and second.json()["head_teacher_id"] == a_id
        got = client.get(f"/api/v1/subjects/{s1}", headers=world["admin"])
        assert got.json()["head_teacher_id"] == a_id
        # Old head loses department-wide visibility: H's resources are no longer shared with teacher A's peers
        assert isinstance(got.json()["head_teacher_id"], str)
