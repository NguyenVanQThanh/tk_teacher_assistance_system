# File Name: test_exam_answer_redaction.py
# Description: Exam ("đề thi") attempt results hide per-question verdicts from the owning student.
# Created At: 2026-11-13
# Created By: AI Agent
# Updated At: 2026-11-17
# Updated By: AI Agent

import uuid
from types import SimpleNamespace

from app.modules.exercise.services.attempt_service import AttemptService

_RESULTS = {"questions": [{
    "question_id": "q1", "question_type": "TrueFalse", "student_answer_text": "a:true",
    "is_correct": False, "sub_results": {"a": False}, "points": 0.0, "max_points": 1.0,
}]}


_QIDS = {k: uuid.uuid4() for k in ("mcq", "tf", "sa")}
_OPT = uuid.uuid4()


def _opt(content, ok, oid=None):
    return SimpleNamespace(option_id=oid or uuid.uuid4(), content=content, is_correct=ok)


def _exercise(kind):
    qs = [
        SimpleNamespace(question_id=_QIDS["mcq"], question_type="MultipleChoice", status="ACTIVE", explanation="e1",
                        correct_answer=None, answer_options=[_opt("x", False), _opt("y", True, _OPT)]),
        SimpleNamespace(question_id=_QIDS["tf"], question_type="TrueFalse", status="ACTIVE", explanation="e2",
                        correct_answer=None, answer_options=[_opt("a) s1", True), _opt("b) s2", False)]),
        SimpleNamespace(question_id=_QIDS["sa"], question_type="ShortAnswer", status="ACTIVE", explanation="e3",
                        correct_answer="1.5", answer_options=[]),
    ]
    return SimpleNamespace(title="T", exercise_kind=kind, questions=qs)


KEY_FIELDS = ("correct_option_id", "correct_values", "correct_answer", "explanation")


def _attempt(student_id, kind, released=False, personal=False, finished=True):
    now = None
    return SimpleNamespace(
        attempt_id=uuid.uuid4(), student_id=student_id, assignment_id=uuid.uuid4(),
        student=SimpleNamespace(full_name="S", phone="1"),
        assignment=SimpleNamespace(
            class_id=uuid.uuid4(), answers_released_at=(object() if released else None), exercise_id=uuid.uuid4(), class_obj=None,
            owner_student_id=(student_id if personal else None),
            exercise=_exercise(kind),
        ),
        start_time=now, end_time=now, total_time_seconds=1, score=5.0,
        detailed_results=_RESULTS, is_finished=finished, status="ACTIVE", created_at=now, updated_at=now,
    )


def test_exam_hides_verdicts_for_owner_only():
    sid = uuid.uuid4()
    owner, teacher = SimpleNamespace(user_id=sid), SimpleNamespace(user_id=uuid.uuid4())
    att = _attempt(sid, "EXAM")
    q = AttemptService.redact_for_owner(att, owner).detailed_results["questions"][0]
    assert q == {"question_id": "q1", "question_type": "TrueFalse", "student_answer_text": "a:true"}
    assert AttemptService.redact_for_owner(att, owner).score == 5.0
    assert "is_correct" in AttemptService.redact_for_owner(att, teacher).detailed_results["questions"][0]
    assert AttemptService.redact_for_owner(att, owner).detailed_results["answer_key_revealed"] is False
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


def _qs(out):
    return out.detailed_results["questions"]


def test_practice_owner_gets_key():
    sid = uuid.uuid4()
    out = AttemptService.redact_for_owner(_attempt(sid, "PRACTICE", personal=True), SimpleNamespace(user_id=sid))
    assert out.detailed_results["answer_key_revealed"] is True
    assert out.detailed_results["questions"][0]  # results use q1 id, so no key merge on unknown ids


def test_key_merged_by_question_id():
    sid = uuid.uuid4()
    att = _attempt(sid, "PRACTICE", personal=True)
    att.detailed_results = {"questions": [
        {"question_id": str(_QIDS["mcq"]), "question_type": "MultipleChoice"},
        {"question_id": str(_QIDS["tf"]), "question_type": "TrueFalse"},
        {"question_id": str(_QIDS["sa"]), "question_type": "ShortAnswer"},
    ]}
    qs = _qs(AttemptService.redact_for_owner(att, SimpleNamespace(user_id=sid)))
    assert qs[0]["correct_option_id"] == str(_OPT)
    assert qs[1]["correct_values"] == {"a": True, "b": False}
    assert qs[2]["correct_answer"] == "1.5" and qs[2]["explanation"] == "e3"
    assert "correct_option_id" not in att.detailed_results["questions"][0]  # source untouched


def test_exam_personal_and_teacher_reveal_unfinished_does_not():
    sid = uuid.uuid4()
    owner = SimpleNamespace(user_id=sid)
    assert AttemptService.redact_for_owner(_attempt(sid, "EXAM", personal=True), owner).detailed_results["answer_key_revealed"]
    teacher = SimpleNamespace(user_id=uuid.uuid4())
    assert AttemptService.redact_for_owner(_attempt(sid, "EXAM"), teacher).detailed_results["answer_key_revealed"]
    out = AttemptService.redact_for_owner(_attempt(sid, "PRACTICE", personal=True, finished=False), owner)
    assert not out.detailed_results.get("answer_key_revealed")
    assert not any(f in out.detailed_results["questions"][0] for f in KEY_FIELDS)


def test_shared_practice_does_not_reveal_key_but_keeps_verdicts():
    """A class PRACTICE assignment may allow retakes: finishing alone must not leak the key."""
    sid = uuid.uuid4()
    out = AttemptService.redact_for_owner(_attempt(sid, "PRACTICE"), SimpleNamespace(user_id=sid))
    assert out.detailed_results["answer_key_revealed"] is False
    assert "is_correct" in out.detailed_results["questions"][0]
    assert not any(f in out.detailed_results["questions"][0] for f in KEY_FIELDS)
