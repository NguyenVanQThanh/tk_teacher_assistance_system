# File Name: test_vision_stream_parsing.py
# Description: Unit tests for vision OCR stream parsing (NDJSON, pretty-printed JSON, tables, no-answer-key imports).
# Created At: 2026-11-09
# Created By: AI Agent
# Updated At: 2026-11-09
# Updated By: AI Agent

import json

from app.modules.exercise.schemas import QuestionCreate, QuestionTypeEnum
from app.modules.exercise.services.gemini_vision_parser_service import GeminiVisionParserService as G

MC = {
    "question_number": 1, "part": "Part1", "question_type": "MultipleChoice",
    "content": "Cau hoi $x^2$?",
    "answer_options": [{"content": c, "is_correct": False, "display_order": i} for i, c in enumerate("ABCD")],
    "correct_answer": None,
}


def test_ndjson_response():
    other = dict(MC, question_number=2)
    raw = json.dumps(MC) + "\n" + json.dumps(other) + "\n" + '{"question_number": 3, "part": "Pa'
    res = G._process_streamed_response(raw)
    assert [q.question_number for q in res.questions] == [1, 2]


def test_pretty_printed_json_not_split_into_fake_questions():
    raw = json.dumps(MC, indent=2) + "\n" + json.dumps(dict(MC, question_number=2), indent=2)
    res = G._process_streamed_response(raw)
    assert len(res.questions) == 2
    assert all(len(q.answer_options) == 4 for q in res.questions)


def test_raw_newline_in_string_strict_false():
    raw = '{"question_number": 1, "part": "Part3", "question_type": "ShortAnswer", "content": "line1\nline2", "answer_options": []}'
    res = G._process_streamed_response(raw)
    assert len(res.questions) == 1
    assert "line2" in res.questions[0].content


def test_part2_single_object_keeps_four_statements():
    item = {
        "question_number": 1, "part": "Part2", "question_type": "TrueFalse", "content": "Stem",
        "answer_options": [{"content": f"{c}) s", "is_correct": False} for c in "abcd"],
    }
    res = G._process_streamed_response(json.dumps(item))
    assert len(res.questions) == 1
    q = res.questions[0]
    assert q.question_type == QuestionTypeEnum.TrueFalse and len(q.answer_options) == 4


def test_inline_table_becomes_segment_not_content():
    table = "| x | 1 |\n|---|---|\n| y | 2 |"
    item = dict(MC, content="Cho bang:\n" + table + "\nTinh y.")
    res = G._process_streamed_response(json.dumps(item))
    q = res.questions[0]
    assert "|" not in q.content and "|" not in (q.content_markdown or "")
    assert q.table_markdown and "---" in q.table_markdown
    assert any(s["type"] == "table" for s in q.segments)


def test_mc_without_correct_rejected_by_default_allowed_for_import():
    opts = [{"content": c, "is_correct": False, "display_order": i} for i, c in enumerate("ABCD")]
    data = {"content": "q", "question_type": "MultipleChoice", "answer_options": opts}
    try:
        QuestionCreate.model_validate(data)
        assert False, "must reject by default"
    except ValueError:
        pass
    assert QuestionCreate.model_validate(data, context={"allow_no_correct": True}).answer_options
