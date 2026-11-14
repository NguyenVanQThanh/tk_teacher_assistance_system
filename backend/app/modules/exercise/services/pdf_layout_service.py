# File Name: pdf_layout_service.py
# Description: PyMuPDF based PDF layout analysis: figure/table block detection, question anchors and regions, and clip rendering.
# Created At: 2026-11-09
# Created By: AI Agent
# Updated At: 2026-11-09
# Updated By: AI Agent

"""PDF layout analysis used to attach figures to the right question.

All coordinates handled here are normalized to 0-1000 in the page DISPLAY space
(i.e. after applying the page rotation). PyMuPDF reports drawings, image info,
tables and words in UNROTATED space, so every rect is multiplied by
``page.rotation_matrix`` before normalizing by ``page.rect``.
"""

import logging
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import pymupdf

logger = logging.getLogger("smartlms.exercise.pdf_layout")

BBox = Tuple[float, float, float, float]

_MIN_SIDE = 15.0
_MIN_AREA = 3000.0
_MAX_ASPECT = 15.0
_MAX_IMAGE_AREA = 0.85e6
_MERGE_INFLATE = 8.0
_COLUMN_SPLIT = 500.0
_ANCHOR_MARGIN = 8.0
_OPTION_Y_TOL = 20.0
_OPTION_X_TOL = 10.0

_NUM_TOKEN = re.compile(r"^\d{1,3}[.:)]?$")
_GLUED = re.compile(r"^(Câu|Question|Bài)(\d{1,3})[.:)]?$")
_KEYWORDS = ("Câu", "Question", "Bài")
_STOPPERS = ("PHẦN", "ĐÁP ÁN", "HƯỚNG DẪN", "ĐỀ SỐ")
_OPTION_LABEL = re.compile(r"^[A-D][.)]$")
_PART_ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6}
_PART_RE = re.compile(r"^PH[ẦA]N$", re.IGNORECASE)
_HAIRLINE_H = 2.0  # normalized height under which a wide drawing is a rule, not a figure
_HAIRLINE_W = 600.0
_TABLE_GROW_MARGIN = 12.0  # pt a table may grow over touching cell/border drawings
_INLINE_MAX_H = 35.0  # images shorter than this (normalized) are inline formulas
_INLINE_ROW_MAX_H = 60.0
_OPTION_LABEL_GAP = 60.0  # max horizontal gap between an option label and its figure
_INLINE_ADJ = 40.0  # normalized gap within which same-row text marks an image as inline


@dataclass(frozen=True)
class Block:
    """A figure, vector drawing or table region on a page."""
    id: str
    page: int  # 1-based
    bbox: BBox  # normalized 0-1000, display space
    kind: str  # image | drawing | table
    area: float


@dataclass(frozen=True)
class Word:
    """A text word with a normalized 0-1000 bbox (display space)."""
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    block: int
    line: int
    wno: int


@dataclass(frozen=True)
class Anchor:
    """Start of a question (number set) or a section stopper (number None)."""
    page: int
    col: int
    y: float
    x: float
    number: Optional[int]
    part: int = 0  # 1-based PHẦN index within the scanned range (0 = before any PHẦN)


@dataclass(frozen=True)
class Region:
    """Flow area owned by one question anchor: list of (page, x0, y0, x1, y1)."""
    anchor: Anchor
    number: int
    rects: Tuple[Tuple[int, float, float, float, float], ...]

    @property
    def part(self) -> int:
        return self.anchor.part


@dataclass
class PdfLayout:
    blocks_by_page: Dict[int, List[Block]] = field(default_factory=dict)
    words_by_page: Dict[int, List[Word]] = field(default_factory=dict)

    @property
    def has_text(self) -> bool:
        return any(self.words_by_page.values())

    @property
    def has_blocks(self) -> bool:
        return any(self.blocks_by_page.values())


@dataclass
class RegionAssignment:
    stem: List[Block] = field(default_factory=list)
    options: Dict[str, Block] = field(default_factory=dict)


# --------------------------------------------------------------------------- geometry helpers

def _norm_rect(page, rect) -> BBox:
    """Unrotated PyMuPDF rect -> normalized 0-1000 display-space bbox."""
    r = pymupdf.Rect(rect) * page.rotation_matrix
    r.normalize()
    pr = page.rect
    return (
        (r.x0 - pr.x0) / pr.width * 1000.0,
        (r.y0 - pr.y0) / pr.height * 1000.0,
        (r.x1 - pr.x0) / pr.width * 1000.0,
        (r.y1 - pr.y0) / pr.height * 1000.0,
    )


def _area(b: Sequence[float]) -> float:
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def _inter(a: Sequence[float], b: Sequence[float]) -> float:
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


def _iou(a: Sequence[float], b: Sequence[float]) -> float:
    i = _inter(a, b)
    u = _area(a) + _area(b) - i
    return i / u if u > 0 else 0.0


def _union(a: Sequence[float], b: Sequence[float]) -> BBox:
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def _touch(a: Sequence[float], b: Sequence[float], inflate: float) -> bool:
    return (a[0] - inflate < b[2] and b[0] - inflate < a[2]
            and a[1] - inflate < b[3] and b[1] - inflate < a[3])


def _is_hairline(nb: Sequence[float]) -> bool:
    """Page-wide thin rule (header/footer line) in normalized coordinates."""
    return (nb[3] - nb[1]) < _HAIRLINE_H and (nb[2] - nb[0]) > _HAIRLINE_W


def _plausible(b: Sequence[float]) -> bool:
    w, h = b[2] - b[0], b[3] - b[1]
    if w < _MIN_SIDE or h < _MIN_SIDE:
        return False
    return max(w / h, h / w) <= _MAX_ASPECT


def _merge_blocks(items: List[Tuple[BBox, str]]) -> List[Tuple[BBox, str]]:
    """Greedily merge touching non-table boxes; tables stay untouched."""
    tables = [i for i in items if i[1] == "table"]
    rest = [i for i in items if i[1] != "table"]
    changed = True
    while changed:
        changed = False
        out: List[Tuple[BBox, str]] = []
        for box, kind in rest:
            for idx, (obox, okind) in enumerate(out):
                if not _touch(box, obox, _MERGE_INFLATE):
                    continue
                merged = _union(box, obox)
                mw = merged[2] - merged[0]
                # Two-column guard: do not bridge two column-sized parts into a full-width block.
                if mw > 550 and (box[2] - box[0]) < 450 and (obox[2] - obox[0]) < 450:
                    continue
                out[idx] = (merged, "image" if "image" in (kind, okind) else "drawing")
                changed = True
                break
            else:
                out.append((box, kind))
        rest = out
    # Absorb blocks that sit >90% inside a bigger block (tables included).
    allb = sorted(tables + rest, key=lambda i: _area(i[0]), reverse=True)
    kept: List[Tuple[BBox, str]] = []
    for box, kind in allb:
        a = _area(box)
        if a > 0 and any(_inter(box, k[0]) / a > 0.9 for k in kept):
            continue
        kept.append((box, kind))
    return kept


# --------------------------------------------------------------------------- service

class PdfLayoutService:
    """Layout extraction (figures, tables, words) and clip rendering via PyMuPDF."""

    @staticmethod
    def _open(file_bytes: bytes):
        try:
            return pymupdf.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            logger.warning("Cannot open PDF for layout analysis: %s", e)
            return None

    @staticmethod
    def _is_inline_image(nb: Sequence[float], nwords: Sequence[Tuple[float, float, float, float, str]]) -> bool:
        """True for inline formula images (short, or short with same-row text next to them).

        Images with an option label (A./B.) just left of them are option figures and
        are kept so the question gets flagged for review.
        """
        h = nb[3] - nb[1]
        if h >= _INLINE_ROW_MAX_H:
            return False
        row = [w for w in nwords
               if min(w[3], nb[3]) - max(w[1], nb[1]) >= 0.5 * (w[3] - w[1])]
        for w in row:
            if _OPTION_LABEL.match(w[4]) and nb[0] - _OPTION_LABEL_GAP <= w[2] <= nb[0] + _OPTION_X_TOL:
                return False
        if h < _INLINE_MAX_H:
            return True
        return any(nb[0] - _INLINE_ADJ <= w[2] <= nb[0] + 3 or nb[2] - 3 <= w[0] <= nb[2] + _INLINE_ADJ
                   for w in row)

    @classmethod
    def _page_blocks(cls, page, page_no: int) -> List[Block]:
        cropbox = page.cropbox
        page_area = cropbox.width * cropbox.height
        items: List[Tuple[BBox, str]] = []

        tables: List[Any] = []
        try:
            tables = [t.bbox for t in page.find_tables().tables]
        except Exception as e:
            logger.warning("find_tables failed on page %s: %s", page_no, e)
        table_rects = [pymupdf.Rect(t) for t in tables]
        nwords_pt = []
        try:
            nwords_pt = page.get_text("words")
        except Exception:
            pass
        # Normalized words, used to recognise inline formula images.
        nwords: List[Tuple[float, float, float, float, str]] = []
        try:
            for w in page.get_text("words"):
                b = _norm_rect(page, w[:4])
                nwords.append((b[0], b[1], b[2], b[3], w[4]))
        except Exception as e:
            logger.warning("get_text failed on page %s: %s", page_no, e)
        if table_rects:
            # find_tables may report only the text extent; grow each table over the
            # cell/border drawings that touch it so grid strokes are not left behind.
            try:
                draw_rects = [pymupdf.Rect(d["rect"]) for d in page.get_drawings()]
                draw_rects = [r for r in draw_rects if r.width * r.height < 0.9 * page_area
                              and not _is_hairline(_norm_rect(page, r))]
            except Exception:
                draw_rects = []
            for i, tr in enumerate(table_rects):
                # Growth is capped to a small margin around the detected table so that
                # neighbouring graphs touching the grid are not swallowed into the table.
                mx = max(_TABLE_GROW_MARGIN, 0.5 * tr.width)
                my = max(_TABLE_GROW_MARGIN, 0.5 * tr.height)
                limit = pymupdf.Rect(tr.x0 - mx, tr.y0 - my, tr.x1 + mx, tr.y1 + my)
                grown = True
                while grown:
                    grown = False
                    for r in draw_rects:
                        if (r.intersects(tr) and not (r in tr) and (r in limit)
                                and r.width <= tr.width and r.height <= tr.height):
                            tr = tr | r
                            grown = True
                table_rects[i] = tr
        for tr in table_rects:
            nb = _norm_rect(page, tr)
            if (nb[2] - nb[0]) >= _MIN_SIDE and (nb[3] - nb[1]) >= _MIN_SIDE:
                items.append((nb, "table"))

        def in_table(r) -> bool:
            c = pymupdf.Point((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2)
            return any(c in t for t in table_rects)

        try:
            for info in page.get_image_info():
                r = pymupdf.Rect(info["bbox"]) & cropbox
                if r.is_empty or in_table(r):
                    continue
                nb = _norm_rect(page, r)
                if _area(nb) > _MAX_IMAGE_AREA:
                    continue  # full-page scan background
                if _plausible(nb) and not cls._is_inline_image(nb, nwords):
                    items.append((nb, "image"))
        except Exception as e:
            logger.warning("get_image_info failed on page %s: %s", page_no, e)

        try:
            drawings = []
            for d in page.get_drawings():
                r = pymupdf.Rect(d["rect"])
                if page_area and r.width * r.height >= 0.9 * page_area:
                    continue  # page-size background rectangle
                if in_table(r) or _is_hairline(_norm_rect(page, r)):
                    continue
                if d.get("fill") is not None and d.get("color") is None and sum(
                        1 for w in nwords_pt if r.contains(pymupdf.Rect(w[:4]))) >= 2:
                    continue  # filled highlight behind a text line, not a figure
                drawings.append(d)
            if drawings:
                clusters = page.cluster_drawings(drawings=drawings, x_tolerance=3, y_tolerance=3)
                words = [w for w in page.get_text("words") if len(w[4]) <= 12]
                for cr in clusters:
                    cr = pymupdf.Rect(cr)
                    zone = pymupdf.Rect(cr.x0 - 14, cr.y0 - 14, cr.x1 + 14, cr.y1 + 14)
                    for w in words:
                        wr = pymupdf.Rect(w[:4])
                        if wr in zone:
                            cr |= wr  # absorb short labels such as A, B, 60
                    nb = _norm_rect(page, cr)
                    if _plausible(nb):
                        items.append((nb, "drawing"))
        except Exception as e:
            logger.warning("drawing analysis failed on page %s: %s", page_no, e)

        merged = _merge_blocks(items)
        merged = [(b, k) for b, k in merged if k == "table" or _area(b) >= _MIN_AREA]
        merged.sort(key=lambda i: (0 if (i[0][0] + i[0][2]) / 2 < _COLUMN_SPLIT else 1, i[0][1], i[0][0]))
        return [
            Block(id=f"p{page_no}-{k[0]}{idx}", page=page_no,
                  bbox=tuple(round(v, 2) for v in b), kind=k, area=_area(b))
            for idx, (b, k) in enumerate(merged)
        ]

    @classmethod
    def extract_blocks(cls, file_bytes: bytes, pages: Optional[Iterable[int]] = None) -> List[Block]:
        """Detect figure/drawing/table blocks. Returns [] when the PDF cannot be opened."""
        doc = cls._open(file_bytes)
        if doc is None:
            return []
        try:
            wanted = set(pages) if pages is not None else None
            out: List[Block] = []
            for idx in range(doc.page_count):
                if wanted is not None and (idx + 1) not in wanted:
                    continue
                out.extend(cls._page_blocks(doc[idx], idx + 1))
            return out
        finally:
            doc.close()

    @classmethod
    def analyze(cls, file_bytes: bytes) -> PdfLayout:
        """Blocks and normalized words for every page."""
        layout = PdfLayout()
        doc = cls._open(file_bytes)
        if doc is None:
            return layout
        try:
            for idx in range(doc.page_count):
                page = doc[idx]
                n = idx + 1
                layout.blocks_by_page[n] = cls._page_blocks(page, n)
                words: List[Word] = []
                try:
                    for w in page.get_text("words"):
                        b = _norm_rect(page, w[:4])
                        words.append(Word(b[0], b[1], b[2], b[3], w[4], int(w[5]), int(w[6]), int(w[7])))
                except Exception as e:
                    logger.warning("get_text failed on page %s: %s", n, e)
                layout.words_by_page[n] = words
        finally:
            doc.close()
        return layout

    @classmethod
    def extract_words(cls, file_bytes: bytes) -> Dict[int, List[Word]]:
        """Normalized words for every page (no block analysis). {} when the PDF cannot be opened."""
        out: Dict[int, List[Word]] = {}
        doc = cls._open(file_bytes)
        if doc is None:
            return out
        try:
            for idx in range(doc.page_count):
                page = doc[idx]
                words: List[Word] = []
                try:
                    for w in page.get_text("words"):
                        b = _norm_rect(page, w[:4])
                        words.append(Word(b[0], b[1], b[2], b[3], w[4], int(w[5]), int(w[6]), int(w[7])))
                except Exception as e:
                    logger.warning("get_text failed on page %s: %s", idx + 1, e)
                out[idx + 1] = words
        finally:
            doc.close()
        return out

    @staticmethod
    def _pixel_snap(page, box: "pymupdf.Rect", text_rects: Sequence["pymupdf.Rect"] = (),
                    table_rects: Sequence["pymupdf.Rect"] = ()) -> Optional["pymupdf.Rect"]:
        """Bounding box (points) of the dominant ink component overlapping ``box``.

        For scans or shifted boxes: render a padded region at low dpi, threshold to a
        coarse grid and keep the largest connected component that hits the box.
        """
        pr = page.rect
        region = pymupdf.Rect(box.x0 - 0.15 * box.width, box.y0 - 0.15 * box.height,
                              box.x1 + 0.15 * box.width, box.y1 + 0.15 * box.height) & pr
        if region.is_empty:
            return None
        pix = page.get_pixmap(dpi=100, clip=region, colorspace=pymupdf.csGRAY, alpha=False)
        W, H, data, cell = pix.width, pix.height, pix.samples, 4
        zone = region
        sx, sy = region.width / max(1, W), region.height / max(1, H)
        ink = set()
        for y in range(H):
            row = data[y * pix.stride: y * pix.stride + W]
            for x in range(W):
                # Pixels already inside the box are ignored so ink touching the figure (axis
                # arrows, glued titles) cannot merge into one oversized, skipped component.
                if row[x] < 200 and not (box.x0 <= zone.x0 + (x + 0.5) * sx <= box.x1
                                         and box.y0 <= zone.y0 + (y + 0.5) * sy <= box.y1):
                    ink.add((x // cell, y // cell))
        if not ink:
            return None
        seen, comps = set(), []
        for c in ink:
            if c in seen:
                continue
            stack, comp = [c], []
            seen.add(c)
            while stack:
                cx, cy = stack.pop()
                comp.append((cx, cy))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        n = (cx + dx, cy + dy)
                        if n in ink and n not in seen:
                            seen.add(n)
                            stack.append(n)
            xs, ys = [p[0] for p in comp], [p[1] for p in comp]
            r = pymupdf.Rect(region.x0 + min(xs) * cell * sx, region.y0 + min(ys) * cell * sy,
                             region.x0 + (max(xs) + 1) * cell * sx, region.y0 + (max(ys) + 1) * cell * sy)
            comps.append((len(comp), r))
        def text_only(r) -> bool:
            area = max(1.0, r.get_area())
            txt = sum((r & t).get_area() for t in text_rects)
            return txt > 0.5 * area or any((r & t).get_area() > 0.3 * area for t in table_rects)

        hits = [(n, r) for n, r in comps if r.intersects(box) and not text_only(r)]
        if not hits:
            return None
        n0, best = max(hits, key=lambda t: t[0])
        if n0 < 8:
            return None
        grow = pymupdf.Rect(best.x0 - 8, best.y0 - 8, best.x1 + 8, best.y1 + 8)
        for _, r in comps:
            if r != best and (r & grow).get_area() >= 0.3 * r.get_area() and not text_only(r):
                best = best | r
        return best

    @staticmethod
    def _pick_figure_candidate(page, box: "pymupdf.Rect", text_rects: Sequence["pymupdf.Rect"],
                               table_rects: Sequence["pymupdf.Rect"]) -> Optional["pymupdf.Rect"]:
        """Best embedded image / vector drawing cluster for a (possibly shifted) box.

        Ignores page-wide rules, white backgrounds, inline formula images and anything inside
        a table; scores overlap and proximity and prefers clusters with axes-like strokes.
        """
        pr = page.rect
        try:
            keep, strokes = [], []
            for d in page.get_drawings():
                r = pymupdf.Rect(d["rect"])
                if r.get_area() >= 0.5 * pr.get_area() or (r.height < 2 and r.width > 0.5 * pr.width):
                    continue
                if d.get("fill") in ((1.0, 1.0, 1.0), (1, 1, 1)) and d.get("color") is None:
                    continue
                c = (r.tl + r.br) / 2
                if any(c in t for t in table_rects):
                    continue
                keep.append(d)
            cands = []
            for cr in (page.cluster_drawings(drawings=keep, x_tolerance=3, y_tolerance=3) if keep else []):
                cr = pymupdf.Rect(cr) & pr
                axes = False
                for d in keep:
                    r = pymupdf.Rect(d["rect"])
                    if r in cr:
                        strokes.append(r)
                hs = [r for r in strokes if r in cr and r.height < 3 and r.width > 0.5 * cr.width]
                vs = [r for r in strokes if r in cr and r.width < 3 and r.height > 0.5 * cr.height]
                strokes = []
                cands.append((cr, bool(hs and vs)))
            for info in page.get_image_info():
                r = pymupdf.Rect(info["bbox"]) & pr
                if r.height >= 0.04 * pr.height and not r.is_empty:
                    c = (r.tl + r.br) / 2
                    if not any(c in t for t in table_rects):
                        cands.append((r, False))
        except Exception as e:
            logger.warning("snap candidates failed: %s", e)
            return None
        reach = 0.15 * max(pr.width, pr.height)
        bc = (box.tl + box.br) / 2
        best, score = None, 0.0
        for c, axes in cands:
            if c.width < 20 or c.height < 20 or c.get_area() >= 0.5 * pr.get_area():
                continue
            inter = (c & box).get_area()
            cc = (c.tl + c.br) / 2
            dist = ((cc.x - bc.x) ** 2 + (cc.y - bc.y) ** 2) ** 0.5
            if inter <= 0 and dist > 2 * reach:
                continue
            sc = inter / max(1.0, box.get_area()) + inter / max(1.0, c.get_area()) + max(0.0, 1 - dist / (2 * reach)) * 0.5
            if axes:
                sc += 0.3
            if sc > score:
                best, score = c, sc
        return best if score >= 0.25 else None

    @staticmethod
    def _absorb_ink(page, box: "pymupdf.Rect", text_rects: Sequence["pymupdf.Rect"], m: float = 20.0,
                    touch_only: bool = False, skip_rows: Sequence["pymupdf.Rect"] = ()) -> "pymupdf.Rect":
        """Grow ``box`` over small ink components within ``m`` pt that are NOT text-layer glyphs.

        Axis tick labels are often vector glyph paths (no text layer), so neither the
        drawing cluster nor the word lookup sees them; body text is excluded because it
        overlaps text-layer words.
        """
        pr = page.rect
        zone = pymupdf.Rect(box.x0 - m, box.y0 - m, box.x1 + m, box.y1 + m) & pr
        pix = page.get_pixmap(dpi=100, clip=zone, colorspace=pymupdf.csGRAY, alpha=False)
        W, H, cell = pix.width, pix.height, 3
        sx, sy = zone.width / max(1, W), zone.height / max(1, H)
        ink = set()
        for y in range(H):
            row = pix.samples[y * pix.stride: y * pix.stride + W]
            for x in range(W):
                # Pixels already inside the box are ignored so ink touching the figure (axis
                # arrows, glued titles) cannot merge into one oversized, skipped component.
                if row[x] < 200 and not (box.x0 <= zone.x0 + (x + 0.5) * sx <= box.x1
                                         and box.y0 <= zone.y0 + (y + 0.5) * sy <= box.y1):
                    ink.add((x // cell, y // cell))
        seen, out = set(), pymupdf.Rect(box)
        for c in ink:
            if c in seen:
                continue
            stack, xs, ys = [c], [], []
            seen.add(c)
            while stack:
                cx, cy = stack.pop()
                xs.append(cx)
                ys.append(cy)
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        n = (cx + dx, cy + dy)
                        if n in ink and n not in seen:
                            seen.add(n)
                            stack.append(n)
            r = pymupdf.Rect(zone.x0 + min(xs) * cell * sx, zone.y0 + min(ys) * cell * sy,
                             zone.x0 + (max(xs) + 1) * cell * sx, zone.y0 + (max(ys) + 1) * cell * sy)
            if r in box or r.width > 0.5 * box.width or r.height > 0.5 * box.height:
                continue
            if any(min(r.y1, row.y1) - max(r.y0, row.y0) > 0.3 * r.height
                   and max(r.x0 - row.x1, row.x0 - r.x1) < 25 for row in skip_rows):
                continue  # glyph path of a body-text row (inline formula etc.)
            if touch_only and (r & pymupdf.Rect(box.x0 - 8, box.y0 - 8, box.x1 + 8, box.y1 + 8)).is_empty:
                continue
            if any((r & t).get_area() > 0.2 * r.get_area() for t in text_rects):
                continue
            out |= r
        return out

    @classmethod
    def refine_bbox(cls, doc: Any, page_no: int, bbox: Sequence[float], snap: bool = False) -> List[float]:
        """Expand/snap a normalized 0-1000 figure bbox so it keeps its context.

        1. snap=True: move a possibly shifted box onto an embedded image rect / vector
           drawing cluster (digital PDF), else onto the dominant ink component (scans).
        2. Absorb adjacent text lines (axis ticks, axis titles, units, legend, captions):
           short lines (<= 40 chars) touching the ~20pt zone around the box, or lines
           mostly inside it. Body paragraphs and "Cau N" headers are never absorbed.
        3. Pad ~4% and clamp to the page and to the next "Cau N" anchor below the figure.
        Returns the refined normalized bbox (the input when anything fails).
        """
        orig = [float(v) for v in bbox]
        try:
            page = doc[page_no - 1]
            pr = page.rect
            sxn, syn = pr.width / 1000.0, pr.height / 1000.0
            box = pymupdf.Rect(pr.x0 + orig[0] * sxn, pr.y0 + orig[1] * syn,
                               pr.x0 + orig[2] * sxn, pr.y0 + orig[3] * syn) & pr
            if box.is_empty:
                return orig
            rot = page.rotation_matrix
            groups: Dict[Tuple[int, int], List[Any]] = defaultdict(list)
            raw_words = page.get_text("words")
            for w in raw_words:
                groups[(w[5], w[6])].append(w)
            line_items = []
            for ws in groups.values():
                r = pymupdf.Rect(ws[0][:4])
                for w in ws[1:]:
                    r |= pymupdf.Rect(w[:4])
                text = " ".join(w[4] for w in sorted(ws, key=lambda w: w[7]))
                line_items.append((r * rot, text))

            text_rects = [pymupdf.Rect(w[:4]) * rot for w in raw_words]
            table_rects: List[Any] = []
            try:
                table_rects = [pymupdf.Rect(t.bbox) * rot for t in page.find_tables().tables]
            except Exception:
                pass
            if snap:
                cand = cls._pick_figure_candidate(page, box, text_rects, table_rects)
                if cand is not None:
                    box = cand
                else:
                    snapped = cls._pixel_snap(page, box, text_rects, table_rects)
                    if snapped is not None:
                        box = snapped
            base = pymupdf.Rect(box)
            # Running header/footer: short lines in the top/bottom page bands away from the figure,
            # plus page-wide rules there. They are never absorbed and the crop is clamped to them.
            band_lines = [r for r, _ in line_items if not r.is_empty and (
                r.y1 <= pr.y0 + 0.06 * pr.height or r.y0 >= pr.y1 - 0.05 * pr.height)
                and not (r & pymupdf.Rect(base.x0 - 4, base.y0 - 4, base.x1 + 4, base.y1 + 4)).get_area() > 0]
            rules = []
            try:
                for d in page.get_drawings():
                    r = pymupdf.Rect(d["rect"]) * rot
                    if r.height < 2 and r.width > 0.5 * pr.width and (
                            r.y1 <= pr.y0 + 0.08 * pr.height or r.y0 >= pr.y1 - 0.07 * pr.height):
                        rules.append(r)
            except Exception:
                pass
            line_items = [(r, t) for r, t in line_items if not any(r == bl for bl in band_lines)]
            header = re.compile(r"^(Câu|Question|Bài)\s*\d", re.IGNORECASE)
            # Body rows: long lines mostly outside the box. Short fragments on the same row (inline
            # formulas, wrapped words) belong to that paragraph, not to the figure.
            body_rows = [r for r, t in line_items if (len(t) > 40 or r.width > 100) and not r.is_empty
                         and (r & base).width < 0.5 * r.width]
            # Chain fragments of the same text row (gap < 25pt) onto a body row, so inline formula
            # pieces such as "700 kg/m3." or "Biet" are body too.
            chain = [r for r, _t in line_items if not r.is_empty and (r & base).is_empty and r not in body_rows]
            grew = True
            while grew:
                grew = False
                for r in list(chain):
                    if any(min(r.y1, b.y1) - max(r.y0, b.y0) > 0.5 * min(r.height, b.height)
                           and max(r.x0 - b.x1, b.x0 - r.x1) < 25 for b in body_rows):
                        body_rows.append(r)
                        chain.remove(r)
                        grew = True
            def _row_mate(r) -> bool:
                return any(r == b for b in body_rows) and (r & base).is_empty
            m = 20.0
            for _ in range(2):  # second pass picks up labels adjacent to first-pass labels
                zone = pymupdf.Rect(box.x0 - m, box.y0 - m, box.x1 + m, box.y1 + m) & pr
                grown = pymupdf.Rect(box)
                for r, text in line_items:
                    if r.is_empty or header.match(text) or _row_mate(r):
                        continue
                    inter = (r & zone).get_area()
                    if inter <= 0:
                        continue
                    # Only short lines qualify: a long line overlapping the zone is body text.
                    # A longer line sticking mostly outside the box is a wrapped body line beside
                    # the figure, not a label.
                    if len(text) > 20 and (r & box).width < 0.5 * r.width and r.y1 - r.y0 < 40:
                        continue
                    if len(text) <= 40 and (inter >= 0.6 * r.get_area()
                                            or r.width <= 0.9 * max(box.width, 60.0)):
                        grown |= r
                box = grown
            # Far axis titles: a short line on the x-axis row (right of the plot) or on the y-axis
            # column (above the plot) within 45pt of the edge belongs to the figure.
            far = pymupdf.Rect(box)
            for r, text in line_items:
                if r.is_empty or len(text.strip()) > 12 or header.match(text) or _row_mate(r):
                    continue
                cy, cx = (r.y0 + r.y1) / 2, (r.x0 + r.x1) / 2
                if 0 < r.x0 - box.x1 <= 45 and box.y1 - 25 <= cy <= box.y1 + 6:
                    far |= r
                elif 0 < box.y0 - r.y1 <= 45 and box.x0 - 8 <= cx <= box.x0 + 25:
                    far |= r
            box = far
            try:
                box = cls._absorb_ink(page, box, text_rects, skip_rows=body_rows) & pr
                # Axis titles may be vector glyphs wider than the 20pt zone: re-absorb components
                # that touch the grown box until stable (bounded).
                for _ in range(4):
                    nxt = cls._absorb_ink(page, box, text_rects, touch_only=True, skip_rows=body_rows) & pr
                    if nxt == box:
                        break
                    box = nxt
            except Exception as e:
                logger.warning("ink absorption failed on page %s: %s", page_no, e)
            # Stray body text: a long line sticking out sideways past the figure and cutting into
            # its top/bottom edge is not part of the figure; trim the box to the line's far edge.
            for r, text in line_items:
                if r.is_empty or len(text) <= 40 or (r & box).is_empty:
                    continue
                if r.x0 >= base.x0 - 15 and r.x1 <= base.x1 + 15:
                    continue
                # A line merely brushing the box edge (wrapped paragraph beside a figure) is not a
                # leading stray line; require a substantial part of it to sit above the plot.
                # Text wrapped beside a side figure overlaps only a sliver of its width.
                if (r & box).width < 0.3 * r.width or (r & box).width < 0.5 * box.width:
                    continue
                mid = (r.y0 + r.y1) / 2
                if mid < box.y0 + 0.35 * box.height and r.y1 < box.y1:
                    box.y0 = max(box.y0, r.y1 + 0.5)
                elif mid > box.y1 - 0.35 * box.height and r.y0 > box.y0:
                    box.y1 = min(box.y1, r.y0 - 0.5)
            for r in rules + band_lines:
                if (r & box).is_empty or (r & base).get_area() > 0:
                    continue
                if (r.y0 + r.y1) / 2 < pr.y0 + pr.height / 2:
                    box.y0 = max(box.y0, r.y1 + 0.5)
                else:
                    box.y1 = min(box.y1, r.y0 - 0.5)

            nb = [(box.x0 - pr.x0) / sxn, (box.y0 - pr.y0) / syn, (box.x1 - pr.x0) / sxn, (box.y1 - pr.y0) / syn]
            stops = []
            try:
                words = [Word(*_norm_rect(page, w[:4]), w[4], int(w[5]), int(w[6]), int(w[7])) for w in raw_words]
                for a in find_anchors({page_no: words}):
                    if a.number is not None and a.y >= orig[1] + 5 and nb[0] - 300 < a.x < nb[2] and a.y > nb[1]:
                        stops.append(a.y)
            except Exception as e:
                logger.warning("anchor clamp failed on page %s: %s", page_no, e)
            w, h = nb[2] - nb[0], nb[3] - nb[1]
            px, py = max(0.04 * w, 6.0 / sxn), max(0.04 * h, 6.0 / syn)
            out = [max(0.0, nb[0] - px), max(0.0, nb[1] - py), min(1000.0, nb[2] + px), min(1000.0, nb[3] + py)]
            # Padding must not cut into text lines that were not absorbed (body text above/below).
            for r, _t in line_items:
                if r.is_empty or (r & box).get_area() > 0.2 * r.get_area():
                    continue
                if r.x1 <= box.x0 or r.x0 >= box.x1:
                    continue
                ry0, ry1 = (r.y0 - pr.y0) / syn, (r.y1 - pr.y0) / syn
                if ry1 <= nb[1] + 0.5 and out[1] < ry1:
                    out[1] = max(out[1], min(ry1 + 0.5, nb[1]))  # epsilon keeps the line's bottom edge out
                elif ry0 >= nb[3] - 0.5 and out[3] > ry0:
                    out[3] = min(out[3], max(ry0, nb[3]))
            if stops:
                out[3] = min(out[3], max(min(stops) - 2.0, nb[3]))
            return out
        except Exception as e:
            logger.warning("refine_bbox failed on page %s: %s", page_no, e)
            return orig

    @classmethod
    def trim_body_text(cls, doc: Any, page_no: int, crop: Sequence[float], keep: Sequence[float]) -> List[float]:
        """Shrink a normalized 0-1000 crop past body-text lines / header bands / rules on its edges.

        Last step before rendering. ``keep`` (the layout-detected figure box) always stays
        intact. Body text = a line of >= 4 alphabetic words, or >= 2 mostly alphabetic words
        not within ~1.5 line heights of a drawing/image. Text overlapping ``keep``, numbers,
        units and parenthesised tokens are never body text. Returns the input when the PDF
        has no text layer or anything fails.
        """
        out = [float(v) for v in crop]
        try:
            page = doc[page_no - 1]
            raw = page.get_text("words")
            if not raw:
                return out
            kx0, ky0, kx1, ky1 = [float(v) for v in keep]
            groups: Dict[Tuple[int, int], List[Any]] = defaultdict(list)
            for w in raw:
                groups[(w[5], w[6])].append(w)
            lines = []
            for ws in groups.values():
                ws = sorted(ws, key=lambda w: w[7])
                r = _norm_rect(page, (min(w[0] for w in ws), min(w[1] for w in ws),
                                      max(w[2] for w in ws), max(w[3] for w in ws)))
                lines.append((r, [w[4] for w in ws]))
            ink: List[BBox] = []
            try:
                for d in page.get_drawings():
                    nb = _norm_rect(page, d["rect"])
                    if (nb[2] - nb[0]) * (nb[3] - nb[1]) > 0 and min(nb[2] - nb[0], nb[3] - nb[1]) > 1.0:
                        ink.append(nb)
                for im in page.get_image_info():
                    ink.append(_norm_rect(page, im["bbox"]))
            except Exception:
                pass
            rules: List[BBox] = []
            try:
                for d in page.get_drawings():
                    nb = _norm_rect(page, d["rect"])
                    if nb[3] - nb[1] < 3 and nb[2] - nb[0] > 400:
                        rules.append(nb)
            except Exception:
                pass

            def body(r: BBox, toks: List[str]) -> bool:
                alpha = [t for t in toks if len(t) >= 2 and t.isalpha()]
                if len(alpha) < 2 or len(alpha) < 0.6 * len(toks):
                    return False
                if len(alpha) >= 4:
                    return True
                lh = max(r[3] - r[1], 1.0)
                near = any(_inter((r[0] - 1.5 * lh, r[1] - 1.5 * lh, r[2] + 1.5 * lh, r[3] + 1.5 * lh), k) > 0
                           for k in ink)
                return not near

            def side_cut(r: BBox, c: List[float]) -> Optional[Tuple[int, float]]:
                """(index, value) of the cheapest crop edge move that clears ``r`` without touching keep."""
                w, h = c[2] - c[0], c[3] - c[1]
                opts = []
                if r[2] <= kx0 and r[2] <= c[0] + 0.35 * w:
                    opts.append(((r[2] - c[0]) * h, 0, r[2]))
                if r[0] >= kx1 and r[0] >= c[2] - 0.35 * w:
                    opts.append(((c[2] - r[0]) * h, 2, r[0]))
                if r[3] <= ky0 and r[3] <= c[1] + 0.35 * h:
                    opts.append(((r[3] - c[1]) * w, 1, r[3]))
                if r[1] >= ky1 and r[1] >= c[3] - 0.35 * h:
                    opts.append(((c[3] - r[1]) * w, 3, r[1]))
                if not opts:
                    return None
                _a, i, v = min(opts)
                return i, v

            c = list(out)
            # Header/footer bands never belong to a figure unless the figure itself reaches them.
            c[1] = max(c[1], min(60.0, ky0))
            c[3] = min(c[3], max(950.0, ky1))
            for r in rules:
                if _inter(r, c) > 0 and _inter(r, (kx0, ky0, kx1, ky1)) <= 0:
                    cut = side_cut(r, c)
                    if cut:
                        c[cut[0]] = cut[1]
            for r, toks in sorted(lines, key=lambda t: (t[0][1], t[0][0])):
                if _inter(r, c) <= 0 or _inter(r, (kx0, ky0, kx1, ky1)) > 0:
                    continue
                if not body(r, toks):
                    continue
                cut = side_cut(r, c)
                if cut:
                    c[cut[0]] = cut[1] + (0.3 if cut[0] in (0, 1) else -0.3)
            # Safety: the layout box must stay intact.
            return [min(c[0], kx0), min(c[1], ky0), max(c[2], kx1), max(c[3], ky1)]
        except Exception as e:
            logger.warning("trim_body_text failed on page %s: %s", page_no, e)
            return out

    @classmethod
    def render_figure(cls, doc: Any, page_no: int, bbox: Sequence[float], snap: bool = False,
                      dpi: int = 250) -> Optional[bytes]:
        """refine_bbox + render_clip (padding already applied), for figure crops."""
        return cls.render_clip(doc, page_no, cls.refine_bbox(doc, page_no, bbox, snap=snap), dpi=dpi, pad=0.0)

    @staticmethod
    def render_clip(file_bytes: Union[bytes, Any], page: int, bbox: Sequence[float],
                    dpi: int = 250, pad: float = 0.02) -> Optional[bytes]:
        """Render a normalized bbox of a page to PNG bytes (None on failure).

        ``file_bytes`` may also be an already opened pymupdf.Document. PyMuPDF's
        get_pixmap clip is expressed in display (rotated) space, so no derotation
        is applied here.
        """
        from app.core.config import QUESTION_IMAGE_MAX_BYTES

        owns = isinstance(file_bytes, (bytes, bytearray))
        doc = PdfLayoutService._open(bytes(file_bytes)) if owns else file_bytes
        if doc is None:
            return None
        try:
            pg = doc[page - 1]
            pr = pg.rect
            x0, y0, x1, y1 = [float(v) for v in bbox]
            w, h = x1 - x0, y1 - y0
            x0, x1 = x0 - w * pad, x1 + w * pad
            y0, y1 = y0 - h * pad, y1 + h * pad
            clip = pymupdf.Rect(
                pr.x0 + max(0.0, x0) / 1000.0 * pr.width, pr.y0 + max(0.0, y0) / 1000.0 * pr.height,
                pr.x0 + min(1000.0, x1) / 1000.0 * pr.width, pr.y0 + min(1000.0, y1) / 1000.0 * pr.height,
            ) & pr
            if clip.is_empty:
                return None
            data = b""
            for d in [dpi] + [v for v in (200, 150) if v < dpi]:
                data = pg.get_pixmap(dpi=d, clip=clip, alpha=False).tobytes("png")
                if len(data) <= QUESTION_IMAGE_MAX_BYTES:
                    return data
            logger.warning("Clip on page %s exceeds max image size even at lowest dpi", page)
            return None
        except Exception as e:
            logger.warning("render_clip failed on page %s: %s", page, e)
            return None
        finally:
            if owns:
                doc.close()


# --------------------------------------------------------------------------- anchors and regions

def _lines(words: Sequence[Word]) -> List[List[Word]]:
    groups: Dict[Tuple[int, int], List[Word]] = defaultdict(list)
    for w in words:
        groups[(w.block, w.line)].append(w)
    return [sorted(g, key=lambda w: w.wno) for g in groups.values()]


def page_columns(words: Sequence[Word]) -> int:
    """1 or 2 text columns; 2 when under 5% of lines cross the middle gutter (x 480-520)."""
    lines = _lines(words)
    if not lines:
        return 1
    crossing = left = right = 0
    for ln in lines:
        x0, x1 = min(w.x0 for w in ln), max(w.x1 for w in ln)
        if x0 < 480 and x1 > 520:
            crossing += 1
        elif x1 <= 520:
            left += 1
        else:
            right += 1
    if crossing / len(lines) >= 0.05:
        return 1
    # Guard: a one-sided page is not a two-column page.
    return 2 if left >= 3 and right >= 3 else 1


def _column_of(x_centre: float, ncols: int) -> int:
    return 1 if (ncols == 2 and x_centre >= _COLUMN_SPLIT) else 0


def clip_words(words_by_page: Dict[int, List[Word]], start: Optional[Tuple[int, float]] = None,
               end: Optional[Tuple[int, float]] = None) -> Dict[int, List[Word]]:
    """Keep only words inside the (page, y) range [start, end); pages outside it are dropped."""
    out: Dict[int, List[Word]] = {}
    for p, ws in words_by_page.items():
        if start is not None and p < start[0]:
            continue
        if end is not None and p > end[0]:
            continue
        if start is not None and p == start[0]:
            ws = [w for w in ws if w.y0 >= start[1]]
        if end is not None and p == end[0]:
            ws = [w for w in ws if w.y0 < end[1]]
        out[p] = list(ws)
    return out


def _part_from_line(ln: Sequence[Word]) -> Optional[int]:
    """Part index when the line starts a PHẦN block (I/II/III/IV, tolerant), else None."""
    first = unicodedata.normalize("NFC", ln[0].text)
    if not _PART_RE.match(first.rstrip(".:")):
        return None
    if len(ln) > 1:
        tok = unicodedata.normalize("NFC", ln[1].text).strip(".:)").upper()
        if tok in _PART_ROMAN:
            return _PART_ROMAN[tok]
        if tok.isdigit():
            return int(tok)
        if len(tok) == 1 and "A" <= tok <= "F" and ln[1].text.strip(".:)").isupper():
            return 0  # "Phần A/B/C" style: next part
    # Without a numeral only an upper-case "PHẦN" counts (lower case is the word "phần");
    # 0 means "next part".
    return 0 if first.isupper() else None


def find_anchors(words_by_page: Dict[int, List[Word]]) -> List[Anchor]:
    """Question anchors (Câu/Question/Bài + number) and section stoppers, in reading order.

    Each anchor carries the 1-based PHẦN index (``part``) it sits in; the counter
    restarts at every exam header stopper ("ĐỀ SỐ ..."). Pass words clipped to one
    exam (see ``clip_words``) so the numbering filter starts fresh per exam.
    """
    raw: List[Tuple[Anchor, str]] = []
    for page in sorted(words_by_page):
        words = words_by_page[page]
        ncols = page_columns(words)
        for ln in _lines(words):
            first = ln[0]
            col = _column_of((first.x0 + first.x1) / 2, ncols)
            number: Optional[int] = None
            matched = False
            if first.text in _KEYWORDS and len(ln) > 1 and _NUM_TOKEN.match(ln[1].text):
                # Reject answer-key rows such as "Câu 1 2 3 4".
                if not (len(ln) > 2 and ln[2].text.isdigit()):
                    number = int(re.sub(r"\D", "", ln[1].text))
                    matched = True
            else:
                m = _GLUED.match(first.text)
                if m:
                    number, matched = int(m.group(2)), True
            kind = "q"
            part_hint: Optional[int] = None
            if not matched:
                part_hint = _part_from_line(ln)
                text = unicodedata.normalize("NFC", " ".join(w.text for w in ln[:3]))
                if part_hint is not None:
                    number, matched, kind = None, True, "part"
                elif any(text.startswith(s) for s in _STOPPERS):
                    number, matched = None, True
                    kind = "exam" if text.startswith("ĐỀ") else "stop"
            if matched:
                raw.append((Anchor(page, col, first.y0, first.x0, number, part_hint or 0), kind))
    raw.sort(key=lambda t: (t[0].page, t[0].col, t[0].y, t[0].x))
    out: List[Anchor] = []
    last = 0
    part = 0
    for a, kind in raw:
        if a.number is None:
            last = 0
            if kind == "part":
                part = a.part if a.part else part + 1
            elif kind == "exam":
                part = 0
            out.append(Anchor(a.page, a.col, a.y, a.x, None, part))
        elif a.number == last + 1 or a.number == 1:
            last = a.number
            out.append(Anchor(a.page, a.col, a.y, a.x, a.number, part))
    return out


# --------------------------------------------------------------------------- part headings

PART_MC, PART_TF, PART_SHORT, PART_ESSAY = "MC", "TF", "SHORT", "ESSAY"
_POSITIONAL_KIND = {1: PART_MC, 2: PART_TF, 3: PART_SHORT, 4: PART_ESSAY}

def _fold(text: str) -> str:
    """Lower-case, accent-free text ("Đúng/Sai" -> "dung/sai") for keyword tests."""
    t = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    return "".join(c for c in t if unicodedata.category(c) != "Mn")

def classify_part(title: str, index: int) -> str:
    """Question kind of a PHẦN block from its heading text.

    Keywords win; ambiguous headings (e.g. "Thí sinh làm từ câu 1 đến câu 4") fall back
    to the positional default I=MC, II=TF, III=SHORT, IV and later=ESSAY.
    """
    t = _fold(title)
    if re.search(r"dung.*sai", t):
        return PART_TF
    if "tu luan" in t:
        return PART_ESSAY
    if "tra loi ngan" in t:
        return PART_SHORT
    if "nhieu lua chon" in t or "trac nghiem" in t:
        return PART_MC
    return _POSITIONAL_KIND.get(index, PART_ESSAY if index > 4 else PART_MC)

def find_part_headings(words_by_page: Dict[int, List[Word]]) -> Dict[int, str]:
    """{part index: heading text} for the PHẦN headings in reading order.

    Uses the same part counter as ``find_anchors`` (restarts at "ĐỀ SỐ"). The title is the
    heading line plus its wrapped continuation line in the same text block.
    """
    items = []
    for page in sorted(words_by_page):
        words = words_by_page[page]
        ncols = page_columns(words)
        by_key: Dict[Tuple[int, int], List[Word]] = defaultdict(list)
        for w in words:
            by_key[(w.block, w.line)].append(w)
        for (blk, ln_no), ln in by_key.items():
            ln = sorted(ln, key=lambda w: w.wno)
            text = unicodedata.normalize("NFC", " ".join(w.text for w in ln[:3]))
            hint = _part_from_line(ln)
            is_exam = hint is None and text.startswith("ĐỀ SỐ")
            if hint is None and not is_exam:
                continue
            title = " ".join(w.text for w in ln)
            nxt = sorted(by_key.get((blk, ln_no + 1), []), key=lambda w: w.wno)
            if hint is not None and nxt and nxt[0].text not in _KEYWORDS and not _PART_RE.match(nxt[0].text):
                title += " " + " ".join(w.text for w in nxt)
            col = _column_of((ln[0].x0 + ln[0].x1) / 2, ncols)
            items.append((page, col, ln[0].y0, ln[0].x0, hint, is_exam, title))
    items.sort(key=lambda t: t[:4])
    out: Dict[int, str] = {}
    part = 0
    for _, _, _, _, hint, is_exam, title in items:
        if is_exam:
            part = 0
        else:
            part = hint if hint else part + 1
            out[part] = unicodedata.normalize("NFC", title)
    return out

def build_regions(anchors: Sequence[Anchor], page_cols: Dict[int, int],
                  section_end: Optional[Tuple[int, float]] = None) -> List[Region]:
    """Each question anchor owns the flow up to the next anchor, across columns and pages.

    ``section_end`` is the (page, y) where the enclosing exam section stops: the last question
    then flows over every following page up to it (clipped at y on that page) instead of
    stopping after the next page.
    """
    slots: List[Tuple[int, int]] = []
    for p in sorted(page_cols):
        slots.extend((p, c) for c in range(page_cols[p]))
    pos = {s: i for i, s in enumerate(slots)}

    def rect(slot, y0, y1):
        page, col = slot
        x0, x1 = (0.0, 1000.0) if page_cols[page] == 1 else ((0.0, 500.0) if col == 0 else (500.0, 1000.0))
        return (page, x0, y0, x1, y1)

    regions: List[Region] = []
    for i, a in enumerate(anchors):
        if a.number is None or (a.page, a.col) not in pos:
            continue
        si = pos[(a.page, a.col)]
        start = max(0.0, a.y - _ANCHOR_MARGIN)
        nxt = anchors[i + 1] if i + 1 < len(anchors) and (anchors[i + 1].page, anchors[i + 1].col) in pos else None
        rects = []
        if nxt is not None:
            sj = pos[(nxt.page, nxt.col)]
            end = max(0.0, nxt.y - _ANCHOR_MARGIN)
            if sj == si:
                rects.append(rect(slots[si], start, end))
            else:
                rects.append(rect(slots[si], start, 1000.0))
                rects.extend(rect(s, 0.0, 1000.0) for s in slots[si + 1:sj])
                if end > 0:
                    rects.append(rect(slots[sj], 0.0, end))
        else:
            if section_end is not None and section_end[0] == a.page and slots[si][0] == section_end[0]:
                rects.append(rect(slots[si], start, max(start, section_end[1])))
            else:
                rects.append(rect(slots[si], start, 1000.0))
            if section_end is None:
                # Last question: flow at most through the next page.
                rects.extend(rect(s, 0.0, 1000.0) for s in slots[si + 1:] if s[0] <= a.page + 1)
            else:
                for s in slots[si + 1:]:
                    if s[0] > section_end[0]:
                        break
                    rects.append(rect(s, 0.0, section_end[1] if s[0] == section_end[0] else 1000.0))
        regions.append(Region(anchor=a, number=a.number, rects=tuple(rects)))
    return regions


def match_questions(regions: Sequence[Region], questions: Sequence[Any]) -> Dict[int, Region]:
    """Pair regions with questions. Key: id(q).

    Numbers restart per PHẦN, so the pairing key is (part group, number, occurrence).
    Region part indices and question ``part`` labels are both mapped to ordinal groups
    (order of first appearance); this is used only when both sides have the same number
    of groups, otherwise (or when questions carry no part) it falls back to the k-th
    region numbered n <-> k-th question numbered n.
    """
    def groups(keys: Iterable[Any]) -> Dict[Any, int]:
        order: Dict[Any, int] = {}
        for k in keys:
            order.setdefault(k, len(order))
        return order

    qidx = [getattr(q, "part_index", None) for q in questions]
    if questions and all(isinstance(i, int) for i in qidx):
        # Deterministic path: parts already resolved from the PDF headings.
        by_idx: Dict[Tuple[int, int], List[Any]] = defaultdict(list)
        for q, i in zip(questions, qidx):
            by_idx[(i, q.question_number)].append(q)
        seen_i: Dict[Tuple[int, int], int] = defaultdict(int)
        res: Dict[int, Region] = {}
        for r in regions:
            key = (r.part, r.number)
            k = seen_i[key]
            seen_i[key] += 1
            if k < len(by_idx.get(key, [])):
                res[id(by_idx[key][k])] = r
        return res

    qparts = [getattr(q, "part", None) for q in questions]
    use_parts = False
    rg: Dict[Any, int] = {}
    qg: Dict[Any, int] = {}
    if questions and all(isinstance(p, str) and p for p in qparts):
        rg = groups(r.part for r in regions)
        qg = groups(qparts)
        use_parts = len(rg) == len(qg) and len(rg) > 1

    by_key: Dict[Tuple[int, int], List[Any]] = defaultdict(list)
    for q, p in zip(questions, qparts):
        by_key[(qg[p] if use_parts else 0, q.question_number)].append(q)
    seen: Dict[Tuple[int, int], int] = defaultdict(int)
    out: Dict[int, Region] = {}
    for r in regions:
        key = (rg[r.part] if use_parts else 0, r.number)
        k = seen[key]
        seen[key] += 1
        if k < len(by_key.get(key, [])):
            out[id(by_key[key][k])] = r
    return out


def _in_region(region: Region, page: int, x: float, y: float) -> bool:
    return any(p == page and x0 <= x <= x1 and y0 <= y <= y1 for p, x0, y0, x1, y1 in region.rects)


def assign_blocks(regions: Sequence[Region], blocks: Sequence[Block],
                  words_by_page: Dict[int, List[Word]]) -> Dict[int, RegionAssignment]:
    """Assign each block to the region holding its centre (never reused).

    Blocks with an option label (A. / B) just left of them on the same row are option figures.
    Result key: index of the region in `regions`.
    """
    result: Dict[int, RegionAssignment] = {i: RegionAssignment() for i in range(len(regions))}
    for blk in blocks:
        cx, cy = (blk.bbox[0] + blk.bbox[2]) / 2, (blk.bbox[1] + blk.bbox[3]) / 2
        for i, reg in enumerate(regions):
            if not _in_region(reg, blk.page, cx, cy):
                continue
            letter = None
            best_x = -1.0
            for w in words_by_page.get(blk.page, []):
                if not _OPTION_LABEL.match(w.text) or not _in_region(reg, blk.page, w.x0, (w.y0 + w.y1) / 2):
                    continue
                wy = (w.y0 + w.y1) / 2
                if (blk.bbox[1] - _OPTION_Y_TOL <= wy <= blk.bbox[3] + _OPTION_Y_TOL
                        and w.x1 <= blk.bbox[0] + _OPTION_X_TOL and w.x1 >= blk.bbox[0] - _OPTION_LABEL_GAP
                        and w.x1 > best_x):
                    best_x, letter = w.x1, w.text[0]
            if letter and letter not in result[i].options:
                result[i].options[letter] = blk
            else:
                result[i].stem.append(blk)
            break
    return result


def pick_primary(stem_blocks: Sequence[Block], page: Optional[int], llm_bbox: Optional[Sequence[float]]) -> Optional[Block]:
    """Choose the main figure: sole block, else best IoU with the LLM bbox, else largest."""
    if not stem_blocks:
        return None
    if len(stem_blocks) == 1:
        return stem_blocks[0]
    if llm_bbox and page:
        same = [b for b in stem_blocks if b.page == page]
        scored = [(_iou(b.bbox, llm_bbox), b) for b in same]
        scored = [s for s in scored if s[0] > 0]
        if scored:
            return max(scored, key=lambda s: s[0])[1]
    return max(stem_blocks, key=lambda b: b.area)
