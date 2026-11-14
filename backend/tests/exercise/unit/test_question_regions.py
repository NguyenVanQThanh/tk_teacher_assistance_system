# File Name: test_question_regions.py
# Description: Unit tests for question anchors, regions, block assignment and the attach_question_images integration.
# Created At: 2026-11-09
# Created By: AI Agent
# Updated At: 2026-11-09
# Updated By: AI Agent

import os
from types import SimpleNamespace

import pytest

import pymupdf

from app.modules.exercise.services.import_parser_service import ImportParserService, ParsedQuestion
from app.modules.exercise.services.pdf_layout_service import (
    Block, PdfLayout, PdfLayoutService, Word, assign_blocks, build_regions, find_anchors,
    clip_words, match_questions, page_columns, pick_primary,
)
from app.modules.exercise.schemas import QuestionTypeEnum


from _font import FONT as _FONT


def _line(block, y, x, text, h=14.0, w=40.0):
    """One text line made of whitespace separated tokens."""
    words, cx = [], x
    for i, tok in enumerate(text.split()):
        words.append(Word(cx, y, cx + w, y + h, tok, block, 0, i))
        cx += w + 5
    return words


def _wide_filler(block, y):
    """Full-width line that crosses the page centre (keeps a page in 1-column mode)."""
    return [Word(50, y, 900, y + 12, "filler", block, 0, 0)]


def _blk(i, page, bbox, kind="drawing"):
    area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
    return Block(id=f"b{i}", page=page, bbox=tuple(bbox), kind=kind, area=area)


def _q(n):
    return SimpleNamespace(question_number=n)


def _regions(words_by_page):
    cols = {p: page_columns(w) for p, w in words_by_page.items()}
    return build_regions(find_anchors(words_by_page), cols), cols


def test_two_column_assignment():
    words = []
    b = 0
    for y in (100, 300, 500, 700):
        words += _line(b, y, 60, "x filler text"); b += 1
        words += _line(b, y + 20, 560, "x filler text"); b += 1
    words += _line(100, 100, 60, "Câu 1.")
    words += _line(101, 500, 60, "Câu 2.")
    words += _line(102, 100, 560, "Câu 3.")
    words += _line(103, 500, 560, "Câu 4.")
    regs, cols = _regions({1: words})
    assert cols[1] == 2
    assert [r.number for r in regs] == [1, 2, 3, 4]
    blocks = [_blk(1, 1, (80, 200, 300, 350)), _blk(2, 1, (580, 200, 800, 350)), _blk(3, 1, (80, 600, 300, 750))]
    asg = assign_blocks(regs, blocks, {1: words})
    assert [b.id for b in asg[0].stem] == ["b1"]
    assert [b.id for b in asg[1].stem] == ["b3"]
    assert [b.id for b in asg[2].stem] == ["b2"]
    assert asg[3].stem == []


def test_page_break_span():
    p1 = _wide_filler(0, 100) + _wide_filler(1, 200) + _line(2, 800, 60, "Câu 1.")
    p2 = _line(3, 100, 60, "Câu 2.") + _wide_filler(4, 300)
    regs, _ = _regions({1: p1, 2: p2})
    asg = assign_blocks(regs, [_blk(1, 2, (100, 20, 400, 80))], {1: p1, 2: p2})
    assert [b.id for b in asg[0].stem] == ["b1"]  # top of page 2 belongs to Câu 1
    assert asg[1].stem == []


def test_numbering_restart_matching():
    words = (_line(0, 100, 60, "Câu 1.") + _line(1, 200, 60, "Câu 2.") + _line(2, 300, 60, "PHẦN II.")
             + _line(3, 400, 60, "Câu 1.") + _line(4, 500, 60, "Câu 2.") + _wide_filler(5, 600))
    regs, _ = _regions({1: words})
    assert [r.number for r in regs] == [1, 2, 1, 2]
    qs = [_q(1), _q(2), _q(1), _q(2)]
    m = match_questions(regs, qs)
    assert [m[id(q)].anchor.y for q in qs] == [r.anchor.y for r in regs]


def test_inline_reference_and_answer_key_row_make_no_anchors():
    words = (_line(0, 100, 60, "Xét theo câu 3 ở trên") + _line(1, 150, 60, "Câu 1 2 3 4 5")
             + _line(2, 200, 60, "Theo Câu 3 thì") + _wide_filler(3, 300))
    assert find_anchors({1: words}) == []


def test_glued_anchor_and_monotonic_filter():
    words = (_line(0, 100, 60, "Câu12: abc") + _line(1, 200, 60, "Câu 1. abc") + _line(2, 300, 60, "Câu 2. abc")
             + _line(3, 400, 60, "Câu 9. abc") + _wide_filler(4, 500))
    nums = [a.number for a in find_anchors({1: words})]
    assert nums == [1, 2]  # Câu12 (not 1/last+1) and Câu 9 (jump) dropped


def test_adjacent_questions_get_distinct_figures():
    words = _line(0, 100, 60, "Câu 1.") + _line(1, 400, 60, "Câu 2.") + _wide_filler(2, 700)
    regs, _ = _regions({1: words})
    blocks = [_blk(1, 1, (100, 150, 300, 300)), _blk(2, 1, (100, 450, 300, 600))]
    asg = assign_blocks(regs, blocks, {1: words})
    assert [b.id for b in asg[0].stem] == ["b1"]
    assert [b.id for b in asg[1].stem] == ["b2"]


def test_option_figures_separated():
    words = (_line(0, 100, 60, "Câu 1.") + _wide_filler(1, 150)
             + [Word(60, 400, 80, 414, "A.", 5, 0, 0), Word(560, 400, 580, 414, "B.", 5, 0, 1)]
             + _wide_filler(2, 800))
    regs, _ = _regions({1: words})
    stem = _blk(1, 1, (100, 200, 300, 350))
    opt_a = _blk(2, 1, (90, 380, 250, 480))
    opt_b = _blk(3, 1, (590, 380, 750, 480))
    asg = assign_blocks(regs, [stem, opt_a, opt_b], {1: words})
    assert [b.id for b in asg[0].stem] == ["b1"]
    assert asg[0].options == {"A": opt_a, "B": opt_b}


def test_pick_primary():
    a = _blk(1, 1, (0, 0, 100, 100))
    b = _blk(2, 1, (200, 0, 500, 300))
    assert pick_primary([a], 1, None) is a
    assert pick_primary([a, b], 1, (0, 0, 110, 110)) is a  # IoU wins over area
    assert pick_primary([a, b], 1, None) is b  # largest area
    assert pick_primary([a, b], 2, (0, 0, 110, 110)) is b  # LLM page mismatch -> largest
    assert pick_primary([], 1, None) is None


def test_no_words_means_no_text_layout():
    doc = pymupdf.open()
    page = doc.new_page()
    page.draw_rect(pymupdf.Rect(100, 100, 300, 300), color=(0, 0, 0))
    layout = PdfLayoutService.analyze(doc.tobytes())
    assert not layout.has_text and layout.has_blocks
    assert not PdfLayout().has_text
    assert find_anchors({}) == []


def _parsed(n):
    return ParsedQuestion(question_number=n, part="Part1", question_type=QuestionTypeEnum.MultipleChoice
                          if hasattr(QuestionTypeEnum, "MultipleChoice") else list(QuestionTypeEnum)[0],
                          difficulty=None, content=f"Câu {n}")


def test_attach_question_images_distinct_crops(monkeypatch):
    colors = {1: (255, 0, 0), 2: (0, 255, 0), 3: (0, 0, 255)}

    def png(c):
        pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 120, 90), False)
        pix.set_rect(pix.irect, c)
        return pix.tobytes("png")

    doc = pymupdf.open()
    p1 = doc.new_page(width=600, height=800)
    p1.insert_text((60, 80), "Câu 1: Cho hình vẽ bên.", fontsize=11)
    p1.insert_image(pymupdf.Rect(100, 100, 300, 200), stream=png(colors[1]))
    p1.insert_text((60, 300), "Câu 2: Cho hình vẽ bên.", fontsize=11)
    p1.insert_image(pymupdf.Rect(100, 320, 300, 420), stream=png(colors[2]))
    p2 = doc.new_page(width=600, height=800)
    p2.insert_text((60, 80), "Câu 3: Cho hình vẽ bên.", fontsize=11)
    p2.insert_image(pymupdf.Rect(100, 100, 300, 200), stream=png(colors[3]))
    data = doc.tobytes()

    saved = []

    def fake_save(img_bytes, ext="png", original_name="image", content_type=None):
        saved.append((original_name, img_bytes))
        return {"url": f"/img/{len(saved)}", "name": original_name}

    from app.modules.exercise.services.question_image_service import QuestionImageService
    monkeypatch.setattr(QuestionImageService, "save_image_bytes", staticmethod(fake_save))

    qs = [_parsed(1), _parsed(2), _parsed(3)]
    # Wrong LLM boxes must not matter when layout is available.
    qs[0].image_page, qs[0].image_bbox = 1, [0, 0, 1000, 1000]
    ImportParserService.attach_question_images(data, qs)

    urls = [q.image_url for q in qs]
    assert all(urls) and len(set(urls)) == 3
    for q, n in zip(qs, (1, 2, 3)):
        crop = pymupdf.Pixmap(saved[int(q.image_url.rsplit("/", 1)[1]) - 1][1])
        r, g, b = crop.pixel(crop.width // 2, crop.height // 2)[:3]
        assert (r, g, b) == colors[n]


def test_part_tracking_and_loose_numbering():
    words = (_line(0, 100, 60, "PHẦN I. Trắc nghiệm") + _line(1, 150, 60, "Câu 1.") + _line(2, 250, 60, "Câu 2.")
             + _line(3, 350, 60, "PHẦN II. Đúng sai") + _line(4, 400, 60, "Câu 1.") + _line(5, 500, 60, "Câu 2.")
             + _line(6, 600, 60, "Phần III. Trả lời ngắn") + _line(7, 650, 60, "Câu 1.") + _wide_filler(8, 800))
    anchors = find_anchors({1: words})
    assert [(a.part, a.number) for a in anchors if a.number] == [(1, 1), (1, 2), (2, 1), (2, 2), (3, 1)]


def test_match_by_part_when_model_skips_a_question():
    words = (_line(0, 100, 60, "PHẦN I.") + _line(1, 150, 60, "Câu 1.") + _line(2, 250, 60, "Câu 2.")
             + _line(3, 350, 60, "PHẦN II.") + _line(4, 400, 60, "Câu 1.") + _line(5, 500, 60, "Câu 2.") + _wide_filler(6, 800))
    regs, _ = _regions({1: words})
    mk = lambda n, part: SimpleNamespace(question_number=n, part=part)
    qs = [mk(1, "Part1"), mk(1, "Part2"), mk(2, "Part2")]  # model dropped Part1 Câu 2
    m = match_questions(regs, qs)
    assert [(m[id(q)].part, m[id(q)].number) for q in qs] == [(1, 1), (2, 1), (2, 2)]


def test_exam_header_resets_part_and_numbering():
    w1 = _line(0, 100, 60, "PHẦN I.") + _line(1, 150, 60, "Câu 1.") + _line(2, 250, 60, "Câu 2.") + _wide_filler(3, 400)
    w2 = _line(4, 100, 224, "ĐỀ SỐ 2") + _line(5, 150, 60, "PHẦN I.") + _line(6, 200, 60, "Câu 1.") + _wide_filler(7, 400)
    anchors = find_anchors({1: w1, 2: w2})
    assert [(a.page, a.part, a.number) for a in anchors if a.number] == [(1, 1, 1), (1, 1, 2), (2, 1, 1)]


def test_clip_words_and_last_region_flows_to_section_end():
    p3 = (_wide_filler(0, 100) + _line(1, 300, 60, "Câu 1.") + _wide_filler(2, 500)
          + _line(3, 920, 224, "ĐỀ SỐ 2"))
    p4 = _line(4, 100, 60, "Câu 1.") + _wide_filler(5, 300)
    p5 = _wide_filler(6, 100)
    allw = {3: p3, 4: p4, 5: p5}
    # Section 1 ends at (3, 900): the header (y=920) is excluded, Câu 3 owns the rest of page 3.
    sec1 = clip_words(allw, None, (3, 900))
    assert set(sec1) == {3} and all(w.y0 < 900 for w in sec1[3])
    regs = build_regions(find_anchors(sec1), {3: 1}, section_end=(3, 900))
    assert regs[0].rects == ((3, 0.0, 292.0, 1000.0, 900.0),)
    # Section 2 starts at (3, 900): only the header remains on page 3; Câu 1 flows to page 5.
    sec2 = clip_words(allw, (3, 900), None)
    assert [w.text for w in sec2[3]] == ["ĐỀ", "SỐ", "2"]
    regs2 = build_regions(find_anchors(sec2), {3: 1, 4: 1, 5: 1}, section_end=None)
    assert {r[0] for r in regs2[0].rects} == {4, 5}


@pytest.mark.skipif(not os.path.exists(_FONT), reason="needs a Unicode TTF font")
def test_section_detection_by_y():
    doc = pymupdf.open()
    kw = dict(fontname="ar", fontfile=_FONT)
    for i in range(3):
        doc.new_page(width=600, height=800)
    doc[0].insert_text((200, 60), "ĐỀ SỐ 1", fontsize=12, **kw)
    doc[0].insert_text((60, 120), "Câu 1: abc", fontsize=11, **kw)
    doc[1].insert_text((60, 120), "Câu 2: abc", fontsize=11, **kw)
    doc[1].insert_text((200, 740), "ĐỀ SỐ 2", fontsize=12, **kw)  # header at the bottom of page 2
    doc[2].insert_text((60, 120), "Câu 1: abc", fontsize=11, **kw)
    secs = ImportParserService.detect_pdf_exam_sections(doc.tobytes())
    assert [s["label"] for s in secs] == ["ĐỀ SỐ 1", "ĐỀ SỐ 2"]
    assert secs[0]["pages"] == [1, 2] and secs[1]["pages"] == [2, 3]
    assert secs[0]["end"][0] == 2 and 880 < secs[0]["end"][1] < 940
    assert secs[1]["start"] == secs[0]["end"]
    # Slices: exam 1 loses the bottom of page 2, exam 2 keeps only a header sliver there.
    top, bottom = ImportParserService._page_slice(secs[0], 2)
    assert (top, bottom) == (0.0, secs[0]["end"][1])
    assert ImportParserService._page_slice(secs[1], 2)[0] == secs[0]["end"][1]


def test_exam_label_variants():
    m = ImportParserService._match_exam_label
    assert m("ĐỀ THI 3 - Vật lí") == "ĐỀ THI 3"
    assert m("Đề số 2") == "ĐỀ SỐ 2"
    assert m("ĐỀ 4") == "ĐỀ 4"
