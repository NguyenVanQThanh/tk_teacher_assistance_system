# File Name: test_figure_ocr.py
# Description: Unit tests for OCR figure boxes, scan box fusion and vertical text strip trimming.
# Created At: 2026-11-11
# Created By: AI Agent
# Updated At: 2026-11-11
# Updated By: AI Agent

import sys
from types import SimpleNamespace as NS

import numpy as np

from app.modules.exercise.services import figure_detection_service as fds


def _resp(*boxes):
    return NS(pages=[NS(images=[NS(top_left_x=a, top_left_y=b, bottom_right_x=c, bottom_right_y=d)
                                for a, b, c, d in boxes])])


def test_pixel_to_normalized():
    out = fds.ocr_boxes(_resp((100, 200, 500, 600), (0, 0, 2, 2)), 1000, 2000)
    assert out == [[100.0, 100.0, 500.0, 300.0]]  # tiny box dropped


def test_detect_figures_ocr_failure_returns_empty(monkeypatch):
    monkeypatch.setitem(sys.modules, "mistralai.client", None)  # import fails
    assert fds.detect_figures_ocr(b"not a png") == []


def _page():
    g = np.full((400, 600), 255, np.uint8)
    g[100:300, 200] = 0      # y axis
    g[300, 200:420] = 0      # x axis
    g[100:300, 205:415:20] = 0  # grid-ish
    for y in range(110, 300, 40):
        g[y:y + 8, 170:190] = 0  # tick labels hugging the axis
    return g


def test_fuse_prefers_union_and_keeps_tick_labels():
    g = _page()
    b = fds.fuse_scan_box(g, [330, 250, 700, 760], [320, 240, 710, 770])
    assert b[0] <= 170 * 1000 / 600  # tick labels kept


def test_fuse_without_ocr_uses_vlm_only():
    assert fds.fuse_scan_box(_page(), None, None) == []


def test_vertical_text_strip_trimmed_but_tick_labels_kept():
    g = _page()
    for y in range(110, 300, 14):
        g[y:y + 8, 20:60] = 0  # far-left text column (short lines)
    ink = fds._ink_mask(g)
    comps = fds._components(ink)
    out = fds.trim_text_strips(ink, [10, 90, 430, 310], comps, 8.0)
    assert 60 < out[0] <= 170
