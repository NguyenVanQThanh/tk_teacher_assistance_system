# File Name: test_skeleton_match.py
# Description: Layout skeleton matching: essay part separate, exam boundary mid-page, duplicates, stray true/false rows, placeholders (model mocked, no network).
# Created At: 2026-11-10
# Created By: AI Agent
# Updated At: 2026-11-10
# Updated By: AI Agent

import pymupdf
from PIL import Image  # noqa: F401

from app.modules.exercise.services.gemini_vision_parser_service import GeminiVisionParserService
from app.modules.exercise.services.import_parser_service import ImportParserService
from app.modules.exercise.services.pdf_layout_service import (
    PdfLayoutService, build_regions, clip_words, find_anchors, page_columns,
)

_FONT = "C:/Windows/Fonts/arial.ttf"
LINES = [
    "ĐỀ SỐ 1",
    "PHẦN I. CÂU TRẮC NGHIỆM PHƯƠNG ÁN NHIỀU LỰA CHỌN", "Câu 1. mc one", "Câu 2. mc two",
    "PHẦN II. Thí sinh chọn đúng hoặc sai cho các ý a), b)", "Câu 1. tf one",
    "PHẦN III. Thí sinh làm từ câu 1 đến câu 2", "Câu 1. short one", "Câu 2. short two",
    "PHẦN IV. Thí sinh làm từ câu 1 đến câu 2", "Câu 1. essay one", "Câu 2. essay two",
    "ĐỀ SỐ 2",
    "PHẦN I. CÂU TRẮC NGHIỆM PHƯƠNG ÁN NHIỀU LỰA CHỌN", "Câu 1. mc one b", "Câu 2. mc two b",
]


def _pdf():
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_font(fontname="f", fontfile=_FONT)
    for i, ln in enumerate(LINES):
        page.insert_text((50, 40 + i * 40), ln, fontname="f", fontsize=11)
    return doc.tobytes()


def _item(n, qtype, content, opts=()):
    return {"question_number": n, "part": "Part1", "question_type": qtype, "content": content,
            "answer_options": [{"content": o, "is_correct": False} for o in opts], "correct_answer": None}


def _qs(items):
    return GeminiVisionParserService._build_result_from_items(items).questions


def _sections(pdf):
    secs = ImportParserService.detect_pdf_exam_sections(pdf)
    return secs


def test_skeleton_per_exam_and_part():
    pdf = _pdf()
    secs = _sections(pdf)
    assert len(secs) == 2  # exam boundary falls mid-page
    words = PdfLayoutService.extract_words(pdf)
    out = []
    for s in secs:
        w = clip_words(words, s["start"], s["end"])
        regs = build_regions(find_anchors(w), {p: page_columns(x) for p, x in w.items()}, section_end=s["end"])
        out.append({p: [r.number for r in regs if r.part == p] for p in sorted({r.part for r in regs})})
    assert out[0] == {1: [1, 2], 2: [1], 3: [1, 2], 4: [1, 2]}
    assert out[1] == {1: [1, 2]}


def test_essay_own_part_dupes_and_stray_dropped():
    pdf = _pdf()
    sec = _sections(pdf)[0]
    mc = ["A. x", "B. y", "C. z", "D. w"]
    items = [
        _item(1, "MultipleChoice", "mc one", mc), _item(2, "MultipleChoice", "mc two", mc),
        _item(1, "TrueFalse", "tf one", ["a) s1", "b) s2", "c) s3", "d) s4"]),
        _item(1, "MultipleChoice", "tf stmt typed as mc", ["a) lone"]),      # TF statement, not a skeleton item
        _item(1, "ShortAnswer", "short one"), _item(2, "ShortAnswer", "short two"),
        _item(1, "ShortAnswer", "short one"),                                 # duplicate
        _item(1, "ShortAnswer", "essay one a) p b) q"), _item(2, "ShortAnswer", "essay two a) p b) q"),
        _item(5, "ShortAnswer", "not in skeleton"),
    ]
    qs = _qs(items)
    missing = ImportParserService.relabel_by_layout(qs, pdf, sec, "ĐỀ SỐ 1")
    assert missing == []
    assert [(q.part_index, q.question_number) for q in qs] == [
        (1, 1), (1, 2), (2, 1), (3, 1), (3, 2), (4, 1), (4, 2)]
    assert [q.part for q in qs] == ["Part1", "Part1", "Part2", "Part3", "Part3", "Part4", "Part4"]
    assert len({q.content for q in qs}) == 7


def test_missing_number_reported_not_invented():
    pdf = _pdf()
    sec = _sections(pdf)[0]
    qs = _qs([_item(1, "MultipleChoice", "mc one", ["A. x", "B. y", "C. z", "D. w"])])
    missing = ImportParserService.relabel_by_layout(qs, pdf, sec, "ĐỀ SỐ 1")
    assert len(qs) == 1 and (1, 2) in {(r.part, r.number) for r, _ in missing}


def test_same_number_two_parts_matched_by_text():
    from types import SimpleNamespace as N
    from app.modules.exercise.services.exam_structure_service import match_to_skeleton, PartSpec, TYPE_SHORT, TYPE_ESSAY
    regs = [N(number=1, part=3), N(number=1, part=4)]
    specs = [PartSpec(3, "", TYPE_SHORT), PartSpec(4, "", TYPE_ESSAY)]
    q = [N(question_number=1, content="khí nhận nhiệt lượng giãn nở", answer_options=[], question_type=None),
         N(question_number=1, content="cung cấp nhiệt lượng xilanh pittông a) b) c)", answer_options=[], question_type=None)]
    text = {0: "khí nhận nhiệt lượng giãn nở".split(), 1: "cung cấp nhiệt lượng xilanh pittông".split()}
    assert match_to_skeleton(q, regs, specs, region_text=text) == {0: 0, 1: 1}


def test_best_text_match_claims_slot_first():
    from types import SimpleNamespace as N
    from app.modules.exercise.services.exam_structure_service import match_to_skeleton, PartSpec, TYPE_SHORT, TYPE_ESSAY
    regs = [N(number=1, part=3), N(number=1, part=4)]
    specs = [PartSpec(3, "", TYPE_SHORT), PartSpec(4, "", TYPE_ESSAY)]
    # stream order puts the part-4 text first; it must still take slot 1
    q = [N(question_number=1, content="cung cấp nhiệt lượng xilanh pittông", answer_options=[], question_type=None),
         N(question_number=1, content="khí nhận nhiệt lượng giãn nở", answer_options=[], question_type=None)]
    text = {0: "khí nhận nhiệt lượng giãn nở".split(), 1: "cung cấp nhiệt lượng xilanh pittông".split()}
    assert match_to_skeleton(q, regs, specs, region_text=text) == {0: 1, 1: 0}


def test_duplicate_copy_does_not_take_other_parts_slot():
    from types import SimpleNamespace as N
    from app.modules.exercise.services.exam_structure_service import match_to_skeleton, PartSpec, TYPE_SHORT, TYPE_ESSAY
    regs = [N(number=1, part=3), N(number=1, part=4)]
    specs = [PartSpec(3, "", TYPE_SHORT), PartSpec(4, "", TYPE_ESSAY)]
    a = "khí nhận nhiệt lượng giãn nở"
    q = [N(question_number=1, content=a, answer_options=[], question_type=None),
         N(question_number=1, content=a, answer_options=[], question_type=None)]
    text = {0: a.split(), 1: "cung cấp nhiệt lượng xilanh pittông".split()}
    assert list(match_to_skeleton(q, regs, specs, region_text=text).values()) == [0]
