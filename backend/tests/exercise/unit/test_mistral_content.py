# File Name: test_mistral_content.py
# Description: Unit tests for Mistral content flattening and the answer solver's multi-exam/TF behaviour (mocked, no network).
# Created At: 2026-11-10
# Created By: AI Agent
# Updated At: 2026-11-10
# Updated By: AI Agent
import json
from types import SimpleNamespace
from unittest.mock import patch

import httpx
import pytest

from app.modules.exercise.schemas import QuestionTypeEnum as T
from app.modules.exercise.services import answer_solver_service as svc
from app.modules.exercise.services.import_parser_service import ParsedOption, ParsedQuestion
from app.modules.exercise.services.mistral_vision_parser_service import (
    MistralVisionParserService, flatten_content, raise_for_status_logged)


def test_flatten_variants():
    assert flatten_content(None) == "" and flatten_content("x") == "x"
    parts = [{"type": "thinking", "thinking": [{"type": "text", "text": "hidden"}]},
             {"type": "text", "text": "a"}, "b", SimpleNamespace(type="text", text="c"),
             SimpleNamespace(type="thinking", thinking="no")]
    assert flatten_content(parts) == "abc"


def test_chat_handles_list_content():
    body = {"choices": [{"message": {"content": [{"type": "thinking", "thinking": "t"},
                                                 {"type": "text", "text": "{\"results\": []}"}]}}]}
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json=body))
    real = httpx.Client
    with patch.object(MistralVisionParserService, "get_api_key", return_value="k"), \
            patch.object(httpx, "Client", lambda **kw: real(transport=transport)):
        assert svc._chat({"model": "m"}) == "{\"results\": []}"


def test_stream_with_list_delta_does_not_raise():
    sse = "\n".join("data: " + json.dumps({"choices": [{"delta": {"content": c}}]}) for c in
                    [[{"type": "text", "text": "{\"question_number\": 1}"}], "\n"]) + "\ndata: [DONE]\n"
    transport = httpx.MockTransport(lambda r: httpx.Response(200, text=sse))
    real = httpx.Client
    with patch.object(MistralVisionParserService, "get_api_key", return_value="k"), \
            patch.object(httpx, "Client", lambda **kw: real(transport=transport)), \
            patch("app.modules.exercise.services.mistral_vision_parser_service.GeminiVisionParserService."
                  "_process_streamed_response", side_effect=lambda t, provider: t) as proc:
        from PIL import Image
        out = MistralVisionParserService.parse_images_with_mistral([Image.new("RGB", (10, 10))])
    assert proc.called and "question_number" in out


def test_400_body_logged(caplog):
    resp = httpx.Response(400, text="bad schema", request=httpx.Request("POST", "http://x"))
    with caplog.at_level("WARNING"), pytest.raises(httpx.HTTPStatusError):
        raise_for_status_logged(resp)
    assert "400" in caplog.text and "bad schema" in caplog.text


def q(n, t, exam, nopts=4):
    opts = [ParsedOption(content=x, is_correct=False, display_order=i) for i, x in enumerate("abcd"[:nopts])]
    return ParsedQuestion(question_number=n, part="P", question_type=t, difficulty=None, content="c",
                          answer_options=opts, exam_label=exam)


def test_all_exams_solved_tf_per_statement_and_flags():
    qs = [q(1, T.MultipleChoice, "E1"), q(1, T.TrueFalse, "E1"), q(1, T.MultipleChoice, "E2"),
          q(2, T.MultipleChoice, "E2", nopts=1), q(3, T.ShortAnswer, "E2", nopts=0)]

    def fake(text):
        assert "Question 4" not in text
        return json.dumps({"results": [
            {"number": 1, "answer": "B", "tf": None, "confidence": 0.9, "rationale": "r"},
            {"number": 2, "answer": None, "tf": {"a": True, "b": False, "c": True, "d": False},
             "confidence": 0.9, "rationale": "r"},
            {"number": 3, "answer": "D", "tf": None, "confidence": 0.9, "rationale": "r"}]})
    with patch.object(svc, "_chat", side_effect=fake):
        assert svc.AnswerSolverService.solve_questions(qs) == 3
    assert all(x.image_metadata["solved_by"] == "ai" for x in qs[:3])
    assert [o.is_correct for o in qs[1].answer_options] == [True, False, True, False]
    assert qs[2].correct_answer == "D"
    assert qs[3].needs_review and "option" in qs[3].image_metadata["review_reason"]
    assert not qs[4].needs_review


def test_failed_questions_retried_once():
    m = q(1, T.MultipleChoice, "E1")
    ok = json.dumps({"results": [{"number": 1, "answer": "A", "tf": None, "confidence": 0.9, "rationale": "r"}]})
    with patch.object(svc, "_chat", side_effect=["junk", "junk", ok]):
        assert svc.AnswerSolverService.solve_questions([m]) == 1
