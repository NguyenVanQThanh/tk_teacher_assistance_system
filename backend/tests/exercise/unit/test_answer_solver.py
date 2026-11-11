# File Name: test_answer_solver.py
# Description: Unit tests for AnswerSolverService with a mocked Mistral call (no network).
# Created At: 2026-11-10
# Created By: AI Agent
# Updated At: 2026-11-10
# Updated By: AI Agent
import json
from unittest.mock import patch

from app.modules.exercise.schemas import QuestionTypeEnum as T
from app.modules.exercise.services import answer_solver_service as svc
from app.modules.exercise.services.import_parser_service import ParsedOption, ParsedQuestion


def q(n, t, correct=None, fig=False):
    opts = [ParsedOption(content=x, is_correct=(i == correct), display_order=i) for i, x in enumerate("abcd")]
    return ParsedQuestion(question_number=n, part="Part1", question_type=t, difficulty=None, content="c",
                          answer_options=[] if t == T.ShortAnswer else opts, image_url="x.png" if fig else None)


def run(qs, reply):
    with patch.object(svc, "_chat", side_effect=reply if callable(reply) else None, return_value=None if callable(reply) else reply):
        return svc.AnswerSolverService.solve_questions(qs)


def res(**kw):
    return {"number": 1, "answer": None, "tf": None, "confidence": 0.9, "rationale": "r", **kw}


def test_mc_solved():
    m = q(1, T.MultipleChoice)
    assert run([m], json.dumps({"results": [res(answer="C")]})) == 1
    assert [o.is_correct for o in m.answer_options] == [False, False, True, False]
    assert m.correct_answer == "C" and m.image_metadata["solved_by"] == "ai" and not m.needs_review


def test_tf_per_statement():
    t = q(1, T.TrueFalse)
    run([t], json.dumps({"results": [res(tf={"a": True, "b": False, "c": True, "d": False})]}))
    assert [o.is_correct for o in t.answer_options] == [True, False, True, False]


def test_short_and_keyed_untouched():
    s, k = q(1, T.ShortAnswer), q(2, T.MultipleChoice, correct=1)
    assert run([s, k], AssertionError("no call expected")) == 0
    assert [o.is_correct for o in k.answer_options] == [False, True, False, False]


def test_low_confidence_and_figure_flagged():
    a, b = q(1, T.MultipleChoice), q(2, T.MultipleChoice, fig=True)
    body = {"results": [res(answer="A", confidence=0.3), res(number=2, answer="B")]}
    run([a, b], json.dumps(body))
    assert a.needs_review and b.needs_review


def test_malformed_json_and_chunks():
    m = q(1, T.MultipleChoice)
    assert run([m], "not json") == 0
    assert m.needs_review and not any(o.is_correct for o in m.answer_options)
    m2 = q(1, T.MultipleChoice)
    with patch.object(svc, "_chat", side_effect=[RuntimeError("422"), "```json\n" + json.dumps({"results": [res(answer="B")]}) + "\n```"]):
        assert svc.AnswerSolverService.solve_questions([m2]) == 1
    assert m2.correct_answer == "B"
