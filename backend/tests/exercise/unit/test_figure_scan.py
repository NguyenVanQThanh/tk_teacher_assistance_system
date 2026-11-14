# File Name: test_figure_scan.py
# Description: Raster refinement and dedup of figure crops on scanned (image-only) pages.
# Created At: 2026-11-11
# Created By: AI Agent
# Updated At: 2026-11-11
# Updated By: AI Agent
import io

import numpy as np
import pymupdf
from PIL import Image, ImageDraw, ImageFont

from app.modules.exercise.services import figure_detection_service as fds

from _font import FONT
W, H = 1654, 2339  # A4 at 200 DPI
FIG = (300, 800, 1000, 1300)  # axes box in px


def _page():
    im = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, 30)
    for i in range(6):  # body lines above (y 450-690) and below (y 1360-1560)
        d.text((150, 450 + i * 40), "The quick brown fox jumps over the lazy dog again " * 2, font=f, fill=0)
        d.text((150, 1380 + i * 40), "Pack my box with five dozen liquor jugs please now " * 2, font=f, fill=0)
    x0, y0, x1, y1 = FIG
    d.line([(x0, y1), (x1, y1)], fill=0, width=4)
    d.line([(x0, y0), (x0, y1)], fill=0, width=4)
    d.line([(x0, y1 - 20), (x0 + 200, y1 - 200), (x0 + 400, y1 - 250), (x1 - 40, y0 + 60)], fill=0, width=4)
    d.text((x1 + 25, y1 - 40), "t (s)", font=f, fill=0)  # right-hand axis title
    d.text((x0 + 15, y0 - 45), "T (K)", font=f, fill=0)
    return im


def _pdf(im):
    buf = io.BytesIO()
    im.save(buf, "PNG")
    doc = pymupdf.open()
    pg = doc.new_page(width=595, height=842)
    pg.insert_image(pg.rect, stream=buf.getvalue())
    return doc


def _norm(px):
    return [px[0] * 1000 / W, px[1] * 1000 / H, px[2] * 1000 / W, px[3] * 1000 / H]


def test_title_in_body_lines_out():
    doc = _pdf(_page())
    gray = fds.render_gray(doc, 1, dpi=200)
    assert gray.shape[1] > 1600
    # Sloppy VLM box: right side cut inside the axis title, bottom grown into body lines.
    sloppy = _norm((FIG[0] - 10, FIG[1] - 10, FIG[2] + 40, FIG[3] + 60))
    box = fds.refine_raster_box(gray, sloppy)
    sx, sy = gray.shape[1] / 1000, gray.shape[0] / 1000
    x1, y1 = box[2] * sx, box[3] * sy
    assert x1 >= FIG[2] + 25 + 48  # "t (s)" fully included
    assert box[0] * sx <= FIG[0] and box[1] * sy <= FIG[1] - 30  # y-axis title included
    assert y1 < 1395  # blank margin only; first body glyph row starts below  # body lines below dropped
    assert box[1] * sy > 700  # body lines above dropped


def test_dedup_iou_and_hash():
    a = (1, [100, 100, 400, 400], 0b1010)
    assert fds.is_duplicate_figure(1, [110, 105, 400, 400], None, [a])
    assert not fds.is_duplicate_figure(2, [110, 105, 400, 400], None, [a])
    im = _page().crop(FIG)
    buf = io.BytesIO()
    im.save(buf, "PNG")
    h = fds.image_hash(buf.getvalue())
    assert fds.is_duplicate_figure(3, [0, 0, 5, 5], h, [(1, [500, 500, 900, 900], h)])
    assert not fds.is_duplicate_figure(3, [0, 0, 5, 5], 0, [(1, [500, 500, 900, 900], (1 << 256) - 1)])
