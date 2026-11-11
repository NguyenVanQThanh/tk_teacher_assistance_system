# File Name: exam_sequence_service.py
# Description: Pure helpers that keep scanned exam questions consistent: page chunking with overlap, stray true/false sub-item merge, duplicate removal, question-number gap detection and review placeholders.
# Created At: 2026-11-10
# Created By: AI Agent
# Updated At: 2026-11-10
# Updated By: AI Agent

import re
from typing import Any, List, Optional, Tuple

from app.modules.exercise.schemas import QuestionTypeEnum
from app.modules.exercise.services.import_parser_service import ParsedOption, ParsedQuestion

_SUB_ITEM = re.compile(r"^\s*\(?[a-dA-D]\)")
_WS = re.compile(r"\s+")
PLACEHOLDER_TEMPLATE = "[Missing question {n} - please review]"


def chunk_pages(pages: List[int], size: int) -> List[List[int]]:
    """Windows of ``size`` pages overlapping by one page, so a question that spans two
    pages is always fully visible in at least one window (size 1 cannot overlap)."""
    if not pages:
        return []
    size = max(1, size)
    if len(pages) <= size:
        return [list(pages)]
    stride = max(1, size - 1)
    chunks = []
    for i in range(0, len(pages), stride):
        chunks.append(pages[i:i + size])
        if i + size >= len(pages):
            break
    return chunks


def _norm(text: Optional[str]) -> str:
    return _WS.sub(" ", (text or "").strip().lower())


def _is_stray_sub_item(q: ParsedQuestion) -> bool:
    """A true/false statement (a-d) that the model emitted as its own question."""
    if q.question_type == QuestionTypeEnum.TrueFalse and len(q.answer_options) <= 1:
        return True
    return (q.question_type != QuestionTypeEnum.MultipleChoice and not q.answer_options
            and bool(_SUB_ITEM.match(q.content or "")))


def merge_stray_true_false(questions: List[ParsedQuestion]) -> List[ParsedQuestion]:
    """Fold stray 1-option / a)-d) rows into the preceding true/false question that has < 4 statements."""
    out: List[ParsedQuestion] = []
    for q in questions:
        prev = out[-1] if out else None
        if (prev is not None and prev.question_type == QuestionTypeEnum.TrueFalse
                and len(prev.answer_options) < 4 and _is_stray_sub_item(q)):
            for o in (q.answer_options or [ParsedOption(content=q.content)]):
                prev.answer_options.append(ParsedOption(o.content, o.is_correct, len(prev.answer_options)))
            continue
        out.append(q)
    for q in out:
        if q.question_type == QuestionTypeEnum.TrueFalse and len(q.answer_options) < 4:
            q.needs_review = True  # statements cannot be invented; teacher must complete them
    return out


def dedupe_questions(questions: List[ParsedQuestion]) -> List[ParsedQuestion]:
    """Drop repeated questions (same stem), keeping the fuller copy at the first position."""
    out: List[ParsedQuestion] = []
    seen = {}
    for q in questions:
        stem = _norm(q.content)
        if not stem:
            out.append(q)
            continue
        key = stem[:160] if len(stem) >= 40 else (q.question_number, stem)
        if key not in seen and len(stem) >= 40:
            # A copy truncated at a chunk boundary is a prefix of the complete one (same number)
            for k, idx in seen.items():
                o = _norm(out[idx].content)
                if (out[idx].question_number == q.question_number and len(o) >= 40
                        and (stem.startswith(o) or o.startswith(stem))):
                    key = k
                    break
        if key in seen:
            i = seen[key]
            if (len(q.answer_options), len(q.content or "")) > (len(out[i].answer_options), len(out[i].content or "")):
                out[i] = q
            continue
        seen[key] = len(out)
        out.append(q)
    return out


def normalize_questions(questions: List[ParsedQuestion]) -> List[ParsedQuestion]:
    """Post-parse cleanup: dedupe (overlapping chunks) then merge stray true/false rows."""
    return merge_stray_true_false(dedupe_questions(questions))


def find_output_gaps(questions: List[ParsedQuestion]) -> List[Tuple[int, int]]:
    """[(index of the preceding question or -1, missing number)] from the model output alone.

    Used when the PDF has no text layer. A run is a stream stretch with increasing
    numbers; each run must start at 1 and have no jumps (numbers restart per part).
    """
    gaps: List[Tuple[int, int]] = []
    prev_no: Optional[int] = None
    for i, q in enumerate(questions):
        n = q.question_number
        if not isinstance(n, int):
            continue
        if prev_no is not None and n > prev_no:
            gaps.extend((i - 1, m) for m in range(prev_no + 1, n))
        elif (prev_no is None or n <= prev_no) and n > 1:
            gaps.extend((i - 1, m) for m in range(1, n))
        prev_no = n
    return gaps


def make_placeholder(number: int, part_index: Optional[int] = None) -> ParsedQuestion:
    """Review placeholder for a question that could not be recovered."""
    text = PLACEHOLDER_TEMPLATE.format(n=number)
    q = ParsedQuestion(
        question_number=number, part="Part3", question_type=QuestionTypeEnum.ShortAnswer,
        difficulty=None, content=text, content_markdown=text, content_latex=text,
        confidence_score=0.0, needs_review=True,
    )
    q.part_index = part_index
    q.doc_ordered = True
    q.is_placeholder = True
    return q


def insert_by_position(questions: List[ParsedQuestion], new_q: ParsedQuestion) -> None:
    """Insert before the first question that sorts after (part_index, number); else append."""
    key: Tuple[Any, Any] = (getattr(new_q, "part_index", None), new_q.question_number)
    if isinstance(key[0], int):
        for i, q in enumerate(questions):
            p = getattr(q, "part_index", None)
            if isinstance(p, int) and (p, q.question_number) > key:
                questions.insert(i, new_q)
                return
    questions.append(new_q)
