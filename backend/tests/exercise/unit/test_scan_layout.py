# File Name: test_scan_layout.py
# Description: Model-read skeleton for no-text-layer PDFs: sections, regions, part types, relabel, placeholders, failure fallback (provider mocked).
# Created At: 2026-11-11
# Created By: AI Agent
# Updated At: 2026-11-11
# Updated By: AI Agent

import json

from app.modules.exercise.services import scan_layout_service as sls
from app.modules.exercise.services.gemini_vision_parser_service import GeminiVisionParserService
from app.modules.exercise.services.import_parser_service import ImportParserService

H1 = "PHẦN I. CÂU TRẮC NGHIỆM PHƯƠNG ÁN NHIỀU LỰA CHỌN"
H2 = "PHẦN II. Thí sinh chọn đúng hoặc sai cho các ý a), b)"
H3 = "PHẦN III. Thí sinh trả lời ngắn"
H4 = "PHẦN IV. Tự luận"


def _q(n, y):
    return {"number": n, "y": y, "col": 0, "snippet": f"q{n}", "follows": "none"}


PAGE1 = {"exam_headers": [{"label": "ĐỀ SỐ 1", "y": 50}],
         "parts": [{"heading": H1, "y": 100, "col": 0}, {"heading": H2, "y": 400, "col": 0},
                   {"heading": H3, "y": 600, "col": 0}, {"heading": H4, "y": 800, "col": 0}],
         "questions": [_q(1, 150), _q(2, 250), _q(3, 320), _q(1, 450), _q(1, 650), _q(1, 850)]}
PAGE2 = {"exam_headers": [{"label": "ĐỀ SỐ 2", "y": 50}],
         "parts": [{"heading": H1, "y": 100, "col": 0}],
         "questions": [_q(1, 150), _q(2, 250)]}


class _Provider:
    def __init__(self, pages):
        self.pages, self.calls = pages, 0

    def complete_json(self, *a, **k):
        r = self.pages[min(self.calls, len(self.pages) - 1)]
        self.calls += 1
        if isinstance(r, Exception):
            raise r
        return r if isinstance(r, str) else json.dumps(r)


def _layout(pages=(PAGE1, PAGE2), h="h"):
    sls.clear_cache()
    return sls.synthesize_layout(h, [object()] * len(pages), _Provider(list(pages)), ImportParserService._match_exam_label)


def _qs(nums):
    items = [{"question_number": n, "part": "Part1", "question_type": "MultipleChoice", "content": f"c{n}",
              "answer_options": [{"content": "A", "is_correct": False}, {"content": "B", "is_correct": False}],
              "correct_answer": None} for n in nums]
    return GeminiVisionParserService._build_result_from_items(items).questions


def test_sections_regions_and_parts():
    lay = _layout()
    s1, s2 = lay.sections
    assert [s["label"] for s in lay.sections] == ["ĐỀ SỐ 1", "ĐỀ SỐ 2"]
    assert s1["start"] is None and s1["end"] == (2, 35.0) and s1["pages"] == [1, 2]
    regions, headings = s1["scan_layout"]
    assert [(r.part, r.number) for r in regions] == [(1, 1), (1, 2), (1, 3), (2, 1), (3, 1), (4, 1)]
    assert sorted(headings) == [1, 2, 3, 4]
    assert [(r.part, r.number) for r in s2["scan_layout"][0]] == [(1, 1), (1, 2)]


def test_relabel_types_and_placeholder():
    s1 = _layout().sections[0]
    qs = _qs([1, 3, 1, 1, 1])  # MC 2 missing; TF/short/essay one each
    qs[2].question_type = qs[3].question_type = qs[4].question_type = qs[0].question_type
    errors = []
    ImportParserService._verify_sequence(qs, errors, b"", s1, "ĐỀ SỐ 1", None, [], None)
    got = [(q.part, q.question_number, getattr(q, "is_placeholder", False)) for q in qs]
    assert len(qs) == 6 and len(errors) == 1
    assert got[:3] == [("Part1", 1, False), ("Part3", 2, True), ("Part1", 3, False)]
    assert [g[0] for g in got[3:]] == ["Part2", "Part3", "Part4"]


def test_duplicates_keep_one():
    s1 = _layout().sections[0]
    qs = _qs([1, 1, 2, 3])
    ImportParserService.relabel_by_layout(qs, b"", s1, "ĐỀ SỐ 1")
    assert [q.question_number for q in qs if q.part_index == 1] == [1, 2, 3]


def test_failure_fallbacks():
    sls.clear_cache()
    assert sls.synthesize_layout("a", [object()], _Provider([RuntimeError("boom")])) is None
    assert sls.synthesize_layout("b", [object()], _Provider(["not json"])) is None
    assert sls.synthesize_layout("c", [object()], None) is None
    no_parts = {"exam_headers": [], "parts": [], "questions": [_q(1, 100)]}
    assert _layout([no_parts], "d") is None
    # A number going backwards is no longer rejected: it starts a synthesized part.
    regress = dict(PAGE1, questions=[_q(2, 150), _q(1, 250)])
    assert _layout([regress], "e") is not None


def test_restart_without_heading_starts_new_part():
    page = {"exam_headers": [{"label": "ĐỀ SỐ 1", "y": 50}],
            "parts": [{"heading": H1, "y": 100, "col": 0}, {"heading": H2, "y": 400, "col": 0},
                      {"heading": H3, "y": 600, "col": 0}],
            "questions": [_q(1, 150), _q(2, 250), _q(1, 450), _q(1, 650), _q(2, 700), _q(3, 750), _q(1, 850), _q(2, 900)]}
    regions, headings = _layout((page,)).sections[0]["scan_layout"]
    assert [(r.part, r.number) for r in regions][-5:] == [(3, 1), (3, 2), (3, 3), (4, 1), (4, 2)]
    assert headings[4] == ""  # synthetic heading: positional default types it as essay


def test_repeated_exam_label_then_part_one_splits_exam():
    p1 = {"exam_headers": [{"label": "ĐỀ SỐ 2", "y": 50}], "parts": [{"heading": H1, "y": 100, "col": 0},
          {"heading": H2, "y": 400, "col": 0}], "questions": [_q(1, 150), _q(1, 450)]}
    p2 = {"exam_headers": [{"label": "ĐỀ SỐ 2", "y": 50}], "parts": [{"heading": H1, "y": 100, "col": 0},
          {"heading": H2, "y": 400, "col": 0}], "questions": [_q(1, 150), _q(1, 450)]}
    assert len(_layout((p1, p2)).sections) == 2
