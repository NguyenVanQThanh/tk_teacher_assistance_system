# File Name: test_taking_and_sync.py
# Description: Tests for the student-safe "taking" paper endpoints
#              (GET /api/v1/assignments/{id}/taking, GET /api/v1/attempts/{id}/paper)
#              and the sync/version APIs (GET /api/v1/sync/version, GET /api/v1/sync/stream, X-Data-Version).
# Created At: 2026-11-12
# Created By: AI Agent
# Updated At: 2026-11-13
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


async def _receive_empty():
    return {"type": "http.request", "body": b"", "more_body": False}


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
        async def _receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        request = Request(scope, _receive)

        async def run():
            resp = await sync_stream(request=request, ticket=None)
            assert isinstance(resp, StreamingResponse)
            assert resp.media_type == "text/event-stream"
            assert resp.headers.get("cache-control") == "no-cache, no-store"
            assert resp.headers.get("referrer-policy") == "no-referrer"
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

    def _stream_first_chunk(self, db_session, monkeypatch, ticket):
        import asyncio
        from sqlalchemy.orm import sessionmaker
        from starlette.requests import Request
        from app.modules.exercise.routers.sync import sync_stream

        monkeypatch.setattr("app.core.database.SessionLocal", sessionmaker(bind=db_session.bind))
        scope = {"type": "http", "method": "GET", "path": "/api/v1/sync/stream", "headers": [], "query_string": b""}

        async def run():
            resp = await sync_stream(request=Request(scope, _receive_empty), ticket=ticket)
            it = resp.body_iterator
            chunk = await it.__anext__()
            await it.aclose()
            return chunk

        return asyncio.run(run())

    def test_stream_ticket_flow(self, client: TestClient, db_session, monkeypatch, exam_setup: dict):
        headers = exam_setup["student_headers"]
        resp = client.post("/api/v1/sync/stream-ticket", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        ticket = resp.json()["ticket"]
        assert self._stream_first_chunk(db_session, monkeypatch, ticket).startswith("data: ")
        # The ticket is not an access token anywhere else.
        assert client.get("/api/v1/sync/version", headers={"Authorization": f"Bearer {ticket}"}).status_code == 401
        # Ticket endpoint itself needs a real access token.
        assert client.post("/api/v1/sync/stream-ticket").status_code == 401

    def test_stream_rejects_access_jwt_and_bad_ticket_in_query(self, db_session, monkeypatch, exam_setup: dict):
        from fastapi import HTTPException
        token = exam_setup["student_headers"]["Authorization"].replace("Bearer ", "")
        for bad in (token, "garbage", None):
            with pytest.raises(HTTPException) as exc:
                self._stream_first_chunk(db_session, monkeypatch, bad)
            assert exc.value.status_code == 401

    def test_stream_rejects_expired_ticket(self, db_session, monkeypatch, exam_setup: dict):
        from datetime import datetime, timedelta, timezone
        from fastapi import HTTPException
        from jose import jwt
        from app.core.security import SECRET_KEY, ALGORITHM
        from app.core.security import create_stream_ticket
        valid = create_stream_ticket("00000000-0000-0000-0000-000000000000")
        sub = jwt.get_unverified_claims(valid)["sub"]
        expired = jwt.encode(
            {"sub": sub, "typ": "sse", "exp": datetime.now(timezone.utc) - timedelta(seconds=5)},
            SECRET_KEY, algorithm=ALGORITHM)
        with pytest.raises(HTTPException) as exc:
            self._stream_first_chunk(db_session, monkeypatch, expired)
        assert exc.value.status_code == 401

    def test_version_endpoint_rejects_query_token(self, client: TestClient, exam_setup: dict):
        # JWTs must only travel in the Authorization header (query strings leak into logs).
        token = exam_setup["student_headers"]["Authorization"].replace("Bearer ", "")
        resp = client.get(f"/api/v1/sync/version?token={token}")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
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


class TestReviewHardening:
    def test_teacher_attempts_student_id_filter(self, client: TestClient, exam_setup: dict):
        # A teacher filtering by student_id gets only that student's attempts.
        aid = _create_assignment(client, exam_setup)
        sh, th = exam_setup["student_headers"], exam_setup["teacher_headers"]
        client.post(f"/api/v1/assignments/{aid}/attempts", headers=sh)
        me = client.get("/api/v1/auth/me", headers=sh).json()["user_id"]
        hit = client.get(f"/api/v1/attempts?student_id={me}", headers=th)
        assert hit.status_code == status.HTTP_200_OK, hit.text
        assert len(hit.json()) >= 1 and all(i["student_id"] == me for i in hit.json())
        miss = client.get(f"/api/v1/attempts?student_id={uuid.uuid4()}", headers=th)
        assert miss.status_code == status.HTTP_200_OK, miss.text
        assert miss.json() == []

    def test_answer_key_owner_only_and_regrades_all_classes(self, client: TestClient, exam_setup: dict):
        # The answer key is shared across classes: the owner's change rescores EVERY class's
        # attempts (no stale scores elsewhere); a non-owner teacher may not change it.
        ah, th = exam_setup["admin_headers"], exam_setup["teacher_headers"]
        ex = client.get(f"/api/v1/exercises/{exam_setup['exercise_id']}", headers=th).json()
        q = next(q for q in ex["questions"] if q["question_type"] == "MultipleChoice")
        right = next(o for o in q["answer_options"] if o["is_correct"])
        wrong = next(o for o in q["answer_options"] if not o["is_correct"])
        answers = {"answers": [{"question_id": q["question_id"], "answer_option_id": wrong["option_id"]}]}

        # Teacher's own class attempt.
        aid = _create_assignment(client, exam_setup)
        att1 = client.post(f"/api/v1/assignments/{aid}/attempts", headers=exam_setup["student_headers"]).json()["attempt_id"]
        assert client.put(f"/api/v1/attempts/{att1}/submit", json=answers, headers=exam_setup["student_headers"]).status_code == 200

        # Another class the teacher is NOT assigned to, same exercise, other student.
        other_class = client.post(
            "/api/v1/classes", json={"class_name": f"Lop X{uuid.uuid4().hex[:4]}", "school_year": "2025-2026"}, headers=ah
        ).json()["class_id"]
        s2h = {"Authorization": f"Bearer {get_student2_token(client)}"}
        s2id = client.get("/api/v1/auth/me", headers=s2h).json()["user_id"]
        assert client.post(
            f"/api/v1/classes/{other_class}/students",
            json={"student_id": s2id, "student_code": f"STU_{uuid.uuid4().hex[:4]}"}, headers=ah
        ).status_code == 201
        due = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        a2 = client.post(
            f"/api/v1/classes/{other_class}/assignments",
            json={"exercise_id": exam_setup["exercise_id"], "due_at": due}, headers=ah
        )
        assert a2.status_code == 201, a2.text
        att2 = client.post(f"/api/v1/assignments/{a2.json()['assignment_id']}/attempts", headers=s2h).json()["attempt_id"]
        assert client.put(f"/api/v1/attempts/{att2}/submit", json=answers, headers=s2h).status_code == 200

        assert client.get(f"/api/v1/attempts/{att2}", headers=ah).json()["score"] == 0

        # Owner flips the key to the previously wrong option -> both classes rescored.
        url = f"/api/v1/exercises/{exam_setup['exercise_id']}/answer-key"
        r = client.put(url, json={"keys": {q["question_id"]: wrong["option_id"]}}, headers=th)
        assert r.status_code == 200, r.text
        assert r.json()["regraded_attempts"] == 2
        assert client.get(f"/api/v1/attempts/{att2}", headers=ah).json()["score"] > 0

        # A teacher cannot see an Admin-owned exercise (no head-of-subject sharing), so the key is hidden (404).
        admin_ex = client.post(
            "/api/v1/exercises", json={"title": "Admin exam", "subject_id": exam_setup["subject_id"]}, headers=ah
        ).json()["exercise_id"]
        denied = client.put(f"/api/v1/exercises/{admin_ex}/answer-key", json={"keys": {}}, headers=th)
        assert denied.status_code == status.HTTP_404_NOT_FOUND, denied.text
        assert client.put(url, json={"keys": {q["question_id"]: right["option_id"]}}, headers=ah).status_code == 200

    def test_grade_save_with_auto_total_does_not_pin_score(self, client: TestClient, exam_setup: dict):
        # The grading UI resends the auto total on every save; that must not freeze the score
        # against a later answer-key regrade. Only a differing total is a teacher override.
        aid = _create_assignment(client, exam_setup)
        sh, th = exam_setup["student_headers"], exam_setup["teacher_headers"]
        ex = client.get(f"/api/v1/exercises/{exam_setup['exercise_id']}", headers=th).json()
        q = next(q for q in ex["questions"] if q["question_type"] == "MultipleChoice")
        wrong = next(o for o in q["answer_options"] if not o["is_correct"])
        att = client.post(f"/api/v1/assignments/{aid}/attempts", headers=sh).json()["attempt_id"]
        sub = client.put(
            f"/api/v1/attempts/{att}/submit",
            json={"answers": [{"question_id": q["question_id"], "answer_option_id": wrong["option_id"]}]}, headers=sh
        )
        assert sub.status_code == 200, sub.text
        g = client.put(f"/api/v1/attempts/{att}/grade", json={"score": sub.json()["score"], "feedback": "ok"}, headers=th)
        assert g.status_code == 200, g.text
        assert "teacher_total_score" not in g.json()["detailed_results"]
        assert g.json()["detailed_results"]["teacher_feedback"] == "ok"
        ak = client.put(
            f"/api/v1/exercises/{exam_setup['exercise_id']}/answer-key",
            json={"keys": {q["question_id"]: wrong["option_id"]}}, headers=th
        )
        assert ak.status_code == 200, ak.text
        assert client.get(f"/api/v1/attempts/{att}", headers=th).json()["score"] > sub.json()["score"]

    def test_open_attempt_window_closes_after_due_plus_duration(self, client: TestClient, db_session, exam_setup: dict):
        # An open attempt may be resumed/submitted until due_at + duration (45 min default), not forever.
        from sqlalchemy import update
        from models.models import ClassAssignment
        aid = _create_assignment(client, exam_setup)
        sh = exam_setup["student_headers"]
        att = client.post(f"/api/v1/assignments/{aid}/attempts", headers=sh).json()["attempt_id"]

        def set_due(delta):
            db_session.execute(update(ClassAssignment).where(ClassAssignment.assignment_id == uuid.UUID(aid))
                               .values(due_at=datetime.now(timezone.utc) + delta))
            db_session.commit()

        set_due(timedelta(minutes=-10))  # past due, still inside the duration grace
        assert client.get(f"/api/v1/assignments/{aid}/taking", headers=sh).status_code == 200
        set_due(timedelta(minutes=-60))  # past due_at + 45 min
        resp = client.get(f"/api/v1/assignments/{aid}/taking", headers=sh)
        assert resp.status_code == 403 and resp.json()["detail"]["code"] == "ERR-EXE-ASSIGNMENT_EXPIRED"
        sub = client.put(f"/api/v1/attempts/{att}/submit", json={"answers": []}, headers=sh)
        assert sub.status_code == 403 and sub.json()["detail"]["code"] == "ERR-EXE-ASSIGNMENT_EXPIRED"
        set_due(timedelta(minutes=-10))
        assert client.put(f"/api/v1/attempts/{att}/submit", json={"answers": []}, headers=sh).status_code == 200

    def test_taking_ai_metadata_whitelisted(self, client: TestClient, db_session, exam_setup: dict):
        from models.models import Exercise
        ex = db_session.query(Exercise).filter(Exercise.exercise_id == uuid.UUID(exam_setup["exercise_id"])).one()
        ex.ai_metadata = {
            "type": "exam", "grade": 12, "duration_minutes": 30, "is_ai_generated": True,
            "topic_prompt": "SECRET PROMPT", "document_ids": ["d1"], "part1_count": 5,
        }
        db_session.commit()
        aid = _create_assignment(client, exam_setup)
        resp = client.get(f"/api/v1/assignments/{aid}/taking", headers=exam_setup["student_headers"])
        assert resp.status_code == 200, resp.text
        meta = resp.json()["exercise"].get("ai_metadata") or {}
        assert meta.get("type") == "exam" and meta.get("grade") == 12
        for leaked in ("topic_prompt", "document_ids", "part1_count"):
            assert leaked not in meta
        assert "SECRET PROMPT" not in resp.text


# =====================================================================
# DISPLAY SHUFFLE — per-attempt question/MultipleChoice-option order
# (display-only alias; questions/answer_options rows in the DB never change)
# =====================================================================

def _create_shuffle_assignment(client: TestClient, setup: dict, max_attempts=None) -> str:
    """Create an assignment for the fixture exercise, optionally overriding max_attempts."""
    due_time = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    payload = {"exercise_id": setup["exercise_id"], "due_at": due_time}
    if max_attempts is not None:
        payload["max_attempts"] = max_attempts
    resp = client.post(
        f"/api/v1/classes/{setup['class_id']}/assignments",
        json=payload,
        headers=setup["teacher_headers"],
    )
    assert resp.status_code == status.HTTP_201_CREATED, resp.text
    return resp.json()["assignment_id"]


def _add_multiple_choice_question(client: TestClient, setup: dict, index: int) -> str:
    """Add one MultipleChoice question (2 options) to the fixture exercise."""
    resp = client.post(
        f"/api/v1/exercises/{setup['exercise_id']}/questions",
        json={
            "content": f"Shuffle question {index}",
            "question_type": "MultipleChoice",
            "display_order": 100 + index,
            "answer_options": [
                {"content": f"Q{index} option A", "is_correct": False, "display_order": 1},
                {"content": f"Q{index} option B", "is_correct": True, "display_order": 2},
            ],
        },
        headers=setup["teacher_headers"],
    )
    assert resp.status_code == status.HTTP_201_CREATED, resp.text
    return resp.json()["question_id"]


def _start_attempt(client: TestClient, assignment_id: str, headers: dict) -> str:
    resp = client.post(f"/api/v1/assignments/{assignment_id}/attempts", headers=headers)
    assert resp.status_code == status.HTTP_201_CREATED, resp.text
    return resp.json()["attempt_id"]


def _get_taking(client: TestClient, assignment_id: str, headers: dict) -> dict:
    resp = client.get(f"/api/v1/assignments/{assignment_id}/taking", headers=headers)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    return resp.json()


def _display_signature(body: dict):
    """Ordered question ids + ordered option ids per question, exactly as displayed."""
    return (
        [q["question_id"] for q in body["questions"]],
        {
            q["question_id"]: [o["option_id"] for o in q["answer_options"]]
            for q in body["questions"]
        },
    )


def _db_paper_order(db_session, exercise_id: str):
    """Persisted order: question display_order, option display_order, and option order per question."""
    from sqlalchemy.orm import joinedload
    from models.models import Question

    db_session.expire_all()
    questions = (
        db_session.query(Question)
        .options(joinedload(Question.answer_options))
        .filter(Question.exercise_id == uuid.UUID(exercise_id))
        .all()
    )
    q_orders = {str(q.question_id): q.display_order for q in questions}
    o_orders = {str(o.option_id): o.display_order for q in questions for o in q.answer_options}
    o_by_q = {
        str(q.question_id): [str(o.option_id) for o in q.answer_options]
        for q in questions
    }
    return q_orders, o_orders, o_by_q


class TestDisplayShuffle:
    def test_shuffle_is_stable_for_same_attempt(self, client: TestClient, db_session, exam_setup: dict):
        setup = exam_setup
        sh = setup["student_headers"]
        assignment_id = _create_shuffle_assignment(client, setup)
        _start_attempt(client, assignment_id, sh)

        first = _get_taking(client, assignment_id, sh)
        second = _get_taking(client, assignment_id, sh)

        # Same attempt -> identical question/option order on every reload.
        assert _display_signature(first) == _display_signature(second)

        # display_order is a 1-based alias over the shuffled display order.
        assert [q["display_order"] for q in first["questions"]] == list(
            range(1, len(first["questions"]) + 1)
        )
        for q in first["questions"]:
            if q["question_type"] == "MultipleChoice":
                assert [o["display_order"] for o in q["answer_options"]] == list(
                    range(1, len(q["answer_options"]) + 1)
                )

        # Every DB question/option appears exactly once (nothing lost, nothing duplicated).
        q_orders, _o_orders, o_by_q = _db_paper_order(db_session, setup["exercise_id"])
        assert {q["question_id"] for q in first["questions"]} == set(q_orders)
        for q in first["questions"]:
            displayed = [o["option_id"] for o in q["answer_options"]]
            assert len(displayed) == len(set(displayed))
            assert set(displayed) == set(o_by_q[q["question_id"]])

    def test_shuffle_differs_between_attempts(self, client: TestClient, db_session, exam_setup: dict):
        setup = exam_setup
        sh = setup["student_headers"]
        # 7 MultipleChoice questions + 1 ShortAnswer: two independent seeds colliding on the exact
        # same question+option order is ~1/8! * 1/2^7, i.e. effectively impossible.
        for i in range(6):
            _add_multiple_choice_question(client, setup, i)
        assignment_id = _create_shuffle_assignment(client, setup, max_attempts=3)

        att1 = _start_attempt(client, assignment_id, sh)
        first = _get_taking(client, assignment_id, sh)
        sub = client.put(f"/api/v1/attempts/{att1}/submit", json={"answers": []}, headers=sh)
        assert sub.status_code == status.HTTP_200_OK, sub.text

        att2 = _start_attempt(client, assignment_id, sh)
        second = _get_taking(client, assignment_id, sh)

        # Each attempt owns a random seed stored in the existing detailed_results JSON column.
        from models.models import StudentExerciseAttempt

        db_session.expire_all()
        attempts = (
            db_session.query(StudentExerciseAttempt)
            .filter(StudentExerciseAttempt.attempt_id.in_([uuid.UUID(att1), uuid.UUID(att2)]))
            .all()
        )
        seeds = {
            str(a.attempt_id): (a.detailed_results or {}).get("shuffle_seed")
            for a in attempts
        }
        assert seeds[att1] and seeds[att2]
        assert seeds[att1] != seeds[att2]

        assert _display_signature(first) != _display_signature(second)

    def test_shuffle_review_keeps_attempt_order(self, client: TestClient, exam_setup: dict):
        setup = exam_setup
        sh = setup["student_headers"]
        assignment_id = _create_shuffle_assignment(client, setup)
        att = _start_attempt(client, assignment_id, sh)
        during = _get_taking(client, assignment_id, sh)

        sub = client.put(f"/api/v1/attempts/{att}/submit", json={"answers": []}, headers=sh)
        assert sub.status_code == status.HTTP_200_OK, sub.text

        # Reviewing the submitted attempt (paper endpoint) keeps the order seen while taking it.
        paper = client.get(f"/api/v1/attempts/{att}/paper", headers=sh)
        assert paper.status_code == status.HTTP_200_OK, paper.text
        assert _display_signature(paper.json()) == _display_signature(during)

        # The assignment paper of the same (now finished) attempt keeps it too.
        review = _get_taking(client, assignment_id, sh)
        assert _display_signature(review) == _display_signature(during)

        # A teacher grade save (whose payload is rebuilt from the teacher view, i.e. without the
        # internal seed) must not drop the seed either: review order stays identical.
        teacher_view = client.get(f"/api/v1/attempts/{att}", headers=setup["teacher_headers"])
        assert teacher_view.status_code == status.HTTP_200_OK, teacher_view.text
        assert "shuffle_seed" not in (teacher_view.json().get("detailed_results") or {})
        grade = client.put(
            f"/api/v1/attempts/{att}/grade",
            json={
                "score": teacher_view.json()["score"],
                "detailed_results": teacher_view.json()["detailed_results"],
            },
            headers=setup["teacher_headers"],
        )
        assert grade.status_code == status.HTTP_200_OK, grade.text
        after_grade = client.get(f"/api/v1/attempts/{att}/paper", headers=sh)
        assert after_grade.status_code == status.HTTP_200_OK, after_grade.text
        assert _display_signature(after_grade.json()) == _display_signature(during)

    def test_shuffle_does_not_change_db(self, client: TestClient, db_session, exam_setup: dict):
        setup = exam_setup
        sh = setup["student_headers"]
        assignment_id = _create_shuffle_assignment(client, setup)
        before = _db_paper_order(db_session, setup["exercise_id"])

        _get_taking(client, assignment_id, sh)  # pre-start preview
        assert _db_paper_order(db_session, setup["exercise_id"]) == before

        _start_attempt(client, assignment_id, sh)
        _get_taking(client, assignment_id, sh)  # attempt paper
        assert _db_paper_order(db_session, setup["exercise_id"]) == before

    def test_true_false_options_not_shuffled(self, client: TestClient, db_session, exam_setup: dict):
        setup = exam_setup
        tf_resp = client.post(
            f"/api/v1/exercises/{setup['exercise_id']}/questions",
            json={
                "content": "True/False statements",
                "question_type": "TrueFalse",
                "display_order": 3,
                "answer_options": [
                    {"content": "a) Statement A", "is_correct": True, "display_order": 1},
                    {"content": "b) Statement B", "is_correct": False, "display_order": 2},
                    {"content": "c) Statement C", "is_correct": True, "display_order": 3},
                    {"content": "d) Statement D", "is_correct": False, "display_order": 4},
                ],
            },
            headers=setup["teacher_headers"],
        )
        assert tf_resp.status_code == status.HTTP_201_CREATED, tf_resp.text
        tf_id = tf_resp.json()["question_id"]

        sh = setup["student_headers"]
        assignment_id = _create_shuffle_assignment(client, setup)
        att = _start_attempt(client, assignment_id, sh)
        body = _get_taking(client, assignment_id, sh)

        # TrueFalse options keep the DB order (a/b/c/d labels are positional for grading).
        tf = next(q for q in body["questions"] if q["question_id"] == tf_id)
        _q_orders, o_orders, o_by_q = _db_paper_order(db_session, setup["exercise_id"])
        assert [o["option_id"] for o in tf["answer_options"]] == o_by_q[tf_id]
        assert [o["display_order"] for o in tf["answer_options"]] == [
            o_orders[oid] for oid in o_by_q[tf_id]
        ]

        # Grading still maps a/b/c/d to the DB order -> the correct pattern scores full marks.
        sub = client.put(
            f"/api/v1/attempts/{att}/submit",
            json={"answers": [{"question_id": tf_id, "answer_text": "a:true;b:false;c:true;d:false"}]},
            headers=sh,
        )
        assert sub.status_code == status.HTTP_200_OK, sub.text
        tf_result = next(
            r for r in sub.json()["detailed_results"]["questions"] if r["question_id"] == tf_id
        )
        assert tf_result["is_correct"] is True
        assert tf_result["points"] > 0

    def test_shuffle_grading_still_correct(self, client: TestClient, exam_setup: dict):
        setup = exam_setup
        sh, th = setup["student_headers"], setup["teacher_headers"]
        assignment_id = _create_shuffle_assignment(client, setup)
        att = _start_attempt(client, assignment_id, sh)
        body = _get_taking(client, assignment_id, sh)

        # The answer key is only visible teacher-side; the student picks the displayed option id.
        ex = client.get(f"/api/v1/exercises/{setup['exercise_id']}", headers=th).json()
        mc = next(q for q in ex["questions"] if q["question_type"] == "MultipleChoice")
        correct_option_id = next(o["option_id"] for o in mc["answer_options"] if o["is_correct"])

        student_mc = next(q for q in body["questions"] if q["question_id"] == mc["question_id"])
        displayed_ids = [o["option_id"] for o in student_mc["answer_options"]]
        assert correct_option_id in displayed_ids

        sub = client.put(
            f"/api/v1/attempts/{att}/submit",
            json={"answers": [{"question_id": mc["question_id"], "answer_option_id": correct_option_id}]},
            headers=sh,
        )
        assert sub.status_code == status.HTTP_200_OK, sub.text
        assert sub.json()["score"] > 0
        result = next(
            r for r in sub.json()["detailed_results"]["questions"]
            if r["question_id"] == mc["question_id"]
        )
        assert result["is_correct"] is True
