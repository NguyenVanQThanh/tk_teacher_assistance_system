# File Name: test_other_question_type.py
# Description: Unit tests for the "Other" question type (schema validation and manual grading skip) and type-change validation on update.
# Created At: 2026-11-12
# Created By: AI Agent
# Updated At: 2026-11-13
# Updated By: AI Agent

import uuid
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from app.modules.exercise.schemas import AnswerInput, QuestionCreate, QuestionUpdate
from app.modules.exercise.services.grading_service import GradingService


def _opts(n, correct=0):
    return [{"content": f"part {i}", "is_correct": i < correct, "display_order": i} for i in range(n)]


def test_other_create_requires_sub_questions_and_clears_correct():
    with pytest.raises(ValidationError):
        QuestionCreate(content="stem", question_type="Other")
    q = QuestionCreate(content="stem", question_type="Other", answer_options=_opts(2, correct=1))
    assert not any(o.is_correct for o in q.answer_options)


def test_update_type_change_validation():
    with pytest.raises(ValidationError):
        QuestionUpdate(question_type="TrueFalse", answer_options=_opts(3))
    with pytest.raises(ValidationError):
        QuestionUpdate(question_type="ShortAnswer", answer_options=_opts(2))
    with pytest.raises(ValidationError):
        QuestionUpdate(question_type="MultipleChoice", answer_options=_opts(4, correct=2))
    with pytest.raises(ValidationError):
        QuestionUpdate(question_type="Other", answer_options=[])
    QuestionUpdate(question_type="TrueFalse", answer_options=_opts(4, correct=2))
    QuestionUpdate(question_type="ShortAnswer", answer_options=[])
    QuestionUpdate(question_type="Other", answer_options=_opts(3))


def test_other_is_pending_manual_grade():
    service = GradingService(MagicMock())
    q_id = uuid.uuid4()
    q = MagicMock()
    q.question_id, q.question_type, q.status, q.answer_options = q_id, "Other", "ACTIVE", []
    ex = MagicMock()
    ex.questions = [q]
    service.exercise_repo.get_by_id = MagicMock(return_value=ex)
    score, detailed = service.grade_attempt(uuid.uuid4(), [AnswerInput(question_id=q_id, answer_text='["x","y"]')])
    res = detailed["questions"][0]
    assert score is None
    assert res["question_type"] == "Other" and res["is_correct"] is None and res["pending_manual_grade"] is True
    assert res["student_answer_text"] == '["x","y"]'


def test_regrade_keeps_teacher_verdict_on_other():
    # Teacher marks on "Other" (sent as manual_marks -> manual_override) must survive an answer-key regrade.
    db = MagicMock()
    service = GradingService(db)
    q_id = uuid.uuid4()
    q = MagicMock()
    q.question_id, q.question_type, q.status, q.answer_options = q_id, "Other", "ACTIVE", []
    ex = MagicMock()
    ex.questions = [q]
    service.exercise_repo.get_by_id = MagicMock(return_value=ex)
    att = MagicMock()
    att.detailed_results = {"questions": [{
        "question_id": str(q_id), "question_type": "Other", "student_answer_text": '["x"]',
        "is_correct": True, "manual_override": True, "pending_manual_grade": False,
    }]}
    db.query.return_value.join.return_value.filter.return_value.all.return_value = [att]
    assert service.regrade_exercise(uuid.uuid4()) == 1
    res = att.detailed_results["questions"][0]
    assert res["is_correct"] is True and res["pending_manual_grade"] is False and res["manual_override"] is True
