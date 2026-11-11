# File Name: test_figure_refine.py
# Description: Unit tests for PdfLayoutService.refine_bbox: axis label inclusion, body-text exclusion, shifted bbox snapping.
# Created At: 2026-11-10
# Created By: AI Agent
# Updated At: 2026-11-10
# Updated By: AI Agent

import pymupdf

from app.modules.exercise.services.pdf_layout_service import PdfLayoutService

PW, PH = 595.0, 842.0


def _doc():
    d = pymupdf.open()
    pg = d.new_page(width=PW, height=PH)
    pg.insert_text((50, 60), "Cau 1. Do thi cho thay su thay doi nhiet do theo thoi gian.", fontsize=10)
    # Plot frame with a few strokes, tick labels left, axis title right.
    pg.draw_rect(pymupdf.Rect(150, 100, 400, 250), width=1)
    pg.draw_line((150, 175), (400, 175), width=1)
    pg.draw_line((275, 100), (275, 250), width=1)
    for i, t in enumerate(["100", "80", "60", "40"]):
        pg.insert_text((120, 108 + i * 45), t, fontsize=9)
    pg.insert_text((405, 250), "t (phut)", fontsize=9)
    pg.insert_text((50, 300), "Day la mot doan van dai mo ta thi nghiem va khong thuoc ve hinh ve nay ca.", fontsize=10)
    pg.insert_text((50, 316), "Tiep tuc doan van dai thu hai mo ta cach lam thi nghiem o tren day.", fontsize=10)
    pg.insert_text((50, 420), "Cau 2. Noi dung cau hai.", fontsize=10)
    return d


def _norm(x0, y0, x1, y1):
    return [x0 / PW * 1000, y0 / PH * 1000, x1 / PW * 1000, y1 / PH * 1000]


def _pts(b):
    return b[0] / 1000 * PW, b[1] / 1000 * PH, b[2] / 1000 * PW, b[3] / 1000 * PH


def test_labels_included_body_excluded():
    d = _doc()
    out = _pts(PdfLayoutService.refine_bbox(d, 1, _norm(150, 100, 400, 250)))
    assert out[0] <= 120 and out[2] >= 405 + 35  # tick labels and axis title
    assert out[3] < 295 and out[3] >= 250  # paragraph below excluded
    assert out[1] > 66  # question stem above excluded


def test_shifted_bbox_snaps_to_figure():
    d = _doc()
    out = _pts(PdfLayoutService.refine_bbox(d, 1, _norm(230, 140, 480, 290), snap=True))
    assert out[0] <= 150 and out[2] >= 400 and out[1] <= 100 and out[3] >= 250
    assert out[3] < 295


def test_render_figure_returns_png():
    d = _doc()
    data = PdfLayoutService.render_figure(d, 1, _norm(150, 100, 400, 250))
    assert data and data[:4] == b"\x89PNG"


def _plot_doc(header: bool = True):
    """Plot with axes under body text, a table-like text block and a running header."""
    d = _doc()
    pg = d[0]
    if header:
        pg.insert_text((50, 30), "Running header text", fontsize=8)
        pg.draw_line((40, 38), (555, 38), width=0.5)
    for i in range(6):
        pg.insert_text((50, 330 + i * 14), "Body text line number %d describing the experiment in detail." % i, fontsize=10)
    return d


def _fig_ok(out):
    return out[0] <= 120 and out[2] >= 440 and out[1] <= 100 and out[3] >= 250 and out[3] < 295


def test_shifted_down_box_lands_on_figure():
    out = _pts(PdfLayoutService.refine_bbox(_plot_doc(), 1, _norm(150, 190, 400, 340), snap=True))
    assert _fig_ok(out)


def test_shifted_right_box_lands_on_figure():
    out = _pts(PdfLayoutService.refine_bbox(_plot_doc(), 1, _norm(260, 100, 510, 250), snap=True))
    assert _fig_ok(out)


def test_header_line_excluded():
    out = _pts(PdfLayoutService.refine_bbox(_plot_doc(), 1, _norm(150, 20, 400, 250), snap=True))
    assert out[1] > 40  # header text and rule above y=40 are not in the crop

def _axes_doc(title_gap: float, stray: bool):
    """Plot with the x-axis title far to the right of the frame and an optional body line above it."""
    d = pymupdf.open()
    pg = d.new_page(width=PW, height=PH)
    if stray:
        pg.insert_text((50, 96), "Body sentence that is much wider than the plot and sits right above it ok.", fontsize=10)
    pg.draw_rect(pymupdf.Rect(150, 110, 350, 250), width=1)
    pg.draw_line((150, 180), (350, 180), width=1)
    pg.draw_line((250, 110), (250, 250), width=1)
    pg.draw_line((350, 250), (352 + title_gap, 250), width=1)  # axis extension to the title
    pg.insert_text((352 + title_gap, 254), "t(phut)", fontsize=10)
    pg.insert_text((50, 330), "Unrelated paragraph text below the figure that is long enough to be body.", fontsize=10)
    return d

def test_far_right_axis_title_absorbed():
    out = _pts(PdfLayoutService.refine_bbox(_axes_doc(30.0, False), 1, _norm(150, 110, 350, 250)))
    assert out[2] >= 352 + 30 + 35  # "t(phut)" fully inside

def test_stray_body_line_above_excluded():
    out = _pts(PdfLayoutService.refine_bbox(_axes_doc(10.0, True), 1, _norm(150, 90, 350, 250)))
    assert out[1] > 99  # body line (y 88-99) not in the crop
    assert out[3] >= 250 and out[3] < 320


# ---- trim_body_text: final crop trimming of leaked body text / header bands ----

def _fig_page():
    d = pymupdf.open()
    pg = d.new_page(width=PW, height=PH)
    pg.draw_rect(pymupdf.Rect(250, 300, 450, 420), width=1)
    pg.draw_line((250, 360), (450, 360), width=1)
    for i, t in enumerate(["10", "5", "0"]):
        pg.insert_text((232, 310 + i * 45), t, fontsize=9)
    pg.insert_text((455, 420), "t (s)", fontsize=9)
    return d, pg


def test_trim_left_body_text_column():
    d, pg = _fig_page()
    pg.insert_text((60, 340), "Mot nhom hoc sinh thuc hien", fontsize=10)
    pg.insert_text((60, 354), "thi nghiem do nhiet do cua nuoc", fontsize=10)
    keep = _norm(250, 300, 450, 420)
    out = _pts(PdfLayoutService.trim_body_text(d, 1, _norm(40, 290, 470, 430), keep))
    assert out[0] >= 185  # text column cut off
    assert out[0] <= 230 and out[2] >= 450 and out[1] <= 300 and out[3] >= 420  # keep intact, tick labels stay


def test_trim_header_band_and_rule():
    d, pg = _fig_page()
    pg.insert_text((150, 30), "Vi tuong lai tuoi sang cua hoc sinh", fontsize=10)
    pg.draw_line((30, 40), (565, 40), width=0.5)
    keep = _norm(250, 300, 450, 420)
    out = _pts(PdfLayoutService.trim_body_text(d, 1, _norm(250, 20, 450, 420), keep))
    assert out[1] > 40


def test_trim_keeps_axis_labels_and_units():
    d, pg = _fig_page()
    pg.insert_text((330, 292), "T (K)", fontsize=9)
    crop = _norm(220, 285, 500, 430)
    out = PdfLayoutService.trim_body_text(d, 1, crop, _norm(250, 300, 450, 420))
    assert [round(v, 3) for v in out] == [round(v, 3) for v in crop]


def test_trim_never_cuts_keep_box():
    d, pg = _fig_page()
    pg.insert_text((260, 330), "text inside the figure box here", fontsize=9)
    keep = _norm(250, 300, 450, 420)
    out = PdfLayoutService.trim_body_text(d, 1, _norm(240, 295, 460, 425), keep)
    assert out[0] <= keep[0] and out[2] >= keep[2] and out[1] <= keep[1] and out[3] >= keep[3]


def test_trim_no_text_layer_noop():
    d = pymupdf.open()
    pg = d.new_page(width=PW, height=PH)
    pg.draw_rect(pymupdf.Rect(250, 300, 450, 420), width=1)
    crop = _norm(200, 250, 500, 450)
    assert PdfLayoutService.trim_body_text(d, 1, crop, _norm(250, 300, 450, 420)) == crop
