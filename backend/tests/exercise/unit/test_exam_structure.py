# File Name: test_exam_structure.py
# Description: Exam structure LLM pre-pass: parsing, fallback, hint injection, targeted retry, relabel by structure (LLM mocked).
# Created At: 2026-11-09
# Created By: AI Agent
# Updated At: 2026-11-09
# Updated By: AI Agent

import json
import logging

import pymupdf
import pytest
from PIL import Image

from app.modules.exercise.schemas import QuestionTypeEnum
from app.modules.exercise.services import exam_structure_service as ess
from app.modules.exercise.services.gemini_vision_parser_service import GeminiVisionParserService
from app.modules.exercise.services.import_parser_service import ImportParserService, ParseResult
from app.modules.exercise.services.pdf_layout_service import PdfLayoutService

from _font import FONT as _FONT


def _pdf(lines):
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_font(fontname="f", fontfile=_FONT)
    y = 50
    for ln in lines:
        page.insert_text((50, y), ln, fontname="f", fontsize=10)
        y += 30
    return doc.tobytes()


# Teacher layout: TF first, then MC, headings "PHẦN A/B/C" (no I/II/III)
ODD_LINES = [
    "PHẦN A. Mỗi câu chọn đúng hoặc sai cho từng ý", "Câu 1. tf stem", "a) one", "b) two",
    "PHẦN B. Chọn một phương án", "Câu 1. mc stem", "A. x", "B. y", "C. z", "D. w",
    "Câu 2. mc stem two", "A. x", "B. y", "C. z", "D. w",
    "PHẦN C. Giải chi tiết", "Câu 1. essay stem", "a) sub a", "b) sub b",
]
ODD_JSON = {"parts": [
    {"index": 1, "heading": "PHẦN A", "type": "TrueFalse", "first_question": 1, "last_question": 1,
     "question_count": 1, "has_answer_key": False, "options_per_question": 4},
    {"index": 2, "heading": "PHẦN B", "type": "MultipleChoice", "first_question": 1, "last_question": 5,
     "question_count": 5, "has_answer_key": False, "options_per_question": 4},
    {"index": 3, "heading": "PHẦN C", "type": "Essay", "first_question": 1, "last_question": 1,
     "question_count": 1, "has_answer_key": False, "options_per_question": 0},
]}


class FakeProvider:
    """Records calls; no network."""

    def __init__(self, structure_reply=None, scans=None):
        self.structure_reply = structure_reply
        self.scans = list(scans or [])
        self.json_calls, self.scan_calls = [], []

    def complete_json(self, system, user, images=None, schema=None, max_tokens=0, timeout=0):
        self.json_calls.append((system, user, schema))
        if isinstance(self.structure_reply, Exception):
            raise self.structure_reply
        return self.structure_reply

    def parse_images(self, images, test_code=None, page_numbers=None, structure_hint=None):
        self.scan_calls.append({"pages": page_numbers, "hint": structure_hint})
        return self.scans.pop(0) if self.scans else ParseResult()

    @staticmethod
    def is_available():
        return True


def _item(n, part, qtype, opts=()):
    return {"question_number": n, "part": part, "question_type": qtype, "content": f"stem {part} {n}",
            "answer_options": [{"content": o, "is_correct": False} for o in opts], "correct_answer": None}


def _layout(pdf):
    from app.modules.exercise.services.pdf_layout_service import (
        build_regions, find_anchors, find_part_headings, page_columns)
    words = PdfLayoutService.extract_words(pdf)
    regions = build_regions(find_anchors(words), {p: page_columns(w) for p, w in words.items()})
    return words, regions, find_part_headings(words)


@pytest.fixture(autouse=True)
def _clear():
    ess.clear_cache()
    yield
    ess.clear_cache()


def test_outline_has_headings_and_followers():
    words, _, _ = _layout(_pdf(ODD_LINES))
    out = ess.build_outline(words)
    assert "[HEADING] PHẦN A" in out and "[HEADING] PHẦN C" in out
    assert "follows: options A-D" in out and "follows: sub-items a-d" in out


def test_odd_layout_structure_and_layout_counts_win():
    pdf = _pdf(ODD_LINES)
    words, regions, headings = _layout(pdf)
    assert sorted(headings) == [1, 2, 3]
    prov = FakeProvider(json.dumps(ODD_JSON))
    st = ess.analyze_structure(ess.build_outline(words), prov, regions=regions, headings=headings)
    assert st.source == "llm"
    assert [p.type for p in st.parts] == ["TrueFalse", "MultipleChoice", "Essay"]
    assert st.parts[1].question_count == 2 and st.parts[1].last_question == 2  # LLM said 5, layout says 2
    assert prov.json_calls[0][2] is not None  # structured output requested


def test_invalid_json_falls_back_to_heuristic(caplog):
    pdf = _pdf(ODD_LINES)
    words, regions, headings = _layout(pdf)
    prov = FakeProvider("not json {")
    with caplog.at_level(logging.WARNING):
        st = ess.analyze_structure("outline", prov, regions=regions, headings=headings)
    assert st.source == "heuristic"
    assert len(prov.json_calls) == 2  # strict attempt + one retry
    assert any("falling back" in r.getMessage() for r in caplog.records)


def test_non_monotonic_or_bad_type_rejected():
    bad = json.loads(json.dumps(ODD_JSON))
    bad["parts"][1]["index"] = 1
    with pytest.raises(ValueError):
        ess.parse_structure(json.dumps(bad))
    bad = json.loads(json.dumps(ODD_JSON))
    bad["parts"][0]["type"] = "Weird"
    with pytest.raises(ValueError):
        ess.parse_structure(json.dumps(bad))


def test_provider_exception_falls_back():
    st = ess.analyze_structure("outline", FakeProvider(RuntimeError("boom")), headings={1: "PHẦN I. x"})
    assert st.source == "heuristic"


def test_cache_avoids_second_call():
    prov = FakeProvider(json.dumps(ODD_JSON))
    key = ("h", "ĐỀ 1")
    a = ess.analyze_structure("outline", prov, cache_key=key)
    b = ess.analyze_structure("outline", prov, cache_key=key)
    assert a is b and len(prov.json_calls) == 1


def test_relabel_uses_structure_types():
    pdf = _pdf(ODD_LINES)
    words, regions, headings = _layout(pdf)
    st = ess.analyze_structure("o", FakeProvider(json.dumps(ODD_JSON)), regions=regions, headings=headings)
    items = [
        _item(1, "Part1", "MultipleChoice", ["a) s1", "b) s2"]),      # model said MC; PHẦN A is TF
        _item(1, "Part2", "TrueFalse", ["A. x", "B. y", "C. z", "D. w"]),
        _item(2, "Part2", "TrueFalse", ["A. x", "B. y", "C. z", "D. w"]),
        _item(1, "Part2", "TrueFalse", ["a) sub a", "b) sub b"]),
    ]
    qs = GeminiVisionParserService._build_result_from_items(items).questions
    missing = ImportParserService.relabel_by_layout(qs, pdf, {"pages": [1], "start": None, "end": None}, "X", structure=st)
    assert missing == []
    assert [q.part for q in qs] == ["Part2", "Part1", "Part1", "Part4"]
    assert qs[3].question_type == QuestionTypeEnum.ShortAnswer and "sub a" in qs[3].content and not qs[3].answer_options


def test_hint_text_and_chunk_filter():
    st = ess.parse_structure(json.dumps(ODD_JSON))
    st.parts[0].pages, st.parts[1].pages, st.parts[2].pages = (1, 1), (1, 2), (3, 3)
    hint = st.to_hint([3])
    assert "PHẦN C" in hint and "PHẦN A" not in hint and "Part3" in hint
    assert "Part2" in st.to_hint([1])
    assert "câu 3, 4" in st.to_hint([1], missing={"PHẦN B": [3, 4]})


def test_parse_document_passes_hint_and_retries_once(monkeypatch):
    pdf = _pdf(ODD_LINES)
    first = ParseResult(questions=GeminiVisionParserService._build_result_from_items([
        _item(1, "Part2", "TrueFalse", ["a) s1", "b) s2"]),
        _item(1, "Part1", "MultipleChoice", ["A. x", "B. y", "C. z", "D. w"]),
        _item(1, "Part3", "ShortAnswer"),
    ]).questions)
    retry = ParseResult(questions=GeminiVisionParserService._build_result_from_items([
        _item(2, "Part1", "MultipleChoice", ["A. x", "B. y", "C. z", "D. w"]),
        _item(1, "Part1", "MultipleChoice", ["A. dup", "B. y", "C. z", "D. w"]),  # already present: must be dropped
    ]).questions)
    prov = FakeProvider(json.dumps(ODD_JSON), scans=[first, retry])
    monkeypatch.setattr(ImportParserService, "get_ai_vision_providers", staticmethod(lambda: [("Fake", prov)]))
    monkeypatch.setattr(ImportParserService, "attach_question_images", classmethod(lambda cls, *a, **k: None))
    monkeypatch.setattr(GeminiVisionParserService, "render_pdf_to_images",
                        staticmethod(lambda b, scale=3.0: [Image.new("RGB", (100, 140))]))
    res = ImportParserService.parse_document(pdf, "x.pdf")
    assert len(prov.json_calls) == 1
    assert len(prov.scan_calls) == 2  # chunk scan + exactly one retry
    assert "PHẦN B" in prov.scan_calls[0]["hint"] and "Part2" in prov.scan_calls[0]["hint"]
    assert "câu 2" in prov.scan_calls[1]["hint"] and "THIẾU" in prov.scan_calls[1]["hint"]
    keyed = [(q.part_index, q.question_number) for q in res.questions]
    assert sorted(keyed) == [(1, 1), (2, 1), (2, 2), (3, 1)]
    assert len(keyed) == len(set(keyed))


def test_sanitize_types_fixes_duplicate_truefalse_part():
    from app.modules.exercise.services.exam_structure_service import (
        ExamStructure, PartSpec, TYPE_ESSAY, TYPE_MC, TYPE_SHORT, TYPE_TF, _sanitize_types,
    )
    st = ExamStructure(parts=[
        PartSpec(1, "PHẦN I. CÂU TRẮC NGHIỆM PHƯƠNG ÁN NHIỀU LỰA CHỌN", TYPE_MC),
        PartSpec(2, "PHẦN II. Thí sinh chọn đúng hoặc sai cho các ý a), b)", TYPE_TF),
        PartSpec(3, "PHẦN III. Thí sinh làm từ câu 1 đến câu 4", TYPE_SHORT),
        PartSpec(4, "PHẦN IV. Thí sinh làm từ câu 1 đến câu 3", TYPE_TF),  # LLM slip
    ], source="llm")
    _sanitize_types(st)
    assert [p.type for p in st.parts] == [TYPE_MC, TYPE_TF, TYPE_SHORT, TYPE_ESSAY]
