# File Name: test_pdf_layout_service.py
# Description: Unit tests for PdfLayoutService block detection and clip rendering using in-memory PDFs.
# Created At: 2026-11-09
# Created By: AI Agent
# Updated At: 2026-11-09
# Updated By: AI Agent

import pymupdf
import pytest

from app.modules.exercise.services.pdf_layout_service import PdfLayoutService


def _png(w=200, h=150, color=(200, 30, 30)) -> bytes:
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, w, h), False)
    pix.set_rect(pix.irect, color)
    return pix.tobytes("png")


def _doc_bytes(builder, rotation=0, width=600, height=800) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=width, height=height)
    builder(page)
    if rotation:
        page.set_rotation(rotation)
    data = doc.tobytes()
    doc.close()
    return data


def _triangle(page, x=100, y=300, s=120):
    page.draw_polyline([(x, y + s), (x + s, y + s), (x + s / 2, y), (x, y + s)], color=(0, 0, 0), width=1.5)


def test_embedded_image_bbox():
    data = _doc_bytes(lambda p: p.insert_image(pymupdf.Rect(100, 100, 300, 250), stream=_png()))
    blocks = PdfLayoutService.extract_blocks(data)
    assert len(blocks) == 1 and blocks[0].kind == "image"
    x0, y0, x1, y1 = blocks[0].bbox
    assert (x0, y0, x1, y1) == pytest.approx((166.7, 125.0, 500.0, 312.5), abs=1.5)


def test_vector_triangle_detected():
    data = _doc_bytes(_triangle)
    blocks = PdfLayoutService.extract_blocks(data)
    assert len(blocks) == 1 and blocks[0].kind == "drawing"


def test_line_noise_dropped():
    def build(p):
        p.draw_line((50, 100), (550, 100), width=1)  # thin horizontal rule
        p.draw_line((50, 120), (550, 121), width=1)

    assert PdfLayoutService.extract_blocks(_doc_bytes(build)) == []


def test_adjacent_drawings_merged_and_label_absorbed():
    def build(p):
        p.draw_rect(pymupdf.Rect(100, 300, 180, 380), color=(0, 0, 0))
        p.draw_rect(pymupdf.Rect(184, 300, 264, 380), color=(0, 0, 0))
        p.insert_text((100, 303), "A", fontsize=8)  # short label hugging the top edge

    blocks = PdfLayoutService.extract_blocks(_doc_bytes(build))
    assert len(blocks) == 1
    # label absorbed: block top is above the rect top (300/800*1000 = 375)
    assert blocks[0].bbox[1] < 374


def test_two_columns_not_merged():
    def build(p):
        p.draw_rect(pymupdf.Rect(60, 300, 290, 400), color=(0, 0, 0), width=1)
        p.draw_rect(pymupdf.Rect(300, 300, 540, 400), color=(0, 0, 0), width=1)

    blocks = PdfLayoutService.extract_blocks(_doc_bytes(build))
    assert len(blocks) == 2


def test_table_grid_single_table_block():
    def build(p):
        x0, y0, cw, rh = 100, 200, 100, 30
        for r in range(3):
            for c in range(3):
                p.draw_rect(pymupdf.Rect(x0 + c * cw, y0 + r * rh, x0 + (c + 1) * cw, y0 + (r + 1) * rh), width=1)
                p.insert_text((x0 + c * cw + 10, y0 + r * rh + 20), f"{r}{c}", fontsize=10)

    blocks = PdfLayoutService.extract_blocks(_doc_bytes(build))
    assert [b.kind for b in blocks] == ["table"]


@pytest.mark.parametrize("rotation", [90, 180, 270])
def test_rotation_bbox_and_render(rotation):
    # Red image placed at the top-left of the unrotated page.
    data = _doc_bytes(lambda p: p.insert_image(pymupdf.Rect(50, 50, 250, 200), stream=_png()), rotation=rotation)
    blocks = PdfLayoutService.extract_blocks(data)
    assert len(blocks) == 1
    doc = pymupdf.open(stream=data, filetype="pdf")
    page = doc[0]
    expected = pymupdf.Rect(50, 50, 250, 200) * page.rotation_matrix
    expected.normalize()
    pr = page.rect
    exp = (expected.x0 / pr.width * 1000, expected.y0 / pr.height * 1000,
           expected.x1 / pr.width * 1000, expected.y1 / pr.height * 1000)
    doc.close()
    assert blocks[0].bbox == pytest.approx(exp, abs=1.5)

    png = PdfLayoutService.render_clip(data, 1, blocks[0].bbox, dpi=100, pad=0.0)
    pix = pymupdf.Pixmap(png)
    assert pix.width > 10 and pix.height > 10
    # Center pixel is the red image, not white.
    cx, cy = pix.width // 2, pix.height // 2
    r, g, b = pix.pixel(cx, cy)[:3]
    assert r > 150 and g < 100 and b < 100
    # Image is 200x150 pt; 90/270 rotation swaps it to 150x200 in display space.
    ratio = pix.width / pix.height
    assert ratio == pytest.approx(150 / 200 if rotation in (90, 270) else 200 / 150, abs=0.05)


def test_full_page_scan_ignored():
    data = _doc_bytes(lambda p: p.insert_image(p.rect, stream=_png(600, 800, (240, 240, 240))))
    assert PdfLayoutService.extract_blocks(data) == []


def test_render_clip_dpi_size():
    data = _doc_bytes(_triangle)
    bbox = (0.0, 0.0, 500.0, 500.0)  # 300 x 400 pt
    p100 = pymupdf.Pixmap(PdfLayoutService.render_clip(data, 1, bbox, dpi=100, pad=0.0))
    p200 = pymupdf.Pixmap(PdfLayoutService.render_clip(data, 1, bbox, dpi=200, pad=0.0))
    assert p100.width == pytest.approx(300 / 72 * 100, abs=2)
    assert p200.width == pytest.approx(2 * p100.width, abs=3)


def test_render_clip_dpi_fallback_on_size(monkeypatch):
    import app.core.config as cfg
    data = _doc_bytes(lambda p: p.insert_image(pymupdf.Rect(0, 0, 600, 800), stream=_png(300, 400)))
    full = PdfLayoutService.render_clip(data, 1, (0, 0, 1000, 1000), dpi=250, pad=0.0)
    monkeypatch.setattr(cfg, "QUESTION_IMAGE_MAX_BYTES", len(full) - 1)
    smaller = PdfLayoutService.render_clip(data, 1, (0, 0, 1000, 1000), dpi=250, pad=0.0)
    if smaller is not None:
        assert pymupdf.Pixmap(smaller).width < pymupdf.Pixmap(full).width


def test_bad_pdf_returns_empty():
    assert PdfLayoutService.extract_blocks(b"not a pdf") == []


# --------------------------------------------------------------------------- block quality fixes

def test_pagewide_hairline_not_merged_into_figure():
    def build(p):
        p.draw_line((30, 30), (570, 30), width=0.5)  # header rule across the page
        p.draw_rect(pymupdf.Rect(350, 25, 520, 160), color=(0, 0, 0), width=1)  # graph touching the rule

    blocks = PdfLayoutService.extract_blocks(_doc_bytes(build))
    assert len(blocks) == 1
    assert blocks[0].bbox[0] > 500  # not stretched to the page width


def test_table_growth_capped():
    def build(p):
        x0, y0, cw, rh = 60, 200, 60, 25
        for r in range(3):
            for c in range(3):
                p.draw_rect(pymupdf.Rect(x0 + c * cw, y0 + r * rh, x0 + (c + 1) * cw, y0 + (r + 1) * rh), width=1)
                p.insert_text((x0 + c * cw + 10, y0 + r * rh + 17), f"{r}{c}", fontsize=10)
        # Wide drawing touching the table's right edge must not be absorbed.
        p.draw_rect(pymupdf.Rect(x0 + 3 * cw, y0 + 10, 560, y0 + 70), color=(0, 0, 0), width=1)

    blocks = PdfLayoutService.extract_blocks(_doc_bytes(build))
    table = [b for b in blocks if b.kind == "table"]
    assert len(table) == 1 and table[0].bbox[2] < 500


def test_inline_formula_images_rejected():
    def build(p):
        p.insert_text((60, 200), "Gia tri cua bieu thuc", fontsize=11)
        p.insert_image(pymupdf.Rect(190, 188, 300, 205), stream=_png(110, 17))  # short inline image
        p.insert_text((60, 300), "Cho", fontsize=11)
        p.insert_image(pymupdf.Rect(90, 280, 200, 310), stream=_png(110, 30))  # taller, text to its left
        p.insert_image(pymupdf.Rect(100, 400, 300, 520), stream=_png(200, 120))  # real figure

    blocks = PdfLayoutService.extract_blocks(_doc_bytes(build))
    assert len(blocks) == 1 and blocks[0].bbox[1] > 480


def test_option_figure_image_kept():
    def build(p):
        p.insert_text((60, 300), "A.", fontsize=11)
        p.insert_image(pymupdf.Rect(85, 290, 200, 312), stream=_png(115, 22))

    blocks = PdfLayoutService.extract_blocks(_doc_bytes(build))
    assert len(blocks) == 1
