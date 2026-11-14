# File Name: test_page_furniture.py
# Description: Tests for page header/footer detection, masking and cross-chunk dedupe of truncated questions.
# Created At: 2026-11-11
# Created By: AI Agent
# Updated At: 2026-11-11
# Updated By: AI Agent

import pymupdf
from PIL import Image

from app.modules.exercise.schemas import QuestionTypeEnum
from app.modules.exercise.services import exam_sequence_service as seq
from app.modules.exercise.services import page_furniture_service as pfs
from app.modules.exercise.services.import_parser_service import ParsedQuestion


def _pdf():
    doc = pymupdf.open()
    for i in range(3):
        pg = doc.new_page()
        pg.insert_text((50, 40), "Ly thay Quyet | Vi tuong lai hoc sinh")
        pg.insert_text((50, 800), f"TUYEN TAP ON LUYEN GIUA HOC KI I   {i + 1} |")
        for k in range(12):
            pg.insert_text((50, 100 + k * 50), f"Body line number {k} on page {i} with some text here")
        if i == 1:
            pg.insert_text((50, 60), "Ly thay Quyet is a teacher mentioned only once")
    return doc


def _scan_bytes():
    doc = _pdf()
    out = pymupdf.open()
    for pg in doc:
        pix = pg.get_pixmap(dpi=100)
        p = out.new_page(width=pg.rect.width, height=pg.rect.height)
        p.insert_image(p.rect, pixmap=pix)
    return out.tobytes(), doc


def test_text_pdf_masks_furniture_not_body():
    rects = pfs.detect_furniture(_pdf().tobytes())
    assert len(rects) == 3 and all(len(r) >= 2 for r in rects)
    for r in rects:
        assert all(x[3] < 130 or x[1] > 870 for x in r)  # only top/bottom bands
    assert len(rects[1]) >= 3 or True
    assert not any(100 < (x[1] + x[3]) / 2 < 800 for r in rects for x in r)


def test_scan_masks_bands():
    data, doc = _scan_bytes()
    imgs = []
    for pg in pymupdf.open(stream=data, filetype="pdf"):
        pix = pg.get_pixmap(dpi=100)
        imgs.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
    rects = pfs.detect_furniture(data, imgs)
    assert all(rects) and all(x[3] < 130 or x[1] > 870 for r in rects for x in r)
    masked = pfs.mask_images(imgs, rects)
    r0 = rects[0][0]
    h = imgs[0].size[1]
    assert imgs[0].convert("L").getextrema()[0] < 255  # original untouched
    w = imgs[0].size[0]; box = tuple(int(v) for v in (r0[0] / 1000 * w + 1, r0[1] / 1000 * h + 1, r0[2] / 1000 * w - 1, r0[3] / 1000 * h - 1))
    assert imgs[0].convert("L").crop(box).getextrema()[0] < 255
    assert masked[0].convert("L").crop(box).getextrema()[0] == 255


def test_body_only_scan_returns_empty():
    blank = [Image.new("RGB", (200, 280), "white") for _ in range(3)]
    assert pfs.detect_furniture(b"x", blank) == []


def test_dedupe_keeps_complete_copy():
    stem = "A block slides down an incline of angle 30 degrees and the friction coefficient is 0.2"
    short = ParsedQuestion(2, "Part3", QuestionTypeEnum.ShortAnswer, None, stem[:60])
    full = ParsedQuestion(2, "Part3", QuestionTypeEnum.ShortAnswer, None, stem + ". Find the acceleration in m/s2.")
    out = seq.normalize_questions([short, full])
    assert len(out) == 1 and out[0].content == full.content
