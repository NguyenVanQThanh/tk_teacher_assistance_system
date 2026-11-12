# File Name: test_exam_answer_redaction.py
# Description: Exam ("đề thi") attempt results hide per-question verdicts from the owning student.
# Created At: 2026-11-13
# Created By: AI Agent
# Updated At: 2026-11-13
# Updated By: AI Agent

import uuid
from types import SimpleNamespace

from app.modules.exercise.services.attempt_service import AttemptService

_RESULTS = {"questions": [{
    "question_id": "q1", "question_type": "TrueFalse", "student_answer_text": "a:true",
    "is_correct": False, "sub_results": {"a": False}, "points": 0.0, "max_points": 1.0,
}]}


def _attempt(student_id, kind, released=False):
    now = None
    return SimpleNamespace(
        attempt_id=uuid.uuid4(), student_id=student_id, assignment_id=uuid.uuid4(),
        student=SimpleNamespace(full_name="S", phone="1"),
        assignment=SimpleNamespace(
            class_id=uuid.uuid4(), answers_released_at=(object() if released else None), exercise_id=uuid.uuid4(), class_obj=None,
            exercise=SimpleNamespace(title="T", exercise_kind=kind),
        ),
        start_time=now, end_time=now, total_time_seconds=1, score=5.0,
        detailed_results=_RESULTS, is_finished=True, status="ACTIVE", created_at=now, updated_at=now,
    )


def test_exam_hides_verdicts_for_owner_only():
    sid = uuid.uuid4()
    owner, teacher = SimpleNamespace(user_id=sid), SimpleNamespace(user_id=uuid.uuid4())
    att = _attempt(sid, "EXAM")
    q = AttemptService.redact_for_owner(att, owner).detailed_results["questions"][0]
    assert q == {"question_id": "q1", "question_type": "TrueFalse", "student_answer_text": "a:true"}
    assert AttemptService.redact_for_owner(att, owner).score == 5.0
    assert "is_correct" in AttemptService.redact_for_owner(att, teacher).detailed_results["questions"][0]
    assert "is_correct" in _RESULTS["questions"][0]  # source untouched


def test_regular_exercise_keeps_verdicts():
    sid = uuid.uuid4()
    att = _attempt(sid, "PRACTICE")
    out = AttemptService.redact_for_owner(att, SimpleNamespace(user_id=sid))
    assert "is_correct" in out.detailed_results["questions"][0]


def test_released_exam_shows_verdicts():
    sid = uuid.uuid4()
    out = AttemptService.redact_for_owner(_attempt(sid, "EXAM", released=True), SimpleNamespace(user_id=sid))
    assert "is_correct" in out.detailed_results["questions"][0]
