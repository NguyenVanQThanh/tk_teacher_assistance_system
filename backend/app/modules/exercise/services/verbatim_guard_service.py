# File Name: verbatim_guard_service.py
# Description: Flags parsed questions whose text differs from the PDF text layer (model paraphrase or dropped sentences).
# Created At: 2026-11-11
# Created By: AI Agent
# Updated At: 2026-11-11
# Updated By: AI Agent

import logging
import re
import unicodedata
from collections import Counter
from typing import Any, Dict, List, Sequence

logger = logging.getLogger("smartlms.exercise.verbatim_guard")

REVIEW_REASON = "Text may differ from the source; compare with the PDF"
MIN_SIMILARITY = 0.85
_WORD = re.compile(r"^[^\W\d_]{3,}$")
_MATH = re.compile(r"\$[^$]*\$|\\\([^)]*\\\)|\\\[[^\]]*\\\]")


def _tokens(words: Sequence[str]) -> Counter:
    """Alphabetic word tokens (len >= 3) after trimming punctuation; math/symbol tokens are ignored."""
    out: Counter = Counter()
    for w in words:
        w = unicodedata.normalize("NFC", w).casefold().strip(".,;:?!()\"'")
        if _WORD.match(w) and w != "câu":
            out[w] += 1
    return out


def similarity(layer_words: Sequence[str], model_text: str) -> float:
    """Dice overlap of word multisets (1.0 = same words). Math is stripped from the model text."""
    a, b = _tokens(layer_words), _tokens(_MATH.sub(" ", model_text).split())
    total = sum(a.values()) + sum(b.values())
    return 1.0 if total == 0 else 2 * sum((a & b).values()) / total


def region_words(regions: Sequence[Any], words_by_page: Dict[int, list]) -> Dict[int, List[str]]:
    """{region index: text-layer words inside the region}."""
    from app.modules.exercise.services.pdf_layout_service import _in_region
    return {ri: [w.text for p, ws in words_by_page.items() for w in ws
                 if _in_region(reg, p, (w.x0 + w.x1) / 2, (w.y0 + w.y1) / 2)]
            for ri, reg in enumerate(regions)}


def flag_deviations(questions: List[Any], regions: Sequence[Any], words_by_page: Dict[int, list],
                    label: str = "") -> int:
    """Set needs_review + image_metadata.review_reason on questions that deviate from the text layer.

    Flag only, text is never rewritten. Returns the number of flagged questions.
    """
    from app.modules.exercise.services.pdf_layout_service import _in_region
    by_slot = {(r.part, r.number): r for r in regions}
    flagged = 0
    for q in questions:
        if getattr(q, "is_placeholder", False):
            continue
        reg = by_slot.get((getattr(q, "part_index", None), q.question_number))
        if reg is None:
            continue
        layer = [w.text for p, ws in words_by_page.items() for w in ws
                 if _in_region(reg, p, (w.x0 + w.x1) / 2, (w.y0 + w.y1) / 2)]
        model = " ".join([q.content or ""] + [o.content or "" for o in (q.answer_options or [])])
        sim = similarity(layer, model)
        if sim < MIN_SIMILARITY:
            q.needs_review = True
            q.image_metadata = {**(q.image_metadata or {}), "review_reason": REVIEW_REASON}
            logger.warning("Exam '%s': question %s text differs from the PDF text layer (similarity=%.2f)",
                           label, q.question_number, sim)
            flagged += 1
    return flagged
