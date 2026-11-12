# File Name: test_other_question_type.py
# Description: Unit tests for the "Other" question type (schema validation and manual grading skip) and type-change validation on update.
# Created At: 2026-11-12
# Created By: AI Agent
# Updated At: 2026-11-12
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
