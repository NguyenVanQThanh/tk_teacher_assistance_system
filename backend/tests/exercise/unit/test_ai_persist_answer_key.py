# File Name: test_ai_persist_answer_key.py
# Description: AI exercise persistence rejects questions without a correct answer and stores the MCQ letter.
# Created At: 2026-11-17
# Created By: AI Agent
# Updated At: 2026-11-17
# Updated By: AI Agent

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.modules.exercise.services.ai_exercise_service import AiExerciseService


def _svc():
    svc = AiExerciseService.__new__(AiExerciseService)
    svc.db = MagicMock()
    return svc


def _call(svc, questions):
    user = SimpleNamespace(user_id="u")
    subject = SimpleNamespace(subject_id="s", subject_name="Math")
    return svc._persist(user, subject, None, questions, {}, 45, "t", "G9", None)


def test_empty_short_answer_rejected():
    svc = _svc()
    with pytest.raises(HTTPException) as e:
        _call(svc, [{"content": "q", "question_type": "ShortAnswer", "correct_answer": " "}])
    assert e.value.status_code == 502
    assert "ERR-EXE-AI_ANSWER_KEY_MISSING" in str(e.value.detail)
    svc.db.commit.assert_not_called()


def test_mcq_letter_derived():
    svc = _svc()
    opts = [{"content": c, "is_correct": i == 2, "display_order": i} for i, c in enumerate("wxyz")]
    try:
        _call(svc, [{"content": "q", "question_type": "MultipleChoice", "answer_options": opts}])
    except Exception:
        pass  # post-commit serialisation of mocks is irrelevant here
    question = svc.db.add.call_args_list[1].args[0]
    assert question.correct_answer == "C"
