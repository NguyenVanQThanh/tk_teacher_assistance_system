# File Name: test_taking_and_sync.py
# Description: Tests for the student-safe "taking" paper endpoints
#              (GET /api/v1/assignments/{id}/taking, GET /api/v1/attempts/{id}/paper)
#              and the sync/version APIs (GET /api/v1/sync/version, GET /api/v1/sync/stream, X-Data-Version).
# Created At: 2026-11-12
# Created By: AI Agent
# Updated At: 2026-11-12
# Updated By: AI Agent

import json
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


def get_student2_token(client: TestClient) -> str:
    # student_allow@test.com — a Student-role account NOT enrolled in the test class
    resp = client.post(
        "/api/v1/auth/login",
        json={"phone": "0934567891", "password": "password123"}
    )
    return resp.json()["access_token"]


def _sensitive_keys_in(obj, found=None):
    """Recursively collect any sensitive key names present in a decoded JSON structure."""
    if found is None:
        found = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() in {"is_correct", "correct", "answer", "answers", "correct_answer", "explanation"}:
                found.add(str(k))
            _sensitive_keys_in(v, found)
    elif isinstance(obj, list):
        for item in obj:
            _sensitive_keys_in(item, found)
    return found


@pytest.fixture
def exam_setup(client: TestClient):
    """Create subject + class + teacher assignment + student enrollment + exercise with questions."""
    admin_headers = {"Authorization": f"Bearer {get_admin_token(client)}"}
    teacher_headers = {"Authorization": f"Bearer {get_teacher_token(client)}"}
    student_headers = {"Authorization": f"Bearer {get_student_token(client)}"}

    subject_resp = client.post(
        "/api/v1/subjects",
        json={"subject_name": f"Toan Hoc {uuid.uuid4().hex[:6]}"},
        headers=admin_headers
    )
    assert subject_resp.status_code == status.HTTP_201_CREATED
    subject_id = subject_resp.json()["subject_id"]

    class_resp = client.post(
        "/api/v1/classes",
        json={"class_name": f"Lop 12A{uuid.uuid4().hex[:4]}", "school_year": "2025-2026"},
        headers=admin_headers
    )
    assert class_resp.status_code == status.HTTP_201_CREATED
    class_id = class_resp.json()["class_id"]

    teacher_id = client.get("/api/v1/auth/me", headers=teacher_headers).json()["user_id"]
    student_id = client.get("/api/v1/auth/me", headers=student_headers).json()["user_id"]

    client.post(
        f"/api/v1/classes/{class_id}/teacher-subjects",
        json={"teacher_id": teacher_id, "subject_id": subject_id},
        headers=admin_headers
    )
    enroll_resp = client.post(
        f"/api/v1/classes/{class_id}/students",
        json={"student_id": student_id, "student_code": f"STU_{uuid.uuid4().hex[:4]}"},
        headers=admin_headers
    )
    assert enroll_resp.status_code == status.HTTP_201_CREATED

    exercise_resp = client.post(
        "/api/v1/exercises",
        json={"title": f"Bai Kiem Tra {uuid.uuid4().hex[:4]}", "subject_id": subject_id},
        headers=teacher_headers
    )
    assert exercise_resp.status_code == status.HTTP_201_CREATED
    exercise_id = exercise_resp.json()["exercise_id"]

    # MC question 1 (answer options carry is_correct in DB)
    q1_resp = client.post(
        f"/api/v1/exercises/{exercise_id}/questions",
        json={
            "content": "2 + 2 = ?",
            "question_type": "MultipleChoice",
            "display_order": 1,
            "answer_options": [
                {"content": "3", "is_correct": False, "display_order": 1},
                {"content": "4", "is_correct": True, "display_order": 2}
            ]
        },
        headers=teacher_headers
    )
    assert q1_resp.status_code == status.HTTP_201_CREATED

    # ShortAnswer question 2 with correct_answer + explanation, plus nasty segments
    q2_resp = client.post(
        f"/api/v1/exercises/{exercise_id}/questions",
        json={
            "content": "Giai thich trong luong.",
            "question_type": "ShortAnswer",
            "correct_answer": "Trong luong la luc hap dan...",
            "explanation": "Vi trai dat hut vat the...",
            "display_order": 2,
            "segments": [
                {
                    "type": "text",
                    "content": "Cau hoi co dap an ben trong",
                    "is_correct": True,
                    "answer": "Dap an bi mat",
                    "nested": {
                        "type": "math",
                        "latex": "F = m.g",
                        "correct": True,
                        "confidence": 0.91,
                        "bbox": [1.0, 2.0, 3.0, 4.0]
                    }
                }
            ]
        },
        headers=teacher_headers
    )
    assert q2_resp.status_code == status.HTTP_201_CREATED

    return {
        "admin_headers": admin_headers,
        "teacher_headers": teacher_headers,
        "student_headers": student_headers,
        "subject_id": subject_id,
        "class_id": class_id,
        "exercise_id": exercise_id,
    }


def _create_assignment(client: TestClient, setup: dict) -> str:
    due_time = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    resp = client.post(
        f"/api/v1/classes/{setup['class_id']}/assignments",
        json={"exercise_id": setup["exercise_id"], "due_at": due_time},
        headers=setup["teacher_headers"]
    )
    assert resp.status_code == status.HTTP_201_CREATED, f"create assignment failed: {resp.text}"
    return resp.json()["assignment_id"]


class TestStudentSafeTaking:
    def test_taking_is_sanitized(self, client: TestClient, exam_setup: dict):
        student_headers = exam_setup["student_headers"]
        assignment_id = _create_assignment(client, exam_setup)

        resp = client.get(
            f"/api/v1/assignments/{assignment_id}/taking",
            headers=student_headers
        )
        assert resp.status_code == status.HTTP_200_OK, resp.text
        body = resp.json()

        # Structure checks
        assert body["assignment"]["assignment_id"] == assignment_id
        assert body["assignment"]["class_id"] == exam_setup["class_id"]
        assert body["exercise"]["exercise_id"] == exam_setup["exercise_id"]
        assert body["exercise"]["subject_id"] == exam_setup["subject_id"]
        assert body["exercise"]["subject_name"]
        assert "duration_minutes" in body["assignment"]
        assert "max_attempts" in body["assignment"]
        assert "status" in body["assignment"]
        assert len(body["questions"]) == 2
        assert body["open_attempt"] is None

        # No answer key anywhere in the raw JSON text
        assert "correct_answer" not in resp.text
        assert "explanation" not in resp.text
        assert '"is_correct"' not in resp.text
        assert "Dap an bi mat" not in resp.text  # sensitive segment key stripped

        # Per-question key checks
        for q in body["questions"]:
            assert "correct_answer" not in q
            assert "explanation" not in q
            for opt in q["answer_options"]:
                assert set(opt.keys()) == {"option_id", "question_id", "content", "display_order"}

        # Segments sanitized recursively, but safe keys kept
        q2 = next(q for q in body["questions"] if q["question_type"] == "ShortAnswer")
        seg = q2["segments"][0]
        assert seg["type"] == "text"
        assert seg["content"] == "Cau hoi co dap an ben trong"
        assert "is_correct" not in seg and "answer" not in seg
        nested = seg["nested"]
        assert nested["type"] == "math"
        assert nested["latex"] == "F = m.g"
        assert nested["confidence"] == 0.91
        assert nested["bbox"] == [1.0, 2.0, 3.0, 4.0]
        assert "correct" not in nested
        assert _sensitive_keys_in(body["questions"]) == set()

    def test_taking_includes_open_attempt(self, client: TestClient, exam_setup: dict):
        student_headers = exam_setup["student_headers"]
        assignment_id = _create_assignment(client, exam_setup)

        start_resp = client.post(
            f"/api/v1/assignments/{assignment_id}/attempts",
            headers=student_headers
        )
        assert start_resp.status_code == status.HTTP_201_CREATED
        attempt_id = start_resp.json()["attempt_id"]

        resp = client.get(
            f"/api/v1/assignments/{assignment_id}/taking",
            headers=student_headers
        )
        assert resp.status_code == status.HTTP_200_OK
        open_attempt = resp.json()["open_attempt"]
        assert open_attempt is not None
        assert open_attempt["attempt_id"] == attempt_id
        assert open_attempt["created_at"] is not None
        # Still no answer key leaked
        assert "correct_answer" not in resp.text
        assert '"is_correct"' not in resp.text

    def test_taking_forbidden_when_not_enrolled(self, client: TestClient, exam_setup: dict):
        assignment_id = _create_assignment(client, exam_setup)
        student2_headers = {"Authorization": f"Bearer {get_student2_token(client)}"}

        resp = client.get(
            f"/api/v1/assignments/{assignment_id}/taking",
            headers=student2_headers
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()["detail"]["code"] == "ERR-EXE-STUDENT_NOT_ENROLLED"

    def test_taking_404_when_assignment_deleted(self, client: TestClient, exam_setup: dict):
        assignment_id = _create_assignment(client, exam_setup)
        student_headers = exam_setup["student_headers"]

        del_resp = client.delete(
            f"/api/v1/assignments/{assignment_id}",
            headers=exam_setup["teacher_headers"]
        )
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT

        resp = client.get(
            f"/api/v1/assignments/{assignment_id}/taking",
            headers=student_headers
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_attempt_paper_owner_only_and_sanitized(self, client: TestClient, exam_setup: dict):
        student_headers = exam_setup["student_headers"]
        assignment_id = _create_assignment(client, exam_setup)

        start_resp = client.post(
            f"/api/v1/assignments/{assignment_id}/attempts",
            headers=student_headers
        )
        assert start_resp.status_code == status.HTTP_201_CREATED
        attempt_id = start_resp.json()["attempt_id"]

        # Owner can read the sanitized paper
        resp = client.get(
            f"/api/v1/attempts/{attempt_id}/paper",
            headers=student_headers
        )
        assert resp.status_code == status.HTTP_200_OK, resp.text
        assert "correct_answer" not in resp.text
        assert "explanation" not in resp.text
        assert '"is_correct"' not in resp.text
        assert len(resp.json()["questions"]) == 2
        assert resp.json()["open_attempt"]["attempt_id"] == attempt_id

        # Another student cannot
        student2_headers = {"Authorization": f"Bearer {get_student2_token(client)}"}
        resp2 = client.get(
            f"/api/v1/attempts/{attempt_id}/paper",
            headers=student2_headers
        )
        assert resp2.status_code == status.HTTP_403_FORBIDDEN


class TestSyncVersion:
    def test_version_endpoint_200_and_shape(self, client: TestClient, exam_setup: dict):
        student_headers = exam_setup["student_headers"]
        resp = client.get("/api/v1/sync/version", headers=student_headers)
        assert resp.status_code == status.HTTP_200_OK, resp.text
        body = resp.json()
        assert isinstance(body["version"], str) and body["version"]
        expected_tables = {
            "exercises", "questions", "answer_options", "class_assignments",
            "student_exercise_attempts", "subjects", "classes"
        }
        assert expected_tables.issubset(set(body["tables"].keys()))
        # Middleware must stamp X-Data-Version on GET responses
        assert resp.headers.get("X-Data-Version") == body["version"]

    def test_version_endpoint_requires_auth(self, client: TestClient):
        resp = client.get("/api/v1/sync/version")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_data_version_header_on_other_get(self, client: TestClient, exam_setup: dict):
        student_headers = exam_setup["student_headers"]
        resp = client.get("/api/v1/assignments", headers=student_headers)
        assert resp.status_code == status.HTTP_200_OK
        assert "X-Data-Version" in resp.headers

    def test_sync_stream_sse_first_event(self, client: TestClient, db_session, monkeypatch, exam_setup: dict):
        # NOTE: TestClient/httpx-ASGITransport buffer streaming bodies in this environment, so the
        # HTTP-level stream cannot be consumed in-process. We drive the route handler directly and
        # verify the StreamingResponse (media type, headers) plus the first `data:` event.
        # Over real HTTP (uvicorn) this endpoint was verified to stream correctly.
        import asyncio
        from sqlalchemy.orm import sessionmaker
        from fastapi.responses import StreamingResponse
        from starlette.requests import Request
        from app.modules.exercise.routers.sync import sync_stream

        # The stream opens short-lived sessions via app.core.database.SessionLocal -> point them
        # at the test engine for this test.
        factory = sessionmaker(bind=db_session.bind)
        monkeypatch.setattr("app.core.database.SessionLocal", factory)

        token = exam_setup["student_headers"]["Authorization"].replace("Bearer ", "")
        scope = {
            "type": "http", "method": "GET", "path": "/api/v1/sync/stream",
            "headers": [(b"authorization", f"Bearer {token}".encode())],
            "query_string": b"",
        }
        request = Request(scope)

        async def run():
            resp = await sync_stream(request=request, token=None)
            assert isinstance(resp, StreamingResponse)
            assert resp.media_type == "text/event-stream"
            assert resp.headers.get("cache-control") == "no-cache"
            iterator = resp.body_iterator
            chunk = await iterator.__anext__()
            await iterator.aclose()
            return chunk

        chunk = asyncio.run(run())
        assert isinstance(chunk, str)
        assert chunk.startswith("data: ") and chunk.endswith("\n\n")
        payload = json.loads(chunk[len("data: "):].strip())
        assert "version" in payload and "tables" in payload
        assert {
            "exercises", "questions", "answer_options", "class_assignments",
            "student_exercise_attempts", "subjects", "classes"
        }.issubset(set(payload["tables"].keys()))

    def test_sync_stream_accepts_query_token(self, client: TestClient, db_session, monkeypatch, exam_setup: dict):
        # EventSource cannot set headers, so the SSE route accepts ?token= (only here).
        import asyncio
        from sqlalchemy.orm import sessionmaker
        from starlette.requests import Request
        from app.modules.exercise.routers.sync import sync_stream

        factory = sessionmaker(bind=db_session.bind)
        monkeypatch.setattr("app.core.database.SessionLocal", factory)
        token = exam_setup["student_headers"]["Authorization"].replace("Bearer ", "")
        scope = {"type": "http", "method": "GET", "path": "/api/v1/sync/stream", "headers": [], "query_string": b""}

        async def run():
            resp = await sync_stream(request=Request(scope), token=token)
            it = resp.body_iterator
            chunk = await it.__anext__()
            await it.aclose()
            return chunk

        chunk = asyncio.run(run())
        assert chunk.startswith("data: ")

    def test_version_endpoint_rejects_query_token(self, client: TestClient, exam_setup: dict):
        # JWTs must only travel in the Authorization header (query strings leak into logs).
        # The ?token= variant is reserved for the SSE stream only.
        token = exam_setup["student_headers"]["Authorization"].replace("Bearer ", "")
        resp = client.get(f"/api/v1/sync/version?token={token}")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        # header auth still works
        resp2 = client.get("/api/v1/sync/version", headers=exam_setup["student_headers"])
        assert resp2.status_code == status.HTTP_200_OK
        assert resp2.json()["version"]

    def test_version_includes_soft_deleted_rows(self, client: TestClient, db_session, exam_setup: dict):
        # A soft-deleted record (status=DELETED) with a bumped updated_at MUST raise the version,
        # otherwise the FE would never learn that an assignment/exercise was cancelled.
        from sqlalchemy import update
        from models.models import ClassAssignment
        from app.modules.exercise.services.sync_service import SyncService

        assignment_id = _create_assignment(client, exam_setup)
        fut = datetime.now(timezone.utc) + timedelta(days=1)
        db_session.execute(
            update(ClassAssignment)
            .where(ClassAssignment.assignment_id == uuid.UUID(assignment_id))
            .values(status="DELETED", updated_at=fut)
        )
        db_session.commit()

        snap = SyncService(db_session).get_version_snapshot()
        ca_ts = snap["tables"]["class_assignments"]
        assert ca_ts is not None
        parsed = datetime.fromisoformat(ca_ts.replace("Z", "+00:00"))
        assert parsed >= fut - timedelta(seconds=1)
        # global version is at least that timestamp
        assert datetime.fromisoformat(snap["version"].replace("Z", "+00:00")) >= fut - timedelta(seconds=1)

    def test_version_bumps_when_assignment_cancelled_via_api(self, client: TestClient, db_session, exam_setup: dict):
        from app.modules.exercise.services.sync_service import SyncService

        assignment_id = _create_assignment(client, exam_setup)
        db_session.expire_all()
        v1 = SyncService(db_session).get_version_snapshot()

        del_resp = client.delete(
            f"/api/v1/assignments/{assignment_id}",
            headers=exam_setup["teacher_headers"],
        )
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT

        db_session.expire_all()
        v2 = SyncService(db_session).get_version_snapshot()
        parse = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))
        # version must not go backwards and the class_assignments table ts must reflect the change
        assert parse(v2["version"]) >= parse(v1["version"])
        if v1["tables"]["class_assignments"] is not None:
            assert parse(v2["tables"]["class_assignments"]) >= parse(v1["tables"]["class_assignments"])


def _set_due_past(db_session, assignment_id: str) -> None:
    """Move an assignment's due_at into the past directly in the DB (API requires future)."""
    from sqlalchemy import update
    from models.models import ClassAssignment
    past = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.execute(
        update(ClassAssignment)
        .where(ClassAssignment.assignment_id == uuid.UUID(assignment_id))
        .values(due_at=past)
    )
    db_session.commit()


class TestTakingWindowAndScoping:
    def test_taking_blocked_after_due_without_attempt(self, client: TestClient, db_session, exam_setup: dict):
        aid = _create_assignment(client, exam_setup)
        _set_due_past(db_session, aid)
        resp = client.get(f"/api/v1/assignments/{aid}/taking", headers=exam_setup["student_headers"])
        assert resp.status_code == status.HTTP_403_FORBIDDEN, resp.text
        assert resp.json()["detail"]["code"] == "ERR-EXE-ASSIGNMENT_EXPIRED"

    def test_start_attempt_blocked_after_due(self, client: TestClient, db_session, exam_setup: dict):
        aid = _create_assignment(client, exam_setup)
        _set_due_past(db_session, aid)
        resp = client.post(f"/api/v1/assignments/{aid}/attempts", headers=exam_setup["student_headers"])
        assert resp.status_code == status.HTTP_403_FORBIDDEN, resp.text
        assert resp.json()["detail"]["code"] == "ERR-EXE-ASSIGNMENT_EXPIRED"

    def test_taking_allowed_for_finished_attempt_after_due(self, client: TestClient, db_session, exam_setup: dict):
        # Review of an already-submitted attempt must keep working even after the due date.
        aid = _create_assignment(client, exam_setup)
        sh = exam_setup["student_headers"]
        att = client.post(f"/api/v1/assignments/{aid}/attempts", headers=sh).json()["attempt_id"]
        ex = client.get(
            f"/api/v1/exercises/{exam_setup['exercise_id']}",
            headers=exam_setup["teacher_headers"]
        ).json()
        qid = ex["questions"][0]["question_id"]
        sub = client.put(f"/api/v1/attempts/{att}/submit", json={"answers": [{"question_id": qid, "answer_text": "x"}]}, headers=sh)
        assert sub.status_code == status.HTTP_200_OK, sub.text
        _set_due_past(db_session, aid)
        resp = client.get(f"/api/v1/assignments/{aid}/taking", headers=sh)
        assert resp.status_code == status.HTTP_200_OK, resp.text
        assert len(resp.json()["questions"]) == 2

    def test_start_attempt_blocked_when_max_attempts_reached(self, client: TestClient, exam_setup: dict):
        # Create assignment with max_attempts=1, finish one attempt, then a new start must 403.
        due = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        resp = client.post(
            f"/api/v1/classes/{exam_setup['class_id']}/assignments",
            json={"exercise_id": exam_setup["exercise_id"], "due_at": due, "max_attempts": 1},
            headers=exam_setup["teacher_headers"]
        )
        assert resp.status_code == status.HTTP_201_CREATED, resp.text
        aid = resp.json()["assignment_id"]
        sh = exam_setup["student_headers"]
        att = client.post(f"/api/v1/assignments/{aid}/attempts", headers=sh).json()["attempt_id"]
        ex = client.get(f"/api/v1/exercises/{exam_setup['exercise_id']}", headers=exam_setup["teacher_headers"]).json()
        qid = ex["questions"][0]["question_id"]
        sub = client.put(f"/api/v1/attempts/{att}/submit", json={"answers": [{"question_id": qid, "answer_text": "x"}]}, headers=sh)
        assert sub.status_code == status.HTTP_200_OK
        again = client.post(f"/api/v1/assignments/{aid}/attempts", headers=sh)
        assert again.status_code == status.HTTP_403_FORBIDDEN
        assert again.json()["detail"]["code"] == "ERR-EXE-ATTEMPT_LIMIT_REACHED"

    def test_student_attempts_scoped_to_self(self, client: TestClient, exam_setup: dict):
        # A Student passing another student's id must still only see their own attempts.
        aid = _create_assignment(client, exam_setup)
        sh = exam_setup["student_headers"]
        client.post(f"/api/v1/assignments/{aid}/attempts", headers=sh)
        me = client.get("/api/v1/auth/me", headers=sh).json()["user_id"]
        other = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {get_student2_token(client)}"}
        ).json()["user_id"]
        assert me != other
        resp = client.get(f"/api/v1/attempts?student_id={other}", headers=sh)
        assert resp.status_code == status.HTTP_200_OK, resp.text
        items = resp.json()
        assert len(items) >= 1
        for item in items:
            assert item["student_id"] == me

    def test_regrade_preserves_teacher_total_score(self, client: TestClient, exam_setup: dict):
        # Teacher sets a manual total score; a later answer-key regrade must NOT overwrite it.
        aid = _create_assignment(client, exam_setup)
        sh, th = exam_setup["student_headers"], exam_setup["teacher_headers"]
        att = client.post(f"/api/v1/assignments/{aid}/attempts", headers=sh).json()["attempt_id"]
        ex = client.get(f"/api/v1/exercises/{exam_setup['exercise_id']}", headers=th).json()
        q = next(q for q in ex["questions"] if q["question_type"] == "MultipleChoice")
        opt_wrong = next(o for o in q["answer_options"] if not o["is_correct"])
        opt_right = next(o for o in q["answer_options"] if o["is_correct"])
        sub = client.put(
            f"/api/v1/attempts/{att}/submit",
            json={"answers": [{"question_id": q["question_id"], "answer_option_id": opt_wrong["option_id"]}]},
            headers=sh
        )
        assert sub.status_code == status.HTTP_200_OK, sub.text
        g = client.put(f"/api/v1/attempts/{att}/grade", json={"score": 9.5}, headers=th)
        assert g.status_code == status.HTTP_200_OK, g.text
        # Change the answer key -> triggers regrade of all submissions of the exercise.
        ak = client.put(
            f"/api/v1/exercises/{exam_setup['exercise_id']}/answer-key",
            json={"keys": {q["question_id"]: opt_right["option_id"]}},
            headers=th
        )
        assert ak.status_code == status.HTTP_200_OK, ak.text
        assert ak.json()["regraded_attempts"] >= 1
        det = client.get(f"/api/v1/attempts/{att}", headers=sh).json()
        assert det["score"] == 9.5  # teacher's manual total score preserved
