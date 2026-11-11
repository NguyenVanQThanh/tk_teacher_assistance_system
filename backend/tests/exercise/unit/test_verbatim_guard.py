# File Name: test_verbatim_guard.py
# Description: Unit tests for the verbatim guard (text-layer vs model text).
# Created At: 2026-11-11
# Created By: AI Agent
# Updated At: 2026-11-11
# Updated By: AI Agent

import pymupdf
from types import SimpleNamespace as NS

from app.modules.exercise.services.pdf_layout_service import (
    PdfLayoutService, find_anchors, page_columns, build_regions)
from app.modules.exercise.services.verbatim_guard_service import REVIEW_REASON, flag_deviations

STEM = "Nhiet luong can cung cap de lam nong chay hoan toan mot vat ran. Biet vat dat trong binh kin"


def _layout():
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 80), "Câu 1. " + STEM)
    page.insert_text((50, 100), "A. nhiet luong thu vao   B. nhiet luong toa ra")
    words = PdfLayoutService.extract_words(doc.tobytes())
    regions = build_regions(find_anchors(words), {1: page_columns(words[1])})
    return regions, words


def _q(content, opts="nhiet luong thu vao nhiet luong toa ra"):
    return NS(question_number=1, part_index=regions_part, content=content, needs_review=False,
              image_metadata={"solved_by": "ai"}, answer_options=[NS(content=opts)])


regions_part = 0


def _run(content):
    global regions_part
    regions, words = _layout()
    regions_part = regions[0].part
    q = _q(content)
    n = flag_deviations([q], regions, words, "t")
    return q, n


def test_exact_not_flagged():
    q, n = _run(STEM)
    assert n == 0 and not q.needs_review


def test_paraphrase_flagged_and_metadata_merged():
    q, n = _run("Luong nhiet phai truyen cho chat ran de no hoa long hoan toan")
    assert n == 1 and q.needs_review
    assert q.image_metadata == {"solved_by": "ai", "review_reason": REVIEW_REASON}


def test_dropped_sentence_flagged():
    q, n = _run("Nhiet luong can cung cap")
    assert n == 1 and q.needs_review
