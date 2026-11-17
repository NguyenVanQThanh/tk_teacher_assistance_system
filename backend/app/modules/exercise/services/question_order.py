# File Name: question_order.py
# Description: Shared paper ordering helpers: questions are always grouped by part
#              (MultipleChoice, TrueFalse, ShortAnswer, Other) and ordered inside each part.
# Created At: 2026-11-17
# Created By: AI Agent
# Updated At: 2026-11-17
# Updated By: AI Agent

PART_RANK = {"MultipleChoice": 1, "TrueFalse": 2, "ShortAnswer": 3, "Other": 4}


def part_rank(question) -> int:
    """Return the part rank of a question (unknown types go last)."""
    return PART_RANK.get(question.question_type, 4)


def question_sort_key(question):
    """Sort key: part rank, stored display_order, creation time, then id as a stable tiebreak."""
    created = getattr(question, "created_at", None)
    return (
        part_rank(question),
        getattr(question, "display_order", 0) or 0,
        created.timestamp() if created else 0.0,
        str(getattr(question, "question_id", "")),
    )
