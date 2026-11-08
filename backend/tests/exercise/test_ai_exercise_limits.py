# File Name: test_ai_exercise_limits.py
# Description: Integration tests for AI-exercise resource limits (max 3 per student, must submit current
# AI exercise before creating another, admin notified via audit log) and the student report-to-admin endpoint.
# Created At: 2026-11-08
# Created By: Tam Khang

from fastapi import status
from fastapi.testclient import TestClient

from tests.exercise.test_exercises import get_admin_token, get_student_token


def _gen(client: TestClient, headers: dict, topic: str):
    return client.post(
        "/api/v1/exercises/ai-generate",
        json={
            "subject_name": "Lịch sử",
            "grade_name": "Lớp 12",
            "topic_prompt": topic,
            "part1_count": 1,
            "part2_count": 0,
            "part3_count": 0,
            "duration_minutes": 15,
        },
        headers=headers,
    )


def _finish_current(client: TestClient, headers: dict, assignment_id: str, exercise_id: str):
    detail = client.get(f"/api/v1/exercises/{exercise_id}", headers=headers).json()
    q = detail["questions"][0]
    opt = q["answer_options"][0]["option_id"]
    start = client.post(f"/api/v1/assignments/{assignment_id}/attempts", headers=headers)
    assert start.status_code == status.HTTP_201_CREATED
    attempt_id = start.json()["attempt_id"]
    sub = client.put(
        f"/api/v1/attempts/{attempt_id}/submit",
        json={"answers": [{"question_id": q["question_id"], "answer_option_id": opt}]},
        headers=headers,
    )
    assert sub.status_code == status.HTTP_200_OK
    assert sub.json()["is_finished"] is True


def test_ai_exercise_sliding_window_max_3_unfinished_and_admin_notify(client: TestClient):
    """Cửa sổ trượt: mỗi lần chỉ được 3 bài AI chưa hoàn thành; muốn tạo tiếp phải hoàn thành (nộp) bớt đi."""
    student_headers = {"Authorization": f"Bearer {get_student_token(client)}"}
    admin_headers = {"Authorization": f"Bearer {get_admin_token(client)}"}

    # Tạo liên tiếp được đúng 3 bài (unfinished: 1 -> 2 -> 3, đều < 3 trước khi tạo)
    created = []
    for i in range(1, 4):
        r = _gen(client, student_headers, f"Chủ đề ôn tập {i}")
        assert r.status_code == status.HTTP_201_CREATED
        created.append((r.json()["exercise_id"], r.json()["assignment_id"]))

    # Đang có 3 bài chưa hoàn thành -> không tạo được bài thứ 4
    r4 = _gen(client, student_headers, "Chủ đề ôn tập 4")
    assert r4.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert r4.json()["detail"]["code"] == "ERR-EXE-AI_UNFINISHED_LIMIT"
    assert "Mỗi lần bạn chỉ được tạo tối đa 3 bài tập tạo sinh AI" in r4.json()["detail"]["message"]

    # Admin nhận được notify kèm nội dung quy định
    logs = client.get("/api/v1/admin/dashboard/audit-logs?limit=50", headers=admin_headers).json()
    notify = [l for l in logs if "bài tập AI chưa hoàn thành" in (l.get("title") or "")]
    assert notify, "admin phải nhận được notify khi học sinh vượt 3 bài chưa hoàn thành"
    assert "Mỗi lần chỉ được tạo tối đa 3 bài tập tạo sinh AI" in (notify[0].get("description") or "")
    assert "sau khi hoàn thành" in (notify[0].get("description") or "").lower()

    # Hoàn thành (nộp) 1 bài -> unfinished còn 2 < 3 -> tạo tiếp được
    ex1, as1 = created[0]
    _finish_current(client, student_headers, as1, ex1)
    r4 = _gen(client, student_headers, "Chủ đề ôn tập 4")
    assert r4.status_code == status.HTTP_201_CREATED
    created.append((r4.json()["exercise_id"], r4.json()["assignment_id"]))

    # Lại đang 3 bài chưa hoàn thành -> chặn tiếp
    r5 = _gen(client, student_headers, "Chủ đề ôn tập 5")
    assert r5.status_code == status.HTTP_429_TOO_MANY_REQUESTS


def test_student_can_report_ai_exercise_to_admin(client: TestClient):
    student_headers = {"Authorization": f"Bearer {get_student_token(client)}"}
    admin_headers = {"Authorization": f"Bearer {get_admin_token(client)}"}

    r1 = _gen(client, student_headers, "Chủ đề báo lỗi")
    assert r1.status_code == status.HTTP_201_CREATED
    ex1 = r1.json()["exercise_id"]

    rep = client.post(
        f"/api/v1/exercises/{ex1}/report",
        json={"reason": "Câu hỏi bị trùng lặp và nội dung không bám SGK"},
        headers=student_headers,
    )
    assert rep.status_code == status.HTTP_201_CREATED
    assert rep.json()["reported"] is True

    logs = client.get("/api/v1/admin/dashboard/audit-logs?limit=50", headers=admin_headers).json()
    report_logs = [item for item in logs if "Báo cáo lỗi bài tập" in (item.get("title") or "")]
    assert len(report_logs) == 1
    assert "Câu hỏi bị trùng lặp" in (report_logs[0].get("description") or "")

    # Bài không tồn tại -> 404
    import uuid
    rep404 = client.post(
        f"/api/v1/exercises/{uuid.uuid4()}/report",
        json={"reason": "test"},
        headers=student_headers,
    )
    assert rep404.status_code == status.HTTP_404_NOT_FOUND
