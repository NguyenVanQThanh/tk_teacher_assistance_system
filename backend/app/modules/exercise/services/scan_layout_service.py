# File Name: scan_layout_service.py
# Description: Model-based layout skeleton (exam sections, part headings, question anchors) for PDFs without a text layer.
# Created At: 2026-11-11
# Created By: AI Agent
# Updated At: 2026-11-11
# Updated By: AI Agent

"""Scan layout synthesis.

Text-layer PDFs get their skeleton (exam headers, PHAN headings, question anchors) from word
positions. A scanned PDF has none, so a cheap per-page vision read supplies the same facts.
They are converted to the objects the text-layer path produces (section dicts, Anchor/Region,
headings dict) so match_to_skeleton / relabel / placeholders work unchanged.
Any failure returns None and the caller keeps the legacy no-skeleton behaviour.
"""

import json
import logging
import re
import unicodedata
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from app.modules.exercise.services.pdf_layout_service import Anchor, build_regions

logger = logging.getLogger("smartlms.exercise.scan_layout")

CACHE_SIZE = 16
_CACHE: "OrderedDict[str, ScanLayout]" = OrderedDict()
_FIRST_PART_RE = re.compile(r"^\s*(PH[ẦẨA]N|PART)\s+(I|1)\b(?![IVX])", re.IGNORECASE)
_HEADER_BAND = 15.0  # cut this far above an exam header (title block sits just above it)

LAYOUT_SYSTEM_PROMPT = """Bạn đọc BỐ CỤC của MỘT trang đề thi (ảnh scan). Không chép nội dung câu hỏi.
Trả về JSON: {"exam_headers":[{"label":"ĐỀ SỐ 2","y":120}],"parts":[{"heading":"PHẦN I. Câu trắc nghiệm...","y":300,"col":0}],"questions":[{"number":1,"y":340,"col":0,"snippet":"<tối đa 80 ký tự đầu câu>","follows":"options|subitems|none"}]}
- exam_headers: tiêu đề mỗi đề trên trang (ĐỀ SỐ n, MÃ ĐỀ nnn...). Bỏ qua tiêu đề lặp ở đầu/cuối trang nếu cùng đề; để mảng rỗng nếu không có.
- parts: LIỆT KÊ TẤT CẢ tiêu đề PHẦN (PHẦN I..IV, Phần 1...) bắt đầu trên trang này, kể cả khi hai tiêu đề nằm sát nhau trên cùng một trang (mỗi tiêu đề một phần tử riêng, đúng thứ tự, có y riêng). Số câu hỏi thường bắt đầu lại từ 1 sau mỗi PHẦN.
- questions: MỖI nhãn "Câu N" bắt đầu trên trang này (chỉ nhãn bắt đầu câu, không phải chữ "câu" trong lời văn). "follows": có phương án A-D, ý a)-d), hoặc không.
- y: vị trí dọc của dòng, thang 0-1000 (0 đỉnh trang). col: cột (0 trái, 1 phải; trang một cột luôn là 0).
Chỉ trả JSON."""


@dataclass
class ScanLayout:
    """Synthetic skeleton: one entry per exam section (same dicts detect_pdf_exam_sections returns)."""
    sections: List[Dict[str, Any]] = field(default_factory=list)


# --------------------------------------------------------------------------- page read

def parse_page_read(raw: str) -> Dict[str, List[Dict[str, Any]]]:
    """Tolerant parse of one page read. Raises ValueError when it is not a JSON object."""
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", (raw or "").strip())
    try:
        data = json.loads(text)
    except Exception as e:
        raise ValueError(f"invalid JSON: {e}")
    if not isinstance(data, dict):
        raise ValueError("page read is not an object")
    out: Dict[str, List[Dict[str, Any]]] = {}
    for key in ("exam_headers", "parts", "questions"):
        items = data.get(key) or []
        out[key] = [it for it in items if isinstance(it, dict)] if isinstance(items, list) else []
    return out


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return max(0.0, min(1000.0, float(value)))
    except (TypeError, ValueError):
        return default


def read_page(image: Any, provider: Any) -> Dict[str, List[Dict[str, Any]]]:
    """One low-res layout call for a page; one retry on call or JSON failure."""
    last: Optional[Exception] = None
    for _ in range(2):
        try:
            raw = provider.complete_json(LAYOUT_SYSTEM_PROMPT, "Đọc bố cục trang đề thi đính kèm.",
                                         images=[image], schema=None, max_tokens=6000, timeout=150.0)
            return parse_page_read(raw)
        except Exception as e:
            last = e
            logger.warning("Scan layout page read failed: %s", e)
    raise RuntimeError(f"layout read failed: {last}")


# --------------------------------------------------------------------------- synthesis

def build_layout(page_reads: Dict[int, Dict[str, List[Dict[str, Any]]]], total_pages: int,
                 label_fn: Optional[Callable[[str], Optional[str]]] = None) -> Optional[ScanLayout]:
    """Convert per-page reads to sections with regions; None when the reads are unusable.

    Each section dict is the text-layer shape (label, pages, start, end) plus
    ``scan_layout`` = (regions, headings). Unusable: no part heading, no question, or
    question numbers that do not increase within an (exam, part).
    """
    events: List[Tuple[int, int, float, int, str, Dict[str, Any]]] = []
    for page, read in page_reads.items():
        for it in read.get("exam_headers", []):
            raw = unicodedata.normalize("NFC", str(it.get("label") or "")).strip()
            label = label_fn(raw) if label_fn else re.sub(r"\s+", " ", raw).upper()
            if label:
                events.append((page, 0, _num(it.get("y")), 0, "exam", {"label": label}))
        for it in read.get("parts", []):
            events.append((page, int(_num(it.get("col"))), _num(it.get("y")), 1, "part",
                           {"heading": unicodedata.normalize("NFC", str(it.get("heading") or "")).strip()}))
        for it in read.get("questions", []):
            try:
                n = int(it.get("number"))
            except (TypeError, ValueError):
                continue
            events.append((page, int(_num(it.get("col"))), _num(it.get("y")), 2, "q",
                           {"number": n, "snippet": str(it.get("snippet") or "")[:80],
                            "follows": str(it.get("follows") or "")}))
    events.sort(key=lambda e: e[:4])

    ncols: Dict[int, int] = {}
    for page, col, _, _, kind, _ in events:
        if kind == "q":
            ncols[page] = max(ncols.get(page, 1), min(col, 1) + 1)

    exams: List[Dict[str, Any]] = []
    cur: Optional[Dict[str, Any]] = None
    any_part = any_q = False
    for page, col, y, _, kind, data in events:
        if kind == "exam":
            if cur is not None and cur["label"] == data["label"]:
                cur["dup"] = (page, y, len(cur["anchors"]))  # repeated header: running header or a missed label
                continue
            cut = max(0.0, y - _HEADER_BAND)
            if cur is None and (page > 1 or cut > 150):
                exams.append({"label": None, "start": None, "anchors": [], "headings": {}, "part": 0})
            first_exam = cur is None and not exams
            cur = {"label": data["label"], "start": None if first_exam else (page, cut),
                   "anchors": [], "headings": {}, "part": 0}
            exams.append(cur)
            continue
        if cur is None:
            cur = {"label": None, "start": None, "anchors": [], "headings": {}, "part": 0}
            exams.append(cur)
        if kind == "part":
            dup = cur.get("dup")
            if (cur["part"] >= 2 and dup and dup[2] == len(cur["anchors"]) and _FIRST_PART_RE.match(data["heading"])):
                # PHAN I again right after a repeated exam header: the exam label was misread, new exam starts there.
                cur = {"label": cur["label"], "start": (dup[0], max(0.0, dup[1] - _HEADER_BAND)),
                       "anchors": [], "headings": {}, "part": 0}
                exams.append(cur)
            cur["part"] += 1
            cur["headings"][cur["part"]] = data["heading"]
            any_part = True
        else:
            any_q = True
            col = min(col, 1)
            prev = cur["anchors"][-1] if cur["anchors"] else None
            if prev is not None and prev.part == cur["part"] and data["number"] < prev.number:
                # Numbering restarted (or went back) with no heading read: a new part began.
                # Empty heading -> classify_part falls back to the positional default (I MC .. IV essay).
                cur["part"] += 1
                cur["headings"][cur["part"]] = ""
                logger.warning("Scan layout: question %d after %d without a part heading; synthesized part %d",
                               data["number"], prev.number, cur["part"])
            cur["anchors"].append(Anchor(page=page, col=col, y=y, x=0.0 if col == 0 else 500.0,
                                         number=data["number"], part=cur["part"]))
            cur.setdefault("meta", {})[(cur["part"], data["number"])] = data
    if not (any_part and any_q):
        return None

    sections: List[Dict[str, Any]] = []
    for idx, ex in enumerate(exams):
        nxt = exams[idx + 1] if idx + 1 < len(exams) else None
        start = ex["start"]
        end = nxt["start"] if nxt else None
        first = start[0] if start else 1
        last = end[0] if end else total_pages
        # Drop an immediate repeat of the previous number (label printed twice), reject regressions.
        kept: List[Anchor] = []
        for a in ex["anchors"]:
            prev = kept[-1] if kept and kept[-1].part == a.part else None
            if prev is not None and a.number == prev.number:
                continue
            if prev is not None and a.number < prev.number:
                logger.warning("Scan layout: numbers regress in exam '%s' part %d (%d after %d)",
                               ex["label"], a.part, a.number, prev.number)
                return None
            kept.append(a)
        pages = list(range(first, last + 1))
        regions = build_regions(kept, {p: ncols.get(p, 1) for p in pages}, section_end=end)
        sections.append({"label": ex["label"], "pages": pages, "start": start, "end": end,
                         "scan_layout": (regions, dict(ex["headings"])),
                         "scan_meta": ex.get("meta", {})})
    return ScanLayout(sections=sections)


def build_scan_outline(section: Dict[str, Any]) -> str:
    """Text outline (same tags as exam_structure_service.build_outline) from a synthetic section."""
    regions, headings = section["scan_layout"]
    meta = section.get("scan_meta", {})
    lines: List[str] = []
    shown = set()
    for r in regions:
        if r.part not in shown and r.part in headings:
            shown.add(r.part)
            lines.append(f"[HEADING] {headings[r.part][:200]}")
        m = meta.get((r.part, r.number), {})
        follow = {"options": "options A-D", "subitems": "sub-items a-d"}.get(m.get("follows", ""), "none")
        lines.append(f"[QUESTION] Câu {r.number}: {m.get('snippet', '')} | follows: {follow}")
    return "\n".join(lines)


def synthesize_layout(file_hash: str, page_images: Sequence[Any], provider: Any,
                      label_fn: Optional[Callable[[str], Optional[str]]] = None) -> Optional[ScanLayout]:
    """Skeleton for a no-text-layer PDF from per-page vision reads (cached by file hash). Never raises."""
    if file_hash in _CACHE:
        _CACHE.move_to_end(file_hash)
        return _CACHE[file_hash]
    try:
        if provider is None or not hasattr(provider, "complete_json") or not page_images:
            return None
        reads = {p: read_page(img, provider) for p, img in enumerate(page_images, 1)}
        layout = build_layout(reads, len(page_images), label_fn)
    except Exception as e:
        logger.warning("Scan layout synthesis failed (%s); using the legacy no-skeleton path.", e)
        return None
    if layout is None:
        logger.warning("Scan layout inconsistent; using the legacy no-skeleton path.")
        return None
    _CACHE[file_hash] = layout
    while len(_CACHE) > CACHE_SIZE:
        _CACHE.popitem(last=False)
    return layout


def clear_cache() -> None:
    _CACHE.clear()
