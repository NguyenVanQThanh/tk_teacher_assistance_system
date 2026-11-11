# File Name: answer_solver_service.py
# Description: Solves multiple-choice and true/false questions that have no answer key using a Mistral chat model.
# Created At: 2026-11-10
# Created By: AI Agent
# Updated At: 2026-11-10
# Updated By: AI Agent

"""Automatic answer solving for unkeyed imports.

Only MultipleChoice and TrueFalse questions without any marked answer are solved.
Short-answer questions and questions keyed by the document are never touched.
Failures never raise: affected questions stay unanswered and are flagged needs_review.
"""
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

import httpx

from app.core import config
from app.modules.exercise.schemas import QuestionTypeEnum
from app.modules.exercise.services.mistral_vision_parser_service import (
    MistralVisionParserService,
    flatten_content,
    raise_for_status_logged,
)

logger = logging.getLogger(__name__)

LOW_CONFIDENCE = 0.7
LABELS = ["A", "B", "C", "D"]

SYSTEM_PROMPT = (
    "You are an expert teacher solving exam questions. For each question return the correct answer. "
    "Multiple choice: answer is one of A, B, C, D. True/false: judge each statement a, b, c, d "
    "independently and set tf; answer is null. Use null if you cannot decide. "
    "Return ONLY JSON: {\"results\": [{\"number\": int, \"answer\": \"A\"|\"B\"|\"C\"|\"D\"|null, "
    "\"tf\": {\"a\": bool, \"b\": bool, \"c\": bool, \"d\": bool}|null, \"confidence\": 0..1, "
    "\"rationale\": \"max 2 sentences\"}]}. Use the question numbers exactly as given."
)

SCHEMA = {
    "type": "object",
    "properties": {"results": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "number": {"type": "integer"},
            "answer": {"type": ["string", "null"], "enum": ["A", "B", "C", "D", None]},
            "tf": {"type": ["object", "null"], "properties": {k: {"type": "boolean"} for k in "abcd"}},
            "confidence": {"type": "number"},
            "rationale": {"type": "string"},
        },
        "required": ["number", "answer", "tf", "confidence", "rationale"],
    }}},
    "required": ["results"],
}


def _is_choice(q: Any) -> bool:
    return q.question_type in (QuestionTypeEnum.MultipleChoice, QuestionTypeEnum.TrueFalse)


def _solvable(q: Any) -> bool:
    """MC needs at least 2 options, TF at least 1 statement."""
    need = 2 if q.question_type == QuestionTypeEnum.MultipleChoice else 1
    return len(q.answer_options or []) >= need


def _needs_solving(q: Any) -> bool:
    return _is_choice(q) and _solvable(q) and not any(o.is_correct for o in q.answer_options)


def _flag(q: Any, reason: str) -> None:
    """Mark for review and record why (image_metadata.review_reason)."""
    q.needs_review = True
    q.image_metadata = {**(q.image_metadata or {}), "review_reason": reason}


def _has_figure(q: Any) -> bool:
    return bool(q.image_url or q.image_bbox or (q.image_metadata and q.image_metadata.get("filename")))


def _chat(payload: dict) -> str:
    """POST to Mistral chat completions; returns message text (tolerates TextChunk lists)."""
    api_key = MistralVisionParserService.get_api_key()
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY is not configured.")
    started = time.monotonic()
    with httpx.Client(timeout=httpx.Timeout(connect=15.0, read=240.0, write=60.0, pool=15.0)) as client:
        resp = client.post(MistralVisionParserService.get_api_url(), json=payload,
                           headers={"Authorization": f"Bearer {api_key}"})
        raise_for_status_logged(resp)
        body = resp.json()
    choice = body["choices"][0]
    text = flatten_content(choice["message"]["content"])
    logger.info("Answer solver call: elapsed=%.1fs chars=%d finish=%s", time.monotonic() - started,
                len(text), choice.get("finish_reason"))
    return text


def _parse_json(text: str) -> Optional[dict]:
    text = re.sub(r"^```(?:json)?|```$", "", (text or "").strip(), flags=re.M).strip()
    for cand in (text, text[text.find("{"):text.rfind("}") + 1]):
        try:
            data = json.loads(cand)
            return data if isinstance(data, dict) else {"results": data}
        except (ValueError, TypeError):
            continue
    return None


def _results(data: Optional[dict]) -> Dict[int, dict]:
    out: Dict[int, dict] = {}
    for r in (data or {}).get("results") or []:
        if isinstance(r, dict) and isinstance(r.get("number"), int):
            out[r["number"]] = r
    return out


def _call(user_text: str, effort: str = "medium") -> Dict[int, dict]:
    """Solver call: json_schema first, plain JSON text if it errors or yields no usable results."""
    base = {
        "model": config.ANSWER_SOLVER_MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_text}],
        "reasoning_effort": effort,  # high burns the whole token budget on thinking (finish=length, empty text)
        "max_tokens": 16000,
    }
    try:
        res = _results(_parse_json(_chat({**base, "response_format": {
            "type": "json_schema", "json_schema": {"name": "answers", "schema": SCHEMA}}})))
        if res:
            return res
        logger.warning("Answer solver json_schema call returned no usable results, retrying without schema")
    except Exception as exc:
        logger.warning("Answer solver json_schema call failed, retrying without schema: %s", exc)
    return _results(_parse_json(_chat(base)))


def _render(idx: int, q: Any) -> str:
    # Batch-local number avoids collisions when several exams repeat numbers in one file.
    mc = q.question_type == QuestionTypeEnum.MultipleChoice
    lines = [f"Question {idx} ({q.question_type.value}): {q.content}"]
    for i, o in enumerate(q.answer_options[:4]):
        lines.append(f"{LABELS[i] if mc else LABELS[i].lower()}) {o.content}")
    return "\n".join(lines)


def _apply(q: Any, r: dict) -> bool:
    opts = q.answer_options
    try:
        conf = float(r.get("confidence"))
    except (TypeError, ValueError):
        conf = 0.0
    if q.question_type == QuestionTypeEnum.MultipleChoice:
        ans = str(r.get("answer") or "").strip().upper()
        if ans not in LABELS[:len(opts)]:
            return False
        opts[LABELS.index(ans)].is_correct = True
        q.correct_answer = ans
    else:
        tf = r.get("tf")
        n = min(len(opts), len(LABELS))
        if not isinstance(tf, dict) or any(not isinstance(tf.get(LABELS[i].lower()), bool) for i in range(n)):
            return False
        for i in range(n):
            opts[i].is_correct = tf[LABELS[i].lower()]
    q.image_metadata = {**(q.image_metadata or {}), "solved_by": "ai", "ai_confidence": conf,
                        "ai_rationale": str(r.get("rationale") or "")[:500]}
    if conf < LOW_CONFIDENCE or _has_figure(q):
        q.needs_review = True
    return True


class AnswerSolverService:
    @staticmethod
    def solve_questions(questions: List[Any]) -> int:
        """Solve unkeyed MC/TF questions in place. Returns the number solved; never raises."""
        if not config.ANSWER_SOLVER_ENABLED:
            return 0
        for q in questions:
            if _is_choice(q) and not _solvable(q) and not any(o.is_correct for o in q.answer_options or []):
                _flag(q, f"Cannot solve: only {len(q.answer_options or [])} parsed option(s); check the question.")
                logger.info("Answer solver skipped question %s %s: too few options", q.exam_label, q.question_number)
        todo = [q for q in questions if _needs_solving(q)]
        solved = failed = 0
        size = max(1, config.ANSWER_SOLVER_BATCH_SIZE)
        for i in range(0, len(todo), size):
            batch = todo[i:i + size]
            b_solved = 0
            pending = batch
            # One retry for questions the first attempt left unanswered (truncation, bad JSON, ...).
            for attempt in (1, 2):
                if not pending:
                    break
                results: Dict[int, dict] = {}
                try:
                    results = _call("\n\n".join(_render(n, q) for n, q in enumerate(pending, start=1)),
                                    effort="medium" if attempt == 1 else "low")
                except Exception as exc:
                    logger.warning("Answer solver batch attempt %d failed: %s", attempt, exc)
                left = []
                for n, q in enumerate(pending, start=1):
                    try:
                        ok = n in results and _apply(q, results[n])
                    except Exception:
                        logger.warning("Answer solver could not apply result", exc_info=True)
                        ok = False
                    if ok:
                        b_solved += 1
                    else:
                        left.append(q)
                pending = left
            for q in pending:
                _flag(q, "AI solver returned no valid answer.")
            solved += b_solved
            failed += len(batch) - b_solved
            logger.info("Answer solver batch %d: requested=%d solved=%d failed=%d",
                        i // size + 1, len(batch), b_solved, len(batch) - b_solved)
        logger.info("Answer solver total: requested=%d solved=%d failed=%d skipped_no_options=%d",
                    len(todo), solved, failed,
                    sum(1 for q in questions if _is_choice(q) and not _solvable(q)))
        return solved
