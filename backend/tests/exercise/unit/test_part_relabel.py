# File Name: test_part_relabel.py
# Description: Deterministic part/type/order relabeling of vision output from PDF PHAN headings.
# Created At: 2026-11-09
# Created By: AI Agent
# Updated At: 2026-11-09
# Updated By: AI Agent

import logging

import pymupdf

from app.modules.exercise.schemas import QuestionTypeEnum
from app.modules.exercise.services.gemini_vision_parser_service import GeminiVisionParserService
from app.modules.exercise.services.import_parser_service import ImportParserService
from app.modules.exercise.services.pdf_layout_service import (
    PART_ESSAY, PART_MC, PART_SHORT, PART_TF, classify_part, find_part_headings,
)

from _font import FONT as _FONT


def _pdf() -> bytes:
    lines = [
        "PHẦN I. CÂU TRẮC NGHIỆM PHƯƠNG ÁN NHIỀU LỰA CHỌN", "Câu 1. mc one", "Câu 2. mc two",
        "PHẦN II. Thí sinh chọn đúng hoặc sai cho các ý a), b)", "Câu 1. tf one",
        "PHẦN III. Thí sinh làm từ câu 1 đến câu 2", "Câu 1. short one", "Câu 2. short two",
        "PHẦN IV. Thí sinh làm từ câu 1 đến câu 2", "Câu 1. essay one", "Câu 2. essay two",
    ]
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_font(fontname="f", fontfile=_FONT)
    y = 60
    for ln in lines:
        page.insert_text((50, y), ln, fontname="f", fontsize=11)
        y += 40
    return doc.tobytes()


def _item(n, part, qtype, opts=()):
    return {"question_number": n, "part": part, "question_type": qtype, "content": f"stem {part} {n}",
            "answer_options": [{"content": o, "is_correct": False} for o in opts], "correct_answer": None}


def _buggy_model_output():
    return [
        _item(1, "Part1", "MultipleChoice", ["A. x", "B. y", "C. z", "D. w"]),
        _item(2, "Part1", "MultipleChoice", ["A. x", "B. y", "C. z", "D. w"]),
        _item(1, "Part2", "TrueFalse", ["a) s1", "b) s2"]),
        _item(1, "Part3", "ShortAnswer"),
        _item(2, "Part3", "ShortAnswer"),
        # PHẦN IV mislabelled as Part2 / TrueFalse by the model
        _item(1, "Part2", "TrueFalse", ["a) sub a", "b) sub b"]),
        _item(2, "Part2", "TrueFalse", ["a) sub a2", "b) sub b2"]),
    ]


def test_classify_part():
    assert classify_part("PHẦN II. chọn đúng hoặc sai", 2) == PART_TF
    assert classify_part("PHẦN I. TRẮC NGHIỆM NHIỀU LỰA CHỌN", 1) == PART_MC
    assert classify_part("PHẦN III. Trả lời ngắn", 3) == PART_SHORT
    assert classify_part("PHẦN IV. Thí sinh làm từ câu 1 đến câu 3", 4) == PART_ESSAY
    assert classify_part("PHẦN III. Thí sinh làm từ câu 1 đến câu 4", 3) == PART_SHORT


def test_find_part_headings():
    words = ImportParserService  # noqa: F841 - keep import used
    from app.modules.exercise.services.pdf_layout_service import PdfLayoutService
    heads = find_part_headings(PdfLayoutService.extract_words(_pdf()))
    assert sorted(heads) == [1, 2, 3, 4]
    assert "đúng" in heads[2]


def test_part4_mislabelled_part2_is_relabelled_and_ordered(caplog):
    pdf = _pdf()
    result = GeminiVisionParserService._build_result_from_items(_buggy_model_output())
    qs = result.questions
    section = {"label": "ĐỀ SỐ 1", "pages": [1], "start": None, "end": None}
    ImportParserService.relabel_by_layout(qs, pdf, section, "ĐỀ SỐ 1")
    assert [q.part_index for q in qs] == [1, 1, 2, 3, 3, 4, 4]
    last = qs[-2:]
    assert all(q.question_type == QuestionTypeEnum.ShortAnswer and q.part in ("Part3", "Part4") for q in last)
    assert all(not q.answer_options and q.correct_answer is None for q in last)
    assert "a) sub a" in last[0].content and "b) sub b" in last[0].content
    assert qs[2].question_type == QuestionTypeEnum.TrueFalse and len(qs[2].answer_options) == 2
    assert all(q.doc_ordered for q in qs)


def test_document_order_not_interleaved_by_part():
    pdf = _pdf()
    items = _buggy_model_output()
    result = GeminiVisionParserService._build_result_from_items(items)
    # The raw build must keep stream order (no part-based interleaving).
    assert [q.content for q in result.questions] == [i["content"] for i in items]
    ImportParserService.relabel_by_layout(result.questions, pdf, {"pages": [1], "start": None, "end": None})
    assert [q.part_index for q in result.questions] == sorted(q.part_index for q in result.questions)


def test_count_mismatch_warning(caplog):
    pdf = _pdf()
    items = _buggy_model_output()[:-1]  # essay Câu 2 missing
    qs = GeminiVisionParserService._build_result_from_items(items).questions
    with caplog.at_level(logging.WARNING):
        ImportParserService.relabel_by_layout(qs, pdf, {"label": "X", "pages": [1], "start": None, "end": None}, "X")
    assert any("expected 2 questions in PHẦN 4, got 1" in r.getMessage() for r in caplog.records)
