# File Name: test_exam_sequence.py
# Description: Tests for chunk overlap, sub-item merge, dedupe, gap detection, gap retry and placeholders (no network).
# Created At: 2026-11-10
# Created By: AI Agent
# Updated At: 2026-11-10
# Updated By: AI Agent

from unittest.mock import patch

from app.modules.exercise.schemas import QuestionTypeEnum
from app.modules.exercise.services import exam_sequence_service as seq
from app.modules.exercise.services.gemini_vision_parser_service import GeminiVisionParserService
from app.modules.exercise.services.import_parser_service import (
    ImportParserService, ParsedOption, ParsedQuestion, ParseResult,
)
from app.modules.exercise.services.mistral_vision_parser_service import (
    DEFAULT_MISTRAL_MODEL, MISTRAL_PROMPT_ADDENDUM, MistralVisionParserService,
)
from test_part_relabel import _item, _pdf


def _qs(items):
    return GeminiVisionParserService._build_result_from_items(items).questions


def test_chunks_overlap_by_one_page():
    assert seq.chunk_pages([1, 2, 3, 4], 2) == [[1, 2], [2, 3], [3, 4]]
    assert seq.chunk_pages([1, 2], 2) == [[1, 2]]


def test_default_model_not_pixtral():
    assert "pixtral" not in DEFAULT_MISTRAL_MODEL
    assert "MỘT câu duy nhất" in MISTRAL_PROMPT_ADDENDUM


def test_merge_stray_true_false_rows():
    tf = _item(2, "Part2", "TrueFalse", ["a) s1", "b) s2"])
    stray = [_item(3, "Part2", "TrueFalse", ["c) s3"]), _item(4, "Part3", "ShortAnswer")]
    stray[1]["content"] = "d) s4"
    out = seq.merge_stray_true_false(_qs([tf] + stray))
    assert len(out) == 1 and len(out[0].answer_options) == 4


def test_dedupe_identical_stems():
    a = _item(1, "Part1", "MultipleChoice", ["A", "B", "C", "D"])
    out = seq.normalize_questions(_qs([a, dict(a), _item(2, "Part1", "MultipleChoice", ["A", "B", "C", "D"])]))
    assert len(out) == 2


def test_find_output_gaps():
    qs = _qs([_item(1, "Part1", "MultipleChoice"), _item(4, "Part1", "MultipleChoice"),
              _item(1, "Part3", "ShortAnswer"), _item(3, "Part3", "ShortAnswer")])
    assert sorted(n for _, n in seq.find_output_gaps(qs)) == [2, 2, 3]


def _section():
    return {"label": "X", "pages": [1], "start": None, "end": None}


def test_gap_placeholder_when_retry_fails_and_retry_limited():
    pdf = _pdf()  # 2 MC, 1 TF, 2 short, 2 essay; model returns only MC 1
    qs = _qs([_item(1, "Part1", "MultipleChoice", ["A", "B", "C", "D"])])
    errors = []
    calls = []

    class Prov:
        @staticmethod
        def parse_images(images, **kw):
            calls.append(kw)
            return ParseResult()

    from app.modules.exercise.services.exam_structure_service import heuristic_structure
    from app.modules.exercise.services.pdf_layout_service import (
        PdfLayoutService, find_anchors, find_part_headings, build_regions, page_columns,
    )
    words = PdfLayoutService.extract_words(pdf)
    regions = build_regions(find_anchors(words), {1: page_columns(words[1])})
    structure = heuristic_structure(find_part_headings(words), regions)
    structure.parts and [setattr(p, "pages", (1, 1)) for p in structure.parts]
    with patch.object(ImportParserService, "get_ai_vision_providers", return_value=[("M", Prov)]), \
            patch.object(ImportParserService, "_section_images", return_value=[object()]), \
            patch.object(ImportParserService, "_slice_pages", return_value=[1]):
        ImportParserService._verify_sequence(qs, errors, pdf, _section(), "X", structure, [object()], None)
    assert len(calls) == 3  # max 3 attempts
    placeholders = [q for q in qs if getattr(q, "is_placeholder", False)]
    assert len(placeholders) == 6 and all(q.needs_review for q in placeholders)
    assert placeholders[0].content.startswith("[Missing question")
    assert len(errors) == 6
    assert [q.part_index for q in qs] == sorted(q.part_index for q in qs)


def test_gap_retry_recovers_missing_question():
    pdf = _pdf()
    full = [
        _item(1, "Part1", "MultipleChoice", ["A", "B", "C", "D"]),
        _item(1, "Part2", "TrueFalse", ["a) s1", "b) s2", "c) s3", "d) s4"]),
        _item(1, "Part3", "ShortAnswer"), _item(2, "Part3", "ShortAnswer"),
        _item(1, "Part2", "TrueFalse"), _item(2, "Part2", "TrueFalse"),
    ]
    qs = _qs(full)
    missing_q = _qs([_item(2, "Part1", "MultipleChoice", ["A", "B", "C", "D"])])[0]
    missing_q.content = "recovered"
    seen = []

    class Prov:
        @staticmethod
        def parse_images(images, **kw):
            seen.append(kw.get("structure_hint"))
            return ParseResult(questions=[missing_q])

    from app.modules.exercise.services.exam_structure_service import heuristic_structure
    from app.modules.exercise.services.pdf_layout_service import (
        PdfLayoutService, find_anchors, find_part_headings, build_regions, page_columns,
    )
    words = PdfLayoutService.extract_words(pdf)
    regions = build_regions(find_anchors(words), {1: page_columns(words[1])})
    structure = heuristic_structure(find_part_headings(words), regions)
    [setattr(p, "pages", (1, 1)) for p in structure.parts]
    with patch.object(ImportParserService, "get_ai_vision_providers", return_value=[("M", Prov)]), \
            patch.object(ImportParserService, "_section_images", return_value=[object()]), \
            patch.object(ImportParserService, "_slice_pages", return_value=[1]):
        ImportParserService._verify_sequence(qs, [], pdf, _section(), "X", structure, [object()], None)
    assert any(q.content == "recovered" for q in qs)
    assert "2" in seen[0]  # hint asks for the missing number


def test_section_based_typing_ignores_model_label():
    pdf = _pdf()
    qs = _qs([_item(1, "Part3", "ShortAnswer", ["A. x", "B. y", "C. z", "D. w"])])  # figure q typed wrongly
    ImportParserService.relabel_by_layout(qs, pdf, _section(), "X")
    assert qs[0].question_type == QuestionTypeEnum.MultipleChoice


def test_mistral_ocr_first_off_by_default(monkeypatch):
    monkeypatch.delenv("SCAN_OCR_FIRST", raising=False)
    assert MistralVisionParserService.ocr_first_enabled() is False
