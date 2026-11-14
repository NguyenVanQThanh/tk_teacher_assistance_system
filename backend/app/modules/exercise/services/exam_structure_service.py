# File Name: exam_structure_service.py
# Description: LLM pre-pass that reads the exam outline (text layer, or low-res pages) and determines its part structure (types, ranges, counts) before questions are scanned.
# Created At: 2026-11-09
# Created By: AI Agent
# Updated At: 2026-11-09
# Updated By: AI Agent

"""Exam structure analysis.

Teachers lay exams out differently (part titles, order, which part is MC / True-False /
short answer / essay). A cheap text-only LLM call reads an outline of the exam first;
the result is the source of truth for part types in the later vision scan and relabeling.
Any failure falls back to the keyword heuristic (``classify_part``), so import never breaks.
"""

import hashlib
import json
import logging
import re
import unicodedata
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.modules.exercise.services.pdf_layout_service import (
    PART_ESSAY, PART_MC, PART_SHORT, PART_TF, Word, _lines, _column_of, _part_from_line,
    classify_part, page_columns,
)

logger = logging.getLogger("smartlms.exercise.exam_structure")

TYPE_MC, TYPE_TF, TYPE_SHORT, TYPE_ESSAY = "MultipleChoice", "TrueFalse", "ShortAnswer", "Essay"
VALID_TYPES = (TYPE_MC, TYPE_TF, TYPE_SHORT, TYPE_ESSAY)
_KIND_TO_TYPE = {PART_MC: TYPE_MC, PART_TF: TYPE_TF, PART_SHORT: TYPE_SHORT, PART_ESSAY: TYPE_ESSAY}
_TYPE_ALIASES = {
    "multiplechoice": TYPE_MC, "mc": TYPE_MC, "truefalse": TYPE_TF, "tf": TYPE_TF,
    "shortanswer": TYPE_SHORT, "short": TYPE_SHORT, "essay": TYPE_ESSAY,
}

MAX_PARTS = 8
CACHE_SIZE = 64
OUTLINE_MAX_CHARS = 12000
_SNIPPET_CHARS = 160

_ANCHOR_RE = re.compile(r"^(Câu|Question|Bài)\s*(\d{1,3})\b[.:)]?\s*(.*)$", re.IGNORECASE)
_ANSWER_ROW_RE = re.compile(r"^(Câu|Question|Bài)\s*\d{1,3}\s+\d")
_HEADING_RE = re.compile(r"^(PH[ẦA]N|PART|SECTION)\s+[IVXA-Z0-9]{1,4}\b", re.IGNORECASE)
_KEY_RE = re.compile(r"^(ĐÁP ÁN|HƯỚNG DẪN)", re.IGNORECASE)
_OPT_INLINE_RE = re.compile(r"\bA[.)]\s.*\bB[.)]\s.*\bC[.)]\s.*\bD[.)]", re.DOTALL)
_SUB_INLINE_RE = re.compile(r"\ba\)\s.*\bb\)", re.DOTALL)

STRUCTURE_SYSTEM_PROMPT = """Bạn là chuyên gia phân tích cấu trúc đề thi Việt Nam. Bạn được cung cấp BẢN PHÁC THẢO của MỘT đề thi: các dòng tiêu đề phần ([HEADING]), dòng hướng dẫn ([INSTR]) và, với mỗi câu, đoạn đầu của câu hỏi cùng dấu hiệu có các ý a) b) c) d) hoặc phương án A. B. C. D. đi kèm ([QUESTION]).
Nhiệm vụ: xác định các PHẦN của đề và loại câu hỏi của từng phần. Mỗi giáo viên đặt tên phần, thứ tự phần và cách đánh số khác nhau (có thể là PHẦN I/II/III, Phần A/B/C, hoặc không có tiêu đề phần mà đánh số liên tục), hãy dựa vào nội dung, KHÔNG dựa vào vị trí mặc định.
Loại câu (type):
- MultipleChoice: trắc nghiệm nhiều lựa chọn, mỗi câu có phương án A, B, C, D (chọn một).
- TrueFalse: đúng/sai, mỗi câu có một câu dẫn và các ý a), b), c), d) để xét đúng/sai.
- ShortAnswer: trả lời ngắn, đáp án là một số hoặc biểu thức ngắn, không có phương án.
- Essay: tự luận, câu có các ý a), b) hoặc yêu cầu trình bày lời giải.
Quy tắc: các phần theo đúng thứ tự xuất hiện trong đề, "index" bắt đầu từ 1 và tăng dần; "first_question"/"last_question" là số câu hiển thị trong đề (có thể bắt đầu lại từ 1 ở mỗi phần); "question_count" là số câu của phần; "has_answer_key" là true nếu đề đã đánh dấu đáp án trong phần đó; "options_per_question" là số phương án/ý mỗi câu (4 cho trắc nghiệm A-D và đúng/sai a-d, 0 nếu không có).
Chỉ trả về JSON đúng schema, không thêm chữ nào khác."""

STRUCTURE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "parts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "heading": {"type": "string"},
                    "type": {"type": "string", "enum": list(VALID_TYPES)},
                    "first_question": {"type": "integer"},
                    "last_question": {"type": "integer"},
                    "question_count": {"type": "integer"},
                    "has_answer_key": {"type": "boolean"},
                    "options_per_question": {"type": "integer"},
                },
                "required": ["index", "heading", "type", "first_question", "last_question",
                             "question_count", "has_answer_key", "options_per_question"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["parts"],
    "additionalProperties": False,
}


@dataclass
class PartSpec:
    """One part (PHẦN) of an exam."""
    index: int
    heading: str
    type: str
    first_question: int = 1
    last_question: int = 0
    question_count: int = 0
    has_answer_key: bool = False
    options_per_question: int = 0
    # (first_page, last_page) of the part's question anchors, filled by reconcile()
    pages: Optional[Tuple[int, int]] = None


@dataclass
class ExamStructure:
    parts: List[PartSpec] = field(default_factory=list)
    source: str = "llm"  # "llm" | "heuristic"

    def to_hint(self, chunk_pages: Optional[Sequence[int]] = None, missing: Optional[Dict[str, List[int]]] = None) -> str:
        """Vietnamese structure note appended to the vision prompt.

        Only parts overlapping ``chunk_pages`` are listed (all parts when none overlap).
        ``missing`` ({heading: [question numbers]}) turns it into a targeted-retry note.
        """
        parts = self.parts
        if chunk_pages:
            lo, hi = min(chunk_pages), max(chunk_pages)
            sel = [p for p in parts if p.pages and p.pages[0] <= hi and p.pages[1] >= lo]
            parts = sel or parts
        items = []
        for p in parts:
            title = (p.heading or f"PHẦN {p.index}")[:50].strip()
            rng = f"câu {p.first_question}-{p.last_question}" if p.last_question else ""
            n = f"{p.question_count} câu" if p.question_count else ""
            if p.type == TYPE_MC:
                what = "trắc nghiệm nhiều lựa chọn (Part1, MultipleChoice, phương án A-D)"
            elif p.type == TYPE_TF:
                what = "đúng/sai (Part2, TrueFalse, mỗi câu 4 ý a-d là MỘT object)"
            elif p.type == TYPE_SHORT:
                what = "trả lời ngắn (Part3, ShortAnswer, không answer_options)"
            else:
                what = "tự luận -> Part3 ShortAnswer, gộp các ý a), b) vào content, không answer_options"
            items.append(f"{title}: {what} {n} {rng}".replace("  ", " ").strip())
        hint = "Cấu trúc đề này (số câu có thể bắt đầu lại từ 1 ở mỗi phần): " + "; ".join(items) + "."
        hint += " A question may continue on the next page after a page break; merge the continuation into the same question and do not start a new question from continuation text."
        if missing:
            miss = "; ".join(f"{h}: câu {', '.join(str(n) for n in nums)}" for h, nums in missing.items())
            hint += (f" LƯU Ý: lần quét trước bị THIẾU các câu sau: {miss}. "
                     "Chỉ bóc tách ĐÚNG các câu thiếu này (giữ nguyên số câu), bỏ qua mọi câu khác.")
        return hint


# --------------------------------------------------------------------------- outline

def build_outline(words_by_page: Dict[int, List[Word]]) -> str:
    """Cheap text-only outline of one exam section: headings, instructions, question snippets.

    Words must already be clipped to the exam section. Returns "" without a text layer.
    """
    entries: List[Tuple[str, str]] = []  # (kind, text)
    last = 0
    instr_left = 0
    cur: Optional[Dict[str, Any]] = None

    def flush():
        nonlocal cur
        if cur is not None:
            block = cur["block"]
            if _OPT_INLINE_RE.search(block) or cur["opts"] >= 2:
                follow = "options A-D"
            elif _SUB_INLINE_RE.search(block) or cur["subs"] >= 2:
                follow = "sub-items a-d"
            else:
                follow = "none"
            entries.append(("Q", f"Câu {cur['n']}: {cur['snippet'][:_SNIPPET_CHARS]} | follows: {follow}"))
            cur = None

    for page in sorted(words_by_page):
        words = words_by_page[page]
        ncols = page_columns(words)
        lines = []
        for ln in _lines(words):
            lines.append((_column_of((ln[0].x0 + ln[0].x1) / 2, ncols), ln[0].y0, ln[0].x0, ln))
        lines.sort(key=lambda t: t[:3])
        for _, _, _, ln in lines:
            text = unicodedata.normalize("NFC", " ".join(w.text for w in ln)).strip()
            if not text:
                continue
            m = _ANCHOR_RE.match(text)
            if m and not _ANSWER_ROW_RE.match(text) and (int(m.group(2)) == last + 1 or int(m.group(2)) == 1):
                flush()
                last = int(m.group(2))
                instr_left = 0
                cur = {"n": last, "snippet": m.group(3).strip(), "block": text, "opts": 0, "subs": 0}
                continue
            if _part_from_line(ln) is not None or _HEADING_RE.match(text):
                flush()
                last, instr_left = 0, 3
                entries.append(("H", text[:200]))
                continue
            if _KEY_RE.match(text):
                flush()
                entries.append(("K", text[:120]))
                continue
            if cur is not None:
                cur["block"] = (cur["block"] + " " + text)[:2000]
                if len(cur["snippet"]) < _SNIPPET_CHARS:
                    cur["snippet"] = (cur["snippet"] + " " + text).strip()
                if re.match(r"^[A-D][.)]\s", text):
                    cur["opts"] += 1
                elif re.match(r"^[a-d]\)\s", text):
                    cur["subs"] += 1
            elif instr_left > 0:
                instr_left -= 1
                entries.append(("I", text[:200]))
    flush()
    tag = {"H": "[HEADING]", "I": "[INSTR]", "Q": "[QUESTION]", "K": "[ANSWERKEY]"}
    out = "\n".join(f"{tag[k]} {t}" for k, t in entries)
    if not any(k == "Q" for k, _ in entries):
        return ""
    return out[:OUTLINE_MAX_CHARS]


# --------------------------------------------------------------------------- parsing and validation

def parse_structure(raw: str) -> ExamStructure:
    """Parse and validate the LLM JSON. Raises ValueError on any problem."""
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        data = json.loads(text)
    except Exception as e:
        raise ValueError(f"invalid JSON: {e}")
    items = data.get("parts") if isinstance(data, dict) else data
    if not isinstance(items, list) or not items or len(items) > MAX_PARTS:
        raise ValueError("missing or oversized parts list")
    parts: List[PartSpec] = []
    prev_index = 0
    for it in items:
        if not isinstance(it, dict):
            raise ValueError("part is not an object")
        ptype = _TYPE_ALIASES.get(str(it.get("type", "")).replace(" ", "").replace("_", "").lower())
        if ptype is None:
            raise ValueError(f"unknown part type {it.get('type')!r}")
        try:
            index = int(it["index"])
            first = int(it.get("first_question") or 1)
            last = int(it.get("last_question") or 0)
            count = int(it.get("question_count") or 0)
            opts = int(it.get("options_per_question") or 0)
        except (KeyError, TypeError, ValueError):
            raise ValueError("non-integer field in part")
        if index <= prev_index:
            raise ValueError("part indexes are not strictly increasing")
        if last and last < first:
            raise ValueError("last_question before first_question")
        prev_index = index
        parts.append(PartSpec(index, str(it.get("heading") or "").strip(), ptype, first, last,
                              count or (last - first + 1 if last else 0),
                              bool(it.get("has_answer_key", False)), opts))
    return ExamStructure(parts=parts, source="llm")


def map_regions(structure: ExamStructure, regions: Sequence[Any], headings: Dict[int, str]) -> List[PartSpec]:
    """PartSpec owning each layout region (parallel to ``regions``).

    Heuristic structures map by the layout PHẦN index. LLM structures map heading k to
    part k when the counts agree, otherwise by walking question numbers in reading order
    (a number that is not previous+1 means a new part started).
    """
    parts = structure.parts
    if structure.source == "heuristic":
        by_idx = {p.index: p for p in parts}
        default = by_idx.get(0) or PartSpec(0, "", TYPE_MC)
        return [by_idx.get(r.part, default) for r in regions]

    by_heading: Dict[int, PartSpec] = {}
    if headings and len(headings) == len(parts):
        by_heading = dict(zip(sorted(headings), parts))
    out: List[PartSpec] = []
    k, prev = 0, None
    for r in regions:
        if by_heading and r.part in by_heading:
            out.append(by_heading[r.part])
            continue
        start = k if (prev is None or r.number == prev + 1) else k + 1
        for j in range(start, len(parts)):
            lo, hi = parts[j].first_question, parts[j].last_question or 10 ** 6
            if lo <= r.number <= hi:
                k = j
                break
        else:
            k = min(start, len(parts) - 1)
        prev = r.number
        out.append(parts[k])
    return out


_SUB_START_RE = re.compile(r"^\s*\(?[a-dA-D]\)")
_OPT_LABEL_RE = re.compile(r"^\s*[A-D][.)]")


def _question_type_guess(q: Any) -> str:
    """Part type a parsed question looks like, from its type, options and stem."""
    opts = [o.content or "" for o in (q.answer_options or [])]
    qt = getattr(q.question_type, "value", q.question_type)
    if len(opts) >= 2 and all(re.match(r"^\s*\(?[a-d]\)", o) for o in opts):
        return TYPE_TF
    if len(opts) >= 2:
        return TYPE_MC
    if not opts and qt == "MultipleChoice":
        return TYPE_MC
    return TYPE_SHORT  # also covers essay (both are ShortAnswer rows)


def _compatible(spec_type: str, guess: str) -> bool:
    if guess == TYPE_SHORT:
        return spec_type in (TYPE_SHORT, TYPE_ESSAY)
    return spec_type == guess


def _fullness(q: Any) -> Tuple[int, int]:
    return (len(q.answer_options or []), len(q.content or ""))


def match_to_skeleton(questions: Sequence[Any], regions: Sequence[Any], specs: Sequence[PartSpec],
                      preset: Optional[Dict[int, int]] = None,
                      label: Optional[str] = None,
                      region_text: Optional[Dict[int, List[str]]] = None) -> Dict[int, int]:
    """Pair model questions with skeleton regions (text-layer anchors) -> {question index: region index}.

    The skeleton (part and number per region) is authoritative; a model question can only fill
    a slot that exists. Pass 1 pairs by number and a compatible type; pass 2 lets a mistyped
    question take an unused slot with the same number. When two questions compete for one slot
    the fuller copy wins. Questions left over are not part of the skeleton: they are dropped
    by the caller after a WARNING logged here.
    """
    pairs: Dict[int, int] = dict(preset or {})
    owner: Dict[int, int] = {ri: qi for qi, ri in pairs.items()}
    by_number: Dict[int, List[int]] = {}
    for ri, reg in enumerate(regions):
        by_number.setdefault(reg.number, []).append(ri)

    def sub_like(q: Any) -> bool:
        txt = q.content or ""
        return bool(re.search(r"(^|\n|\s)a\)\s", txt) and re.search(r"(\n|\s)b\)\s", txt))

    pending = [qi for qi in range(len(questions)) if qi not in pairs]
    if region_text:
        # Same number in several parts: serve the (question, slot) pairs with the best text match
        # first, so stream order cannot hand a slot to the wrong question.
        from app.modules.exercise.services.verbatim_guard_service import similarity

        def _score(qi: int) -> float:
            q = questions[qi]
            model = " ".join([q.content or ""] + [o.content or "" for o in (q.answer_options or [])])
            ris = [ri for ri in by_number.get(q.question_number, []) if ri not in owner]
            return max((similarity(region_text.get(ri, []), model) for ri in ris), default=0.0) if len(ris) > 1 else 0.0
        pending.sort(key=lambda qi: -_score(qi))
    leftovers: List[int] = []
    for qi in pending:
        q = questions[qi]
        if _SUB_START_RE.match(q.content or "") and len(q.answer_options or []) <= 1:
            leftovers.append(qi)  # a stray true/false statement is never a skeleton item
            continue
        guess = _question_type_guess(q)
        cands = [ri for ri in by_number.get(q.question_number, []) if _compatible(specs[ri].type, guess)]
        free = [ri for ri in cands if ri not in owner]
        if region_text and len(cands) > 1:
            from app.modules.exercise.services.verbatim_guard_service import similarity
            model = " ".join([q.content or ""] + [o.content or "" for o in (q.answer_options or [])])
            best = max(cands, key=lambda ri: similarity(region_text.get(ri, []), model))
            if similarity(region_text.get(best, []), model) >= 0.5:
                # The slot this text belongs to wins; if it is taken this is a duplicate copy,
                # never a reason to fill a different part's slot.
                cands = [best]
                free = [best] if best not in owner else []
        if len(free) > 1 and region_text:
            # Same number in several parts: the slot whose PDF text matches the question wins.
            from app.modules.exercise.services.verbatim_guard_service import similarity
            model = " ".join([q.content or ""] + [o.content or "" for o in (q.answer_options or [])])
            free.sort(key=lambda ri: -similarity(region_text.get(ri, []), model))
            logger.info("Exam '%s': question '%s' candidate slots (region, part, similarity) %s", label,
                        (q.content or "")[:20].replace(chr(10), " "),
                        [(ri, regions[ri].part, round(similarity(region_text.get(ri, []), model), 2)) for ri in free])
        elif guess == TYPE_SHORT and len(free) > 1:
            want = TYPE_ESSAY if sub_like(q) else TYPE_SHORT
            free.sort(key=lambda ri: specs[ri].type != want)
        if free:
            pairs[qi] = free[0]
            owner[free[0]] = qi
        elif cands:
            # Duplicate of a filled slot: keep the fuller copy.
            ri = cands[0]
            cur = owner[ri]
            if cur in pairs and ri == pairs[cur] and cur not in (preset or {}) and _fullness(q) > _fullness(questions[cur]):
                del pairs[cur]
                leftovers.append(cur)
                pairs[qi] = ri
                owner[ri] = qi
            else:
                leftovers.append(qi)
        else:
            leftovers.append(qi)
    still = []
    for qi in leftovers:
        q = questions[qi]
        if qi in pairs:
            continue
        free = [ri for ri in by_number.get(q.question_number, []) if ri not in owner]
        if region_text and free:
            from app.modules.exercise.services.verbatim_guard_service import similarity
            model = " ".join([q.content or ""] + [o.content or "" for o in (q.answer_options or [])])
            taken = [ri for ri in by_number.get(q.question_number, []) if ri in owner]
            # Skip only when a different, already filled slot is clearly this text's real home.
            home = max((similarity(region_text.get(ri, []), model) for ri in taken), default=0.0)
            if home >= 0.5 and all(similarity(region_text.get(ri, []), model) < home - 0.2 for ri in free):
                free = []
        if free and not (_SUB_START_RE.match(q.content or "") and len(q.answer_options or []) <= 1):
            pairs[qi] = free[0]
            owner[free[0]] = qi
        else:
            still.append(qi)
    for qi in still:
        q = questions[qi]
        logger.warning("Exam '%s': dropped question number=%s outside the layout skeleton: %s",
                       label, q.question_number, (q.content or "")[:60].replace("\n", " "))
    return pairs


def _sanitize_types(structure: ExamStructure) -> None:
    """Repair LLM part types that contradict the heading text (the LLM is not deterministic).

    A heading with an unambiguous keyword wins over the LLM. A second TrueFalse part without
    the "dung/sai" keyword is an LLM slip (e.g. PHẦN IV "Thí sinh làm từ câu 1 đến câu 3"):
    it falls back to the positional default of the heading heuristic.
    """
    from app.modules.exercise.services.pdf_layout_service import classify_part, _fold
    seen_tf = False
    for p in structure.parts:
        kind = _KIND_TO_TYPE[classify_part(p.heading, p.index)]
        folded = _fold(p.heading or "")
        keyed = bool(re.search(r"dung.*sai|tu luan|tra loi ngan|nhieu lua chon|trac nghiem", folded))
        if keyed and kind != p.type:
            logger.info("Structure part %d: type %s overridden by heading keyword -> %s", p.index, p.type, kind)
            p.type = kind
        elif p.type == TYPE_TF and seen_tf:
            logger.info("Structure part %d: duplicate TrueFalse without keyword -> %s", p.index, kind)
            p.type = kind
        seen_tf = seen_tf or p.type == TYPE_TF


def reconcile(structure: ExamStructure, regions: Sequence[Any], headings: Dict[int, str]) -> ExamStructure:
    """Prefer layout anchor counts over LLM counts. Raises ValueError when the structure
    cannot explain the layout (a part without any question anchor)."""
    if not regions or structure.source == "heuristic":
        return structure
    _sanitize_types(structure)
    specs = map_regions(structure, regions, headings)
    for p in structure.parts:
        rs = [r for r, s in zip(regions, specs) if s is p]
        if not rs:
            raise ValueError(f"part {p.index} has no question anchors in the layout")
        if p.question_count != len(rs):
            logger.info("Structure part %d: LLM count %d, layout count %d (using layout)",
                        p.index, p.question_count, len(rs))
        nums = [r.number for r in rs]
        p.first_question, p.last_question, p.question_count = min(nums), max(nums), len(rs)
        p.pages = (min(r.anchor.page for r in rs), max(r.anchor.page for r in rs))
    return structure


def heuristic_structure(headings: Dict[int, str], regions: Sequence[Any] = ()) -> ExamStructure:
    """Keyword/positional structure (classify_part); also used when the LLM pass fails."""
    parts = [PartSpec(i, h, _KIND_TO_TYPE[classify_part(h, i)]) for i, h in sorted(headings.items())]
    if any(getattr(r, "part", 0) == 0 for r in regions):
        parts.insert(0, PartSpec(0, "", _KIND_TO_TYPE[classify_part("", 0)]))
    for p in parts:
        rs = [r for r in regions if r.part == p.index]
        if rs:
            nums = [r.number for r in rs]
            p.first_question, p.last_question, p.question_count = min(nums), max(nums), len(rs)
            p.pages = (min(r.anchor.page for r in rs), max(r.anchor.page for r in rs))
    return ExamStructure(parts=parts, source="heuristic")


# --------------------------------------------------------------------------- entry point

_CACHE: "OrderedDict[Tuple[str, str], ExamStructure]" = OrderedDict()


def file_hash(file_bytes: bytes) -> str:
    return hashlib.sha1(file_bytes).hexdigest()


def clear_cache() -> None:
    _CACHE.clear()


def _call_llm(source: Any, provider: Any) -> ExamStructure:
    """One text-only (or low-res image) chat call; one retry (without strict schema) on call or JSON failure."""
    if isinstance(source, str):
        user_text, images = "BẢN PHÁC THẢO ĐỀ THI:\n" + source, None
    else:
        user_text = "Đọc các trang đề thi đính kèm và xác định cấu trúc các phần."
        images = list(source)
    last_err: Optional[Exception] = None
    for strict in (True, False):
        try:
            return parse_structure(provider.complete_json(
                STRUCTURE_SYSTEM_PROMPT, user_text, images=images,
                schema=STRUCTURE_SCHEMA if strict else None, max_tokens=4096, timeout=90.0,
            ))
        except Exception as e:
            last_err = e
            logger.warning("Structure LLM call failed (strict=%s): %s", strict, e)
    raise RuntimeError(f"structure LLM call failed: {last_err}")


def analyze_structure(source: Any, provider: Any, *, regions: Sequence[Any] = (),
                      headings: Optional[Dict[int, str]] = None,
                      cache_key: Optional[Tuple[str, str]] = None) -> ExamStructure:
    """Determine the exam structure with the LLM; never raises.

    ``source`` is the outline text from ``build_outline`` or a list of low-res page images.
    ``regions``/``headings`` are the layout anchors used to reconcile counts and to build the
    heuristic fallback. Results (including fallbacks) are cached by ``cache_key``.
    """
    headings = headings or {}
    if cache_key is not None and cache_key in _CACHE:
        _CACHE.move_to_end(cache_key)
        return _CACHE[cache_key]
    try:
        if provider is None or not hasattr(provider, "complete_json"):
            raise RuntimeError("no structure-capable provider")
        structure = reconcile(_call_llm(source, provider), regions, headings)
    except Exception as e:
        logger.warning("Exam structure analysis failed (%s); falling back to heading heuristic.", e)
        structure = heuristic_structure(headings, regions)
    if cache_key is not None:
        _CACHE[cache_key] = structure
        while len(_CACHE) > CACHE_SIZE:
            _CACHE.popitem(last=False)
    return structure
