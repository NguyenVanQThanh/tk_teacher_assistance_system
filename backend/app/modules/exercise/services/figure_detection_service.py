# File Name: figure_detection_service.py
# Description: VLM figure detection per page (bbox 0-1000 + caption) and a crop verification pass; used to reconcile with PDF layout blocks.
# Created At: 2026-11-10
# Created By: AI Agent
# Updated At: 2026-11-10
# Updated By: AI Agent

"""Vision-model figure detection, complementing PyMuPDF layout analysis.

All functions fail soft: any error yields an empty / unchanged result and a warning log.
"""
import base64
import hashlib
import io
import json
import logging
import re
from typing import Any, Dict, List, Optional, Sequence

from app.core import config
from app.modules.exercise.services.answer_solver_service import _chat
from app.modules.exercise.services.mistral_vision_parser_service import MistralVisionParserService

logger = logging.getLogger("smartlms.exercise.figure_detection")

DETECT_DPI = 120  # cheap page render; the VLM only needs the coarse layout
VERIFY_MAX_SIDE = 800
GROW_RATIO = 0.06  # share of the box size a "cut" side grows by

DETECT_PROMPT = (
    "You are a layout detector for school exam pages. Find EVERY graph, chart, diagram, geometric drawing, "
    "circuit, photo or table-like illustration on the page image. Return ONLY JSON: "
    '{"figures": [{"bbox": [x0, y0, x1, y1], "caption": "short description", "kind": "graph|diagram|photo|circuit|other"}]}. '
    "bbox is on a 0-1000 scale relative to the page, origin top-left. The bbox MUST include axis labels, axis "
    "titles, units, legends, captions and sub-labels such as (1), (2). It must NOT include question text or "
    'answer options. No figures: {"figures": []}.'
)

VERIFY_PROMPT = (
    "This image is a crop of an exam figure. Return ONLY JSON: "
    '{"complete": bool, "cut": [sides where the figure, its labels or axis titles are cut off], '
    '"has_foreign_text": [sides where unrelated question text or answer options are included]}. '
    "Sides are among left, right, top, bottom."
)

_SIDES = ("left", "right", "top", "bottom")
_BAND = 5  # grid cell in px for ink-gap trimming (see trim_to_gap)

_cache: Dict[tuple, List[dict]] = {}


def enabled() -> bool:
    return bool(config.FIGURE_VLM_ENABLED and MistralVisionParserService.get_api_key())


def _json(text: str) -> Any:
    text = re.sub(r"^```(?:json)?|```$", "", (text or "").strip(), flags=re.M).strip()
    for cand in (text, text[text.find("{"):text.rfind("}") + 1], text[text.find("["):text.rfind("]") + 1]):
        try:
            return json.loads(cand)
        except (ValueError, TypeError):
            continue
    return None


def parse_figures(text: str) -> List[dict]:
    """Tolerant parse of a detection reply into [{bbox, caption, kind}] (bbox clamped to 0-1000)."""
    data = _json(text)
    items = ([data] if "bbox" in data else data.get("figures")) if isinstance(data, dict) else data
    out: List[dict] = []
    for f in items if isinstance(items, list) else []:
        bb = f.get("bbox") if isinstance(f, dict) else None
        try:
            x0, y0, x1, y1 = [max(0.0, min(1000.0, float(v))) for v in bb]
        except (TypeError, ValueError):
            continue
        x0, x1, y0, y1 = min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1)
        if x1 - x0 < 10 or y1 - y0 < 10:
            continue
        out.append({"bbox": [x0, y0, x1, y1], "caption": str(f.get("caption", "")), "kind": str(f.get("kind", "other"))})
    return out


def _image_content(png: bytes, prompt: str) -> List[dict]:
    url = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
    return [{"type": "image_url", "image_url": {"url": url}}, {"type": "text", "text": prompt}]


def _ask(png: bytes, prompt: str) -> str:
    return _chat({
        "model": config.FIGURE_VLM_MODEL or MistralVisionParserService.get_model_name(),
        "messages": [{"role": "user", "content": _image_content(png, prompt)}],
        "reasoning_effort": "low",
        "max_tokens": 2000,
    })


def detect_page_figures(page_png: bytes) -> List[dict]:
    """Figures on one page image (PNG bytes); [] on any failure."""
    try:
        return parse_figures(_ask(page_png, DETECT_PROMPT))
    except Exception as exc:
        logger.warning("Figure detection failed: %s", exc)
        return []


def detect_pdf_figures(file_bytes: bytes) -> Dict[int, List[dict]]:
    """{page_no: figures} for every page, cached per (file hash, page). {} when disabled."""
    if not enabled():
        return {}
    import pymupdf
    key = hashlib.sha1(file_bytes).hexdigest()
    out: Dict[int, List[dict]] = {}
    try:
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        logger.warning("Figure detection cannot open PDF: %s", exc)
        return {}
    try:
        for i in range(doc.page_count):
            if (key, i + 1) not in _cache:
                _cache[(key, i + 1)] = detect_page_figures(doc[i].get_pixmap(dpi=DETECT_DPI, alpha=False).tobytes("png"))
            out[i + 1] = _cache[(key, i + 1)]
    finally:
        doc.close()
    return out


def verify_crop(crop_png: bytes) -> dict:
    """{complete, cut: [...], has_foreign_text: [...]}; {} on failure."""
    try:
        data = _json(_ask(crop_png, VERIFY_PROMPT))
        if not isinstance(data, dict):
            return {}
        pick = lambda k: [s for s in (data.get(k) or []) if s in _SIDES] if isinstance(data.get(k), list) else []
        return {"complete": bool(data.get("complete", True)), "cut": pick("cut"), "has_foreign_text": pick("has_foreign_text")}
    except Exception as exc:
        logger.warning("Figure verification failed: %s", exc)
        return {}


def best_match(page: int, bbox: Sequence[float], figures: Dict[int, List[dict]], min_iou: float = 0.25) -> Optional[dict]:
    """VLM figure on ``page`` with the best IoU against ``bbox`` (>= min_iou), else None."""
    best, score = None, min_iou
    for f in figures.get(page, []):
        i = iou(f["bbox"], bbox)
        if i >= score:
            best, score = f, i
    return best


def iou(a: Sequence[float], b: Sequence[float]) -> float:
    inter = max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    area = lambda r: max(0.0, r[2] - r[0]) * max(0.0, r[3] - r[1])
    union = area(a) + area(b) - inter
    return inter / union if union > 0 else 0.0


def trim_to_gap(doc: Any, page_no: int, bbox: Sequence[float], side: str) -> List[float]:
    """Cut ``side`` of a normalized bbox back to the first blank band inside its outer 35%.

    Used when the VLM reports foreign text on that side: the text is separated from the figure by
    white space, so the first ink-free band (after some ink) is the boundary. Unchanged if none.
    """
    import pymupdf
    pg = doc[page_no - 1]
    pr = pg.rect
    x0, y0, x1, y1 = [float(v) for v in bbox]
    clip = pymupdf.Rect(pr.x0 + x0 / 1000 * pr.width, pr.y0 + y0 / 1000 * pr.height,
                        pr.x0 + x1 / 1000 * pr.width, pr.y0 + y1 / 1000 * pr.height) & pr
    pix = pg.get_pixmap(dpi=100, clip=clip, colorspace=pymupdf.csGRAY, alpha=False)
    W, H, data = pix.width, pix.height, pix.samples
    horiz = side in ("top", "bottom")
    n = H if horiz else W
    def has_ink(k: int) -> bool:
        if horiz:
            return any(v < 200 for v in data[k * pix.stride:k * pix.stride + W])
        return any(data[y * pix.stride + k] < 200 for y in range(H))
    order = list(range(n)) if side in ("top", "left") else list(range(n - 1, -1, -1))
    limit, seen_ink, gap = int(0.35 * n), False, 0
    for step, k in enumerate(order[:limit]):
        if has_ink(k):
            seen_ink, gap = True, 0
        elif seen_ink:
            gap += 1
            if gap >= max(2, _BAND // 2):
                cut = (k + 1) if side in ("top", "left") else k
                # Only trim when the remaining part is clearly still a figure (>= 40% of the size).
                frac = cut / n if side in ("top", "left") else 1 - cut / n
                if 0 < frac < 0.6:
                    if horiz:
                        d = (y1 - y0) * cut / n
                        return [x0, y0 + d, x1, y1] if side == "top" else [x0, y0, x1, y0 + d]
                    d = (x1 - x0) * cut / n
                    return [x0 + d, y0, x1, y1] if side == "left" else [x0, y0, x0 + d, y1]
                break
    return [x0, y0, x1, y1]


def verify_adjust(doc: Any, page_no: int, bbox: Sequence[float], clamp: Optional[Sequence[float]] = None) -> List[float]:
    """One verification iteration: grow cut sides by 6%, trim sides with foreign text. Never raises."""
    if not (config.FIGURE_VLM_VERIFY and enabled()):
        return list(bbox)
    try:
        from app.modules.exercise.services.pdf_layout_service import PdfLayoutService
        png = PdfLayoutService.render_clip(doc, page_no, bbox, dpi=int(VERIFY_MAX_SIDE / 8), pad=0.0)
        if not png:
            return list(bbox)
        res = verify_crop(png)
        if not res:
            return list(bbox)
        x0, y0, x1, y1 = [float(v) for v in bbox]
        w, h = x1 - x0, y1 - y0
        lim = list(clamp) if clamp else [0.0, 0.0, 1000.0, 1000.0]
        if "left" in res["cut"]:
            x0 = max(lim[0], x0 - GROW_RATIO * w)
        if "right" in res["cut"]:
            x1 = min(lim[2], x1 + GROW_RATIO * w)
        if "top" in res["cut"]:
            y0 = max(lim[1], y0 - GROW_RATIO * h)
        if "bottom" in res["cut"]:
            y1 = min(lim[3], y1 + GROW_RATIO * h)
        out = [x0, y0, x1, y1]
        for side in res["has_foreign_text"]:
            if side not in res["cut"]:
                out = trim_to_gap(doc, page_no, out, side)
        return out
    except Exception as exc:
        logger.warning("Figure verify/adjust failed: %s", exc)
        return list(bbox)


# --------------------------------------------------------------------------- raster refinement (scans)
# Pure numpy: used when the page has no text layer, so the VLM box is the only signal.

def _ink_mask(gray: Any) -> Any:
    """Boolean ink mask: pixels clearly darker than the paper (paper level = 90th percentile)."""
    import numpy as np
    paper = float(np.percentile(gray, 90))
    return gray < max(60.0, paper - 70.0)


def _components(ink: Any) -> List[List[int]]:
    """8-connected components of a boolean mask (row-run union-find) -> [x0, y0, x1, y1]."""
    import numpy as np
    runs: List[tuple] = []
    parent: List[int] = []
    prev: List[int] = []

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for y in range(ink.shape[0]):
        row = ink[y]
        cur: List[int] = []
        if row.any():
            d = np.diff(np.concatenate(([0], row.view(np.uint8), [0])))
            for xs, xe in zip(np.flatnonzero(d == 1).tolist(), np.flatnonzero(d == -1).tolist()):
                i = len(runs)
                runs.append((y, xs, xe))
                parent.append(i)
                cur.append(i)
                for j in prev:
                    if runs[j][1] <= xe and xs <= runs[j][2]:
                        a, b = find(i), find(j)
                        if a != b:
                            parent[a] = b
        prev = cur
    comps: Dict[int, List[int]] = {}
    for i, (y, xs, xe) in enumerate(runs):
        r = find(i)
        c = comps.get(r)
        if c is None:
            comps[r] = [xs, y, xe, y + 1]
        else:
            c[0], c[1], c[2], c[3] = min(c[0], xs), min(c[1], y), max(c[2], xe), max(c[3], y + 1)
    return list(comps.values())


def estimate_text_height(comps: Sequence[Sequence[int]], page_h: int) -> float:
    """Median height of glyph-sized components on the page (page-relative, no fixed constant)."""
    hs = sorted(c[3] - c[1] for c in comps
                if 3 <= c[3] - c[1] <= 0.03 * page_h and c[2] - c[0] <= 0.03 * page_h)
    return float(hs[len(hs) // 2]) if hs else max(6.0, page_h * 0.01)


def grow_box(box: Sequence[int], comps: Sequence[Sequence[int]], med: float, page_w: int, page_h: int) -> List[int]:
    """Grow a pixel box over ink components that touch it, or sit within 1.5 x text height
    to its right (x-axis title) / above it (y-axis title). Per-side growth is capped."""
    gap = 1.5 * med
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    cap_r, cap_u = x1 + 0.4 * bw, y0 - 0.15 * bh
    for _ in range(6):
        changed = False
        for cx0, cy0, cx1, cy1 in (c[:4] for c in comps):
            small = cy1 - cy0 <= 2.5 * med
            if cx1 > x0 and cx0 < x1 and cy1 > y0 and cy0 < y1:
                if cx1 - cx0 > 1.6 * bw or cy1 - cy0 > 1.6 * bh:
                    continue  # page frame / body block
                n = (min(x0, cx0), min(y0, cy0), max(x1, cx1), max(y1, cy1))
            elif cx0 >= x1 and cx0 - x1 <= gap and cy1 > y0 and cy0 < y1 and small:
                n = (x0, y0, min(max(x1, cx1), int(cap_r)), y1)
            elif cy1 <= y0 and y0 - cy1 <= gap and cx1 > x0 and cx0 < x1 and small and cy0 >= cap_u:
                n = (x0, min(y0, cy0), x1, y1)
            else:
                continue
            n = (max(0, n[0]), max(0, n[1]), min(page_w, n[2]), min(page_h, n[3]))
            if n != (x0, y0, x1, y1):
                x0, y0, x1, y1 = n
                changed = True
        if not changed:
            break
    return [int(x0), int(y0), int(x1), int(y1)]


def trim_text_bands(ink: Any, box: Sequence[int], comps: Sequence[Sequence[int]], med: float) -> List[int]:
    """Drop text-like bands (and thin full-width rules) at the top/bottom edges of the box.
    Never cuts into the largest ink component (the figure core)."""
    import numpy as np
    x0, y0, x1, y1 = box
    bw = x1 - x0
    inside = [c for c in comps if c[0] >= x0 - 1 and c[2] <= x1 + 1 and c[1] >= y0 - 1 and c[3] <= y1 + 1]
    if not inside:
        return [x0, y0, x1, y1]
    core = max(inside, key=lambda c: (c[2] - c[0]) * (c[3] - c[1]))
    for side in ("top", "bottom"):
        for _ in range(10):
            prof = ink[y0:y1, x0:x1].any(axis=1)
            ys = np.flatnonzero(prof)
            if len(ys) == 0 or y1 - y0 < 8:
                break
            if side == "top":
                a = int(ys[0])
                b = a
                while b + 1 < len(prof) and prof[b + 1]:
                    b += 1
            else:
                b = int(ys[-1])
                a = b
                while a > 0 and prof[a - 1]:
                    a -= 1
            r0, r1 = y0 + a, y0 + b + 1
            if core[1] < r1 and core[3] > r0:
                break  # run touches the figure core
            members = [c for c in inside if c[1] < r1 and c[3] > r0]
            if not members:
                break
            h = r1 - r0
            span = max(c[2] for c in members) - min(c[0] for c in members)
            rule = h <= 0.25 * med and span > 0.8 * bw
            text = (h <= 2.2 * med and span > 0.4 * bw and len(members) >= 4
                    and all(c[2] - c[0] <= 0.4 * bw and c[3] - c[1] <= 2.2 * med for c in members))
            if not (rule or text):
                break
            if side == "top":
                y0 = r1
            else:
                y1 = r0
    return [x0, y0, x1, y1]


def refine_raster_box(gray: Any, bbox: Sequence[float], pad: float = 0.04) -> List[float]:
    """Refine a VLM box (0-1000 normalized) on a grayscale page raster; returns a 0-1000 box.
    Pads 4%, grows over axis titles, trims edge text bands. Returns the padded box on any doubt."""
    h, w = gray.shape
    bx0, by0, bx1, by1 = [float(v) for v in bbox]
    pw, ph = (bx1 - bx0) * pad, (by1 - by0) * pad
    pbox = [max(0.0, bx0 - pw), max(0.0, by0 - ph), min(1000.0, bx1 + pw), min(1000.0, by1 + ph)]
    px = [int(pbox[0] * w / 1000), int(pbox[1] * h / 1000), int(pbox[2] * w / 1000), int(pbox[3] * h / 1000)]
    if px[2] - px[0] < 8 or px[3] - px[1] < 8:
        return pbox
    ink = _ink_mask(gray)
    comps = _components(ink)
    if not comps:
        return pbox
    med = estimate_text_height(comps, h)
    out = trim_text_bands(ink, grow_box(px, comps, med, w, h), comps, med)
    return [out[0] * 1000.0 / w, out[1] * 1000.0 / h, out[2] * 1000.0 / w, out[3] * 1000.0 / h]


def render_gray(doc: Any, page_no: int, dpi: int = 200) -> Any:
    """Render a page to a grayscale numpy array."""
    import numpy as np
    pix = doc[page_no - 1].get_pixmap(dpi=dpi, colorspace="gray", alpha=False)
    return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)


# --------------------------------------------------------------------------- OCR figure boxes (scans)

_ocr_cache: Dict[tuple, List[List[float]]] = {}


def ocr_boxes(resp: Any, width: int, height: int) -> List[List[float]]:
    """Image boxes of a Mistral OCR response, converted from pixels of the submitted page to 0-1000."""
    out: List[List[float]] = []
    for pg in getattr(resp, "pages", None) or []:
        for im in getattr(pg, "images", None) or []:
            try:
                x0, y0, x1, y1 = [float(getattr(im, k)) for k in
                                  ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")]
            except (TypeError, ValueError, AttributeError):
                continue
            b = [max(0.0, min(1000.0, x0 * 1000 / width)), max(0.0, min(1000.0, y0 * 1000 / height)),
                 max(0.0, min(1000.0, x1 * 1000 / width)), max(0.0, min(1000.0, y1 * 1000 / height))]
            if b[2] - b[0] >= 10 and b[3] - b[1] >= 10:
                out.append(b)
    return out


def detect_figures_ocr(page_png: bytes) -> List[List[float]]:
    """Figure boxes (0-1000) from Mistral OCR image regions of one page PNG; [] on any failure."""
    try:
        from PIL import Image
        from mistralai.client import Mistral
        w, h = Image.open(io.BytesIO(page_png)).size
        client = Mistral(api_key=MistralVisionParserService.get_api_key())
        url = "data:image/png;base64," + base64.b64encode(page_png).decode("ascii")
        resp = client.ocr.process(model=MistralVisionParserService.get_ocr_model(),
                                  document={"type": "image_url", "image_url": url}, include_image_base64=False)
        return ocr_boxes(resp, w, h)
    except Exception as exc:
        logger.warning("OCR figure detection failed: %s", exc)
        return []


def detect_pdf_ocr_figures(file_bytes: bytes, pages: Sequence[int]) -> Dict[int, List[List[float]]]:
    """{page_no: OCR boxes} for the requested pages, cached per (file hash, page). {} when no API key."""
    if not MistralVisionParserService.get_api_key():
        return {}
    import pymupdf
    key = hashlib.sha1(file_bytes).hexdigest()
    out: Dict[int, List[List[float]]] = {}
    try:
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        logger.warning("OCR figure detection cannot open PDF: %s", exc)
        return {}
    try:
        for p in pages:
            if (key, p) not in _ocr_cache and 1 <= p <= doc.page_count:
                _ocr_cache[(key, p)] = detect_figures_ocr(doc[p - 1].get_pixmap(dpi=DETECT_DPI, alpha=False).tobytes("png"))
            out[p] = _ocr_cache.get((key, p), [])
    finally:
        doc.close()
    return out


def trim_text_strips(ink: Any, box: Sequence[int], comps: Sequence[Sequence[int]], med: float) -> List[int]:
    """Drop text-like vertical strips at the left/right edges: a column of short lines separated from the
    rest by a white gutter. Keeps the figure core and tick labels (a strip within 3 text heights of the
    core, i.e. hugging an axis, is never removed)."""
    import numpy as np
    x0, y0, x1, y1 = box
    bh = y1 - y0
    inside = [c for c in comps if c[0] >= x0 - 1 and c[2] <= x1 + 1 and c[1] >= y0 - 1 and c[3] <= y1 + 1]
    if not inside:
        return [x0, y0, x1, y1]
    core = max(inside, key=lambda c: (c[2] - c[0]) * (c[3] - c[1]))
    gut = max(2, int(0.8 * med))
    for side in ("left", "right"):
        # Zone beyond 3 text heights from the core: nearer ink is tick labels / axis titles, always kept.
        lo, hi = (x0, core[0] - int(3 * med)) if side == "left" else (core[2] + int(3 * med), x1)
        if hi - lo < gut + 2:
            continue
        prof = ink[y0:y1, lo:hi].any(axis=0)
        ks = range(len(prof) - 1, -1, -1) if side == "left" else range(len(prof))  # core -> outward
        cut, run, seen = None, 0, False
        for k in ks:
            seen = seen or bool(prof[k])
            run = 0 if prof[k] else run + 1
            if seen and run >= gut:
                cut = k  # first gutter after ink; text must lie beyond it (checked below)
                break
        if cut is None:
            continue
        z0, z1 = (lo, lo + cut) if side == "left" else (lo + cut, hi)
        members = [c for c in inside if c is not core and c[0] >= z0 - 1 and c[2] <= z1 + 1]
        if len(members) < 3 or any(c[3] - c[1] > 2.2 * med for c in members):
            continue
        if max(c[3] for c in members) - min(c[1] for c in members) <= 0.4 * (y1 - y0):
            continue
        if side == "left":
            x0 = z1
        else:
            x1 = z0
    return [x0, y0, x1, y1]


def trim_furniture(box: Sequence[int], rects: Sequence[Sequence[float]], w: int, h: int) -> List[int]:
    """Cut header/footer rects (0-1000) off the top/bottom of a pixel box."""
    x0, y0, x1, y1 = box
    for rx0, ry0, rx1, ry1 in rects or []:
        ry0, ry1 = ry0 * h / 1000, ry1 * h / 1000
        if rx1 * w / 1000 <= x0 or rx0 * w / 1000 >= x1:
            continue
        mid = (y0 + y1) / 2
        if ry1 <= mid and ry1 > y0:
            y0 = int(ry1)
        elif ry0 >= mid and ry0 < y1:
            y1 = int(ry0)
    return [x0, y0, x1, y1]


def fuse_scan_box(gray: Any, ocr: Optional[Sequence[float]], vlm: Optional[Sequence[float]],
                  furniture: Optional[Sequence[Sequence[float]]] = None, pad: float = 0.02) -> List[float]:
    """Fuse OCR image box + VLM box (0-1000) on a scan raster: union when they agree (IoU >= 0.3, else the
    OCR box), grow over touching ink, trim furniture, text bands and text strips. Returns a 0-1000 box."""
    if ocr is None:
        return refine_raster_box(gray, vlm) if vlm else []
    base = list(ocr)
    if vlm is not None and iou(ocr, vlm) >= 0.3:
        base = [min(ocr[0], vlm[0]), min(ocr[1], vlm[1]), max(ocr[2], vlm[2]), max(ocr[3], vlm[3])]
    h, w = gray.shape
    bw, bh = (base[2] - base[0]) * pad, (base[3] - base[1]) * pad
    px = [int(max(0.0, base[0] - bw) * w / 1000), int(max(0.0, base[1] - bh) * h / 1000),
          int(min(1000.0, base[2] + bw) * w / 1000), int(min(1000.0, base[3] + bh) * h / 1000)]
    ink = _ink_mask(gray)
    comps = _components(ink)
    if not comps or px[2] - px[0] < 8 or px[3] - px[1] < 8:
        return base
    med = estimate_text_height(comps, h)
    box = grow_box(px, comps, med, w, h)
    return trim_scan_box(gray, [box[0] * 1000.0 / w, box[1] * 1000.0 / h, box[2] * 1000.0 / w, box[3] * 1000.0 / h],
                         furniture)


def trim_scan_box(gray: Any, bbox: Sequence[float], furniture: Optional[Sequence[Sequence[float]]] = None) -> List[float]:
    """Trim furniture, edge text bands and text strips from a 0-1000 box (also re-run after VLM verify grows it)."""
    h, w = gray.shape
    px = [int(bbox[0] * w / 1000), int(bbox[1] * h / 1000), int(bbox[2] * w / 1000), int(bbox[3] * h / 1000)]
    ink = _ink_mask(gray)
    comps = _components(ink)
    if not comps or px[2] - px[0] < 8 or px[3] - px[1] < 8:
        return list(bbox)
    med = estimate_text_height(comps, h)
    box = trim_furniture(px, furniture, w, h)
    box = trim_text_strips(ink, trim_text_bands(ink, box, comps, med), comps, med)
    return [box[0] * 1000.0 / w, box[1] * 1000.0 / h, box[2] * 1000.0 / w, box[3] * 1000.0 / h]


# --------------------------------------------------------------------------- dedup

def image_hash(png: bytes, size: int = 16) -> int:
    """Cheap perceptual (average) hash of a downscaled grayscale crop."""
    from PIL import Image
    px = list(Image.open(io.BytesIO(png)).convert("L").resize((size, size)).getdata())
    mean = sum(px) / len(px)
    v = 0
    for p in px:
        v = (v << 1) | (1 if p > mean else 0)
    return v


def is_duplicate_figure(page: int, bbox: Sequence[float], h: Optional[int],
                        seen: Sequence[tuple], max_bits: int = 8, min_iou: float = 0.6) -> bool:
    """True when (page, bbox) overlaps a seen figure with IoU > min_iou on the same page, or the
    perceptual hash is within max_bits of a seen one. seen items: (page, bbox, hash or None)."""
    for sp, sb, sh in seen:
        if sp == page and iou(bbox, sb) > min_iou:
            return True
        if h is not None and sh is not None and bin(h ^ sh).count("1") <= max_bits:
            return True
    return False
