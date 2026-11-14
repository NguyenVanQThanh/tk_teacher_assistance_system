# File Name: test_student_ai_generation.py
# Description: API tests for the student AI generation endpoint (upload guards, validation, personal assignment, scoping).
# Created At: 2026-11-13
# Created By: AI Agent
# Updated At: 2026-11-13
# Updated By: AI Agent

import json
import uuid

import pytest

from models.models import (
    AnswerOption, Class, ClassAssignment, Question, StudentClass, Subject, TeacherSubject, User,
)
from app.modules.exercise.services import ai_exercise_service as svc_mod
from app.modules.exercise.services.rag_context_service import RagContextService
from app.modules.exercise.services.ai_generator_service import AiExerciseGeneratorService
from app.modules.exercise.services.rag_retrieval_service import RagRetrievalService

URL = "/api/v1/ai-exercises/student"
CH = "Chương 1: ESTER - LIPID"


def _login(client, phone):
    r = client.post("/api/v1/auth/login", json={"phone": phone, "password": "password123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def world(client, db_session, monkeypatch):
    student = db_session.query(User).filter(User.phone == "0934567890").one()
    teacher = db_session.query(User).filter(User.phone == "0912345678").one()
    subject = Subject(subject_name=f"Hóa học {uuid.uuid4().hex[:5]}", status="ACTIVE")
    cls = Class(class_name=f"12A{uuid.uuid4().hex[:4]}", status="ACTIVE")
    other_subject = Subject(subject_name=f"Vật lí {uuid.uuid4().hex[:5]}", status="ACTIVE")
    db_session.add_all([subject, cls, other_subject])
    db_session.flush()
    db_session.add_all([
        StudentClass(student_id=student.user_id, class_id=cls.class_id, status="ACTIVE"),
        TeacherSubject(teacher_id=teacher.user_id, class_id=cls.class_id, subject_id=subject.subject_id,
                       status="ACTIVE"),
    ])
    db_session.flush()
    monkeypatch.setattr(RagRetrievalService, "resolve_sgk_filter", staticmethod(lambda *a: ["doc1"]))
    monkeypatch.setattr(RagRetrievalService, "list_chapters",
                        staticmethod(lambda db, ids: [{"chapter": CH, "doc_id": "doc1", "page_start": 6}]))
    monkeypatch.setattr(RagContextService, "build_student_context", classmethod(lambda c, db, **kw: ("ctx", [])))
    return {"headers": _login(client, "0934567890"), "subject": subject, "other": other_subject, "cls": cls,
            "student": student}


def _payload(world, **over):
    p = {"subject_id": str(world["subject"].subject_id), "chapters": [CH], "topic_prompt": "este",
         "duration_minutes": 30,
         "matrix": {"mcq": {"NhanBiet": 1, "ThongHieu": 1, "VanDung": 0},
                    "tf": {"NhanBiet": 0, "ThongHieu": 1, "VanDung": 0},
                    "short": {"NhanBiet": 0, "ThongHieu": 0, "VanDung": 1}}}
    p.update(over)
    return p


def _post(client, world, payload=None, files=None, headers=None):
    return client.post(URL, data={"payload": json.dumps(payload or _payload(world))},
                       files=files or None, headers=headers or world["headers"])


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


def test_success_personal_assignment_and_tf_options(client, db_session, world, monkeypatch):
    _fake_questions(monkeypatch)
    r = _post(client, world, files={"file": ("n.txt", "Este la hop chat huu co".encode("utf-8"), "text/plain")})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["total_questions"] == 4
    a = db_session.query(ClassAssignment).filter(ClassAssignment.assignment_id == uuid.UUID(body["assignment_id"])).one()
    assert a.owner_student_id == world["student"].user_id and a.class_id == world["cls"].class_id
    tf = db_session.query(Question).filter(Question.exercise_id == uuid.UUID(body["exercise_id"]),
                                           Question.question_type == "TrueFalse").one()
    opts = db_session.query(AnswerOption).filter(AnswerOption.question_id == tf.question_id).order_by(
        AnswerOption.display_order).all()
    assert [o.content[:2] for o in opts] == ["a)", "b)", "c)", "d)"]
    assert [o.is_correct for o in opts] == [True, False, True, False]
    assert any(s["source"] == "student_file" for s in body["sources"])


def test_no_auto_creation_of_subject_or_class(client, db_session, world, monkeypatch):
    _fake_questions(monkeypatch)
    before = (db_session.query(Subject).count(), db_session.query(Class).count())
    assert _post(client, world).status_code == 201
    assert (db_session.query(Subject).count(), db_session.query(Class).count()) == before


def test_subject_not_taught_404_and_no_class_403(client, db_session, world):
    r = _post(client, world, _payload(world, subject_id=str(world["other"].subject_id)))
    assert r.status_code == 404
    db_session.query(StudentClass).filter(StudentClass.student_id == world["student"].user_id).delete()
    assert _post(client, world).status_code == 403


def test_teacher_cannot_use_student_endpoint(client, world):
    assert _post(client, world, headers=_login(client, "0912345678")).status_code == 403


def test_413_when_file_too_large(client, world):
    r = _post(client, world, files={"file": ("n.txt", b"a" * 1_048_576, "text/plain")})
    assert r.status_code == 413 and r.json()["detail"]["code"] == "ERR-EXE-AI_FILE_TOO_LARGE"
    r = _post(client, world, files={"file": ("n.txt", b"a" * (1_048_576 + 70_000), "text/plain")})
    assert r.status_code == 413


def test_411_without_content_length(client, world):
    def gen():
        yield b"--b\r\n"
    r = client.post(URL, content=gen(), headers={**world["headers"], "Content-Type": "multipart/form-data; boundary=b"})
    assert r.status_code == 411


def test_415_fake_pdf_and_bad_extension(client, world):
    assert _post(client, world, files={"file": ("fake.pdf", b"not a pdf", "application/pdf")}).status_code == 415
    assert _post(client, world, files={"file": ("x.exe", b"MZ", "application/octet-stream")}).status_code == 415
    assert _post(client, world, files={"file": ("x.txt", b"\xff\xfe\x00bad", "text/plain")}).status_code == 415


def test_422_image_only_pdf(client, world):
    import fitz
    doc = fitz.open()
    doc.new_page()
    r = _post(client, world, files={"file": ("scan.pdf", doc.tobytes(), "application/pdf")})
    assert r.status_code == 422 and r.json()["detail"]["code"] == "ERR-EXE-AI_FILE_NO_TEXT"


@pytest.mark.parametrize("override,code", [
    ({"chapters": []}, "ERR-EXE-AI_CHAPTER_REQUIRED"),
    ({"chapters": ["Chuong 99: X"]}, "ERR-EXE-AI_INVALID_CHAPTER"),
    ({"matrix": {"mcq": {}, "tf": {}, "short": {}}}, "ERR-EXE-AI_EMPTY_MATRIX"),
    ({"topic_prompt": "x" * 301}, "ERR-EXE-AI_INVALID_PAYLOAD"),
    ({"duration_minutes": 1}, "ERR-EXE-AI_INVALID_PAYLOAD"),
    ({"matrix": {"mcq": {"NhanBiet": 16}}}, "ERR-EXE-AI_INVALID_PAYLOAD"),
    ({"matrix": {"mcq": {"NhanBiet": 15, "ThongHieu": 15, "VanDung": 15}, "tf": {"NhanBiet": 1}}},
     "ERR-EXE-AI_MATRIX_TOO_LARGE"),
])
def test_422_validation(client, world, override, code):
    r = _post(client, world, _payload(world, **override))
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["code"] == code


def test_chapters_endpoint_and_scope(client, world):
    r = client.get("/api/v1/ai-exercises/chapters", params={"subject_id": str(world["subject"].subject_id)},
                   headers=world["headers"])
    assert r.status_code == 200 and r.json()[0]["chapter"] == CH
    r = client.get("/api/v1/ai-exercises/chapters", params={"subject_id": str(world["other"].subject_id)},
                   headers=world["headers"])
    assert r.status_code == 404


def test_busy_returns_503(client, world, monkeypatch):
    class Busy:
        def acquire(self, timeout=None):
            return False
    monkeypatch.setattr(svc_mod, "AI_GENERATE_SEMAPHORE", Busy())
    r = _post(client, world)
    assert r.status_code == 503 and r.json()["detail"]["code"] == "ERR-EXE-AI_BUSY"


def test_generation_failure_502(client, world, monkeypatch):
    monkeypatch.setattr("app.modules.exercise.services.ai_generator_service.GeminiVisionParserService.get_api_key",
                        lambda: None)
    assert _post(client, world).status_code == 502
