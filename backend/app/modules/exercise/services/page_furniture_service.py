# File Name: page_furniture_service.py
# Description: Detects repeated page headers/footers (page furniture) in PDFs and masks them so the model and local parser never see them.
# Created At: 2026-11-11
# Created By: AI Agent
# Updated At: 2026-11-11
# Updated By: AI Agent

import io
import logging
import re
import unicodedata
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

BAND = 0.12          # top/bottom fraction of the page scanned for furniture
Y_TOL = 0.015        # max y drift of a repeated line between pages
MIN_REPEAT = 0.5     # fraction of pages a line must repeat on
NCC_MIN = 0.8        # scan band profile correlation threshold
PAD = 6              # rect padding (0-1000 units)

# Lines that carry exam structure are never furniture.
_PROTECTED = re.compile(r"^\s*(c[aâ]u\s*\d|ph[aầ]n\s|[dđ][eề]\s*s[oố]|m[aã]\s*[dđ][eề]|b[aà]i\s*\d|\d+\s*[.)]\s)",
                        re.IGNORECASE)
_PAGE_NO = re.compile(r"^(trang|page)?\s*\d{1,4}\s*(/\s*\d{1,4})?\s*\|?$|^\d{1,4}\s*\|$|^\|\s*\d{1,4}$", re.IGNORECASE)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"\d", "#", unicodedata.normalize("NFC", text)).casefold()).strip()


def _lines(page: Any) -> List[Dict[str, Any]]:
    """Group page words into lines with normalized (0-1000) boxes."""
    w, h = float(page.width), float(page.height)
    rows: Dict[int, List[Dict[str, Any]]] = {}
    for wd in page.extract_words():
        rows.setdefault(round(wd["top"] / 3), []).append(wd)
    out = []
    for ws in rows.values():
        ws.sort(key=lambda d: d["x0"])
        out.append({
            "text": " ".join(d["text"] for d in ws),
            "rect": [min(d["x0"] for d in ws) / w * 1000, min(d["top"] for d in ws) / h * 1000,
                     max(d["x1"] for d in ws) / w * 1000, max(d["bottom"] for d in ws) / h * 1000],
        })
    return out


def _in_band(rect: List[float]) -> bool:
    return rect[3] <= BAND * 1000 or rect[1] >= (1 - BAND) * 1000


def _text_furniture(pdf: Any) -> Optional[List[List[List[float]]]]:
    pages = pdf.pages
    cand = []  # per page: [(key, rect, protected)]
    total_words = 0
    for pg in pages:
        ls = _lines(pg)
        total_words += sum(len(l["text"].split()) for l in ls)
        cand.append([l for l in ls if _in_band(l["rect"]) and l["text"].strip()])
    if total_words < 10 * len(pages):
        return None  # no usable text layer
    need = max(2, -(-len(pages) // 2)) if len(pages) >= 2 else 99
    result: List[List[List[float]]] = []
    for i, pg in enumerate(pages):
        rects = []
        for l in cand[i]:
            if _PROTECTED.match(l["text"]):
                continue
            key, y = _norm(l["text"]), (l["rect"][1] + l["rect"][3]) / 2
            hits = 0
            for j in range(len(pages)):
                if any(_norm(o["text"]) == key and abs((o["rect"][1] + o["rect"][3]) / 2 - y) <= Y_TOL * 1000
                       for o in cand[j]):
                    hits += 1
            if hits >= need or _PAGE_NO.match(l["text"].strip()):
                rects.append(l["rect"])
        # thin full-width horizontal rules adjacent to a furniture line
        if rects:
            h, w = float(pg.height), float(pg.width)
            for ln in list(pg.lines) + [r for r in pg.rects if r["height"] < 2]:
                x0, x1 = ln["x0"] / w * 1000, ln["x1"] / w * 1000
                y = ln["top"] / h * 1000
                if x1 - x0 > 600 and _in_band([0, y, 0, y]) and any(
                        abs(y - r[3]) < 25 or abs(y - r[1]) < 25 for r in rects):
                    rects.append([x0, y - 1, x1, y + 1])
        result.append([[max(0.0, r[0] - PAD), max(0.0, r[1] - PAD), min(1000.0, r[2] + PAD), min(1000.0, r[3] + PAD)]
                       for r in rects])
    return result


def _scan_furniture(images: List[Any]) -> List[List[List[float]]]:
    """Image analysis: band ink profiles that correlate across pages mark furniture."""
    import numpy as np
    n = len(images)
    empty: List[List[List[float]]] = [[] for _ in range(n)]
    if n < 2:
        return empty
    need = max(2, -(-n // 2))
    out = [[] for _ in range(n)]
    for top in (True, False):
        profs, spans, ink_all = [], [], []
        for img in images:
            g = np.asarray(img.convert("L").resize((200, 280)), dtype=float)
            band = g[:int(280 * BAND)] if top else g[-int(280 * BAND):]
            ink = (band < 160)
            prof = ink.mean(axis=1)
            profs.append(prof)
            spans.append(ink)
            ink_all.append(ink)
        for i in range(n):
            p = profs[i]
            if p.max() == 0 or (p > 0).mean() > 0.6:
                continue
            hits = 1
            for j in range(n):
                if j == i or profs[j].max() == 0:
                    continue
                a, b = p - p.mean(), profs[j] - profs[j].mean()
                d = np.sqrt((a * a).sum() * (b * b).sum())
                if d > 0 and (a * b).sum() / d > NCC_MIN:
                    hits += 1
            if hits < need:
                continue
            rows = np.where(spans[i].any(axis=1))[0]
            # keep only the ink cluster nearest the page edge (a gap of >2 blank rows ends it)
            rows = rows if top else rows[::-1]
            cut = next((k for k in range(1, len(rows)) if abs(rows[k] - rows[k - 1]) > 3), len(rows))
            rows = rows[:cut]
            spans[i] = spans[i].copy()
            spans[i][:, :] = False
            spans[i][rows, :] = ink_all[i][rows, :]
            cols = np.where(spans[i].any(axis=0))[0]
            off = 0 if top else 280 - int(280 * BAND)
            y0, y1 = (rows.min() + off) / 280 * 1000, (rows.max() + 1 + off) / 280 * 1000
            out[i].append([max(0.0, cols.min() / 200 * 1000 - PAD), max(0.0, y0 - 2 * PAD),
                           min(1000.0, (cols.max() + 1) / 200 * 1000 + PAD), min(1000.0, y1 + 2 * PAD)])
    return out


def detect_furniture(file_bytes: bytes, page_images: Optional[List[Any]] = None) -> List[List[List[float]]]:
    """Per-page rects [x0, y0, x1, y1] (0-1000) to mask. Returns [] lists when unreliable."""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            res = _text_furniture(pdf)
            n = len(pdf.pages)
        if res is not None:
            return res
        if page_images:
            return _scan_furniture(page_images)
        return [[] for _ in range(n)]
    except Exception as e:
        logger.warning("Page furniture detection failed: %s", e)
        return []


def mask_images(images: List[Any], rects: List[List[List[float]]]) -> List[Any]:
    """Copies of the page images with furniture rects painted white."""
    from PIL import ImageDraw
    out = []
    for i, img in enumerate(images):
        rs = rects[i] if i < len(rects) else []
        if not rs:
            out.append(img)
            continue
        cp = img.copy()
        w, h = cp.size
        d = ImageDraw.Draw(cp)
        for r in rs:
            d.rectangle([r[0] / 1000 * w, r[1] / 1000 * h, r[2] / 1000 * w, r[3] / 1000 * h], fill="white")
        out.append(cp)
    return out


def strip_page_text(page: Any, rects: List[List[float]]) -> Any:
    """pdfplumber page without characters inside the furniture rects."""
    if not rects:
        return page
    w, h = float(page.width), float(page.height)

    def keep(o: Dict[str, Any]) -> bool:
        if o.get("object_type") != "char":
            return True
        cx, cy = (o["x0"] + o["x1"]) / 2 / w * 1000, (o["top"] + o["bottom"]) / 2 / h * 1000
        return not any(r[0] <= cx <= r[2] and r[1] <= cy <= r[3] for r in rects)

    return page.filter(keep)


# Masked model views keyed by id(original list); the original list is kept alive so ids stay valid.
_VIEWS: Dict[int, Any] = {}


def register_model_view(page_images: List[Any], rects: List[List[List[float]]]) -> None:
    """Remember a masked copy of page_images for model calls (originals stay untouched)."""
    if not page_images or not any(rects):
        return
    if len(_VIEWS) >= 8:
        _VIEWS.pop(next(iter(_VIEWS)))
    _VIEWS[id(page_images)] = (page_images, mask_images(page_images, rects))


def model_view(page_images: List[Any]) -> List[Any]:
    """Masked copy registered for page_images, else page_images itself."""
    hit = _VIEWS.get(id(page_images))
    return hit[1] if hit and hit[0] is page_images else page_images
