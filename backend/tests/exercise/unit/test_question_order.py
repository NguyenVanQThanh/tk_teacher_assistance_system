# File Name: test_question_order.py
# Description: Unit tests for part-grouped question shuffling.
# Created At: 2026-11-17
# Created By: AI Agent
# Updated At: 2026-11-17
# Updated By: AI Agent

import uuid
from datetime import datetime, timezone

from app.modules.exercise.schemas import StudentQuestionOut, StudentAnswerOptionOut
from app.modules.exercise.services.assignment_service import _shuffle_student_questions
from app.modules.exercise.services.question_order import PART_RANK

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _q(qtype, order, n_opts=4):
    qid = uuid.uuid4()
    opts = [
        StudentAnswerOptionOut(option_id=uuid.uuid4(), question_id=qid, content=f"{c}) x", display_order=i)
        for i, c in enumerate("abcd"[:n_opts], 1)
    ]
    return StudentQuestionOut(
        question_id=qid, exercise_id=uuid.uuid4(), content="q", question_type=qtype,
        display_order=order, is_ai_generated=False, status="ACTIVE",
        created_at=_NOW, updated_at=_NOW, answer_options=opts,
    )


def _paper():
    types = ["ShortAnswer", "MultipleChoice", "TrueFalse"] * 4
    return [_q(t, i) for i, t in enumerate(types, 1)]


def test_parts_grouped_and_continuous():
    out = _shuffle_student_questions(_paper(), "seed")
    ranks = [PART_RANK[q.question_type] for q in out]
    assert ranks == sorted(ranks)
    assert [q.display_order for q in out] == list(range(1, 13))


def test_multiset_preserved():
    src = _paper()
    out = _shuffle_student_questions(src, "seed")
    assert {q.question_id for q in out} == {q.question_id for q in src}
    assert len(out) == len(src)


def test_deterministic():
    src = _paper()
    a = [q.question_id for q in _shuffle_student_questions(src, "s1")]
    b = [q.question_id for q in _shuffle_student_questions(src, "s1")]
    assert a == b


def test_true_false_options_unchanged():
    src = _paper()
    before = {q.question_id: [o.option_id for o in q.answer_options] for q in src if q.question_type == "TrueFalse"}
    out = _shuffle_student_questions(src, "seed")
    for q in out:
        if q.question_type == "TrueFalse":
            assert [o.option_id for o in q.answer_options] == before[q.question_id]
