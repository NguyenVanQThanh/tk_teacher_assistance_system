# File Name: grading_service.py
# Description: Internal auto-grading engine for exercise attempts (F-EXE-04) with per-part score weights, True/False partial credit, numeric short answers and exercise-wide regrading.
# Created At: 2026-08-05
# Created By: Tam Khang
# Updated At: 2026-11-13
# Updated By: AI Agent

from types import SimpleNamespace
from typing import List, Tuple, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.modules.exercise.schemas import AnswerInput
from app.modules.exercise.repository import ExerciseRepository

# Score budget per part (national exam layout), normalised over the parts present in the exercise.
PART_WEIGHTS = {"MultipleChoice": 3.0, "TrueFalse": 4.0, "ShortAnswer": 3.0}
# True/False partial credit by number of correct statements (out of 4).
TF_PARTIAL = {0: 0.0, 1: 0.1, 2: 0.25, 3: 0.5, 4: 1.0}


def compute_max_points(questions) -> Dict[str, float]:
    """Return {question_id: max_points} splitting the 10-point scale across the parts present."""
    counts: Dict[str, int] = {t: 0 for t in PART_WEIGHTS}
    for q in questions:
        if q.question_type in counts:
            counts[q.question_type] += 1
    total_weight = sum(PART_WEIGHTS[t] for t, c in counts.items() if c > 0)
    result: Dict[str, float] = {}
    for q in questions:
        c = counts.get(q.question_type, 0)
        result[str(q.question_id).lower()] = (
            10.0 * PART_WEIGHTS[q.question_type] / total_weight / c if c and total_weight else 0.0
        )
    return result


def _numeric_equal(a: str, b: str) -> bool:
    """Compare short answers numerically when both parse (comma or dot decimals), else by text."""
    na, nb = a.strip().replace(',', '.'), b.strip().replace(',', '.')
    try:
        fa, fb = float(na), float(nb)
        return abs(fa - fb) <= 1e-6 * max(1.0, abs(fb))
    except ValueError:
        return na.lower() == nb.lower()


class GradingService:
    """Service handling automatic evaluation of exercise attempt submissions."""

    def __init__(self, db: Session):
        self.db = db
        self.exercise_repo = ExerciseRepository(db)

    def grade_attempt(
        self,
        exercise_id: UUID,
        answers: List[AnswerInput]
    ) -> Tuple[Optional[float], Dict[str, Any]]:
        """
        Grades an attempt submission. MultipleChoice, TrueFalse (partial credit) and ShortAnswer
        (numeric match) are scored automatically; ShortAnswer/Other stay flagged for manual review.

        Returns (score, detailed_results_dict).
        """
        exercise = self.exercise_repo.get_by_id(exercise_id)
        if not exercise:
            return None, {"questions": [], "error": "Exercise not found"}
        answers_map = {str(ans.question_id).lower(): ans for ans in answers}
        return self._grade(exercise, answers_map)

    def _grade(
        self,
        exercise,
        answers_map: Dict[str, Any],
        manual_overrides: Optional[Dict[str, bool]] = None
    ) -> Tuple[Optional[float], Dict[str, Any]]:
        """Score answers (objects with answer_option_id / answer_text) against the current answer key."""
        manual_overrides = manual_overrides or {}

        def get_display_order(q):
            val = getattr(q, 'display_order', 0)
            return val if isinstance(val, (int, float)) else 0

        active_questions = sorted(
            [q for q in exercise.questions if getattr(q, 'status', None) != 'DELETED'],
            key=get_display_order
        )
        max_points = compute_max_points(active_questions)
        auto_count = sum(1 for q in active_questions if q.question_type in ('MultipleChoice', 'TrueFalse'))

        earned_points = 0.0
        question_results = []

        for q in active_questions:
            q_id_str = str(q.question_id).lower()
            ans = answers_map.get(q_id_str)
            q_max = max_points.get(q_id_str, 0.0)

            if q.question_type == 'MultipleChoice':
                is_correct = False
                selected_option_id = getattr(ans, 'answer_option_id', None) if ans else None

                if selected_option_id:
                    matched_opt = next(
                        (opt for opt in q.answer_options if str(opt.option_id).lower() == str(selected_option_id).lower()),
                        None
                    )
                    if matched_opt and matched_opt.is_correct:
                        is_correct = True

                points = q_max if is_correct else 0.0
                earned_points += points
                question_results.append({
                    "question_id": str(q.question_id),
                    "question_type": "MultipleChoice",
                    "student_answer_option_id": str(selected_option_id) if selected_option_id else None,
                    "is_correct": is_correct,
                    "points": round(points, 4),
                    "max_points": round(q_max, 4),
                    "pending_manual_grade": False
                })

            elif q.question_type == 'TrueFalse':
                student_text = getattr(ans, 'answer_text', None) if ans else None
                # student_text format: "a:true;b:false;c:true;d:false"
                sub_answers = {}
                if student_text:
                    for part in student_text.split(';'):
                        if ':' in part:
                            k, v = part.split(':', 1)
                            sub_answers[k.strip().lower()] = (v.strip().lower() == 'true')

                tf_correct_count = 0
                tf_total_count = len(q.answer_options) if q.answer_options else 0
                sub_results = {}
                if q.answer_options:
                    for idx, opt in enumerate(q.answer_options):
                        opt_label = chr(ord('a') + idx)
                        for key in ['a', 'b', 'c', 'd']:
                            if opt.content.strip().lower().startswith(key):
                                opt_label = key
                                break
                        user_val = sub_answers.get(opt_label)
                        is_sub_correct = (user_val == opt.is_correct) if user_val is not None else False
                        sub_results[opt_label] = is_sub_correct
                        if is_sub_correct:
                            tf_correct_count += 1

                all_correct = (tf_correct_count == tf_total_count) if tf_total_count > 0 else False
                if tf_total_count == 4:
                    fraction = TF_PARTIAL.get(tf_correct_count, 0.0)
                else:
                    fraction = (tf_correct_count / tf_total_count) if tf_total_count else 0.0
                points = q_max * fraction
                earned_points += points
                question_results.append({
                    "question_id": str(q.question_id),
                    "question_type": "TrueFalse",
                    "student_answer_text": student_text,
                    "is_correct": all_correct,
                    "sub_results": sub_results,
                    "points": round(points, 4),
                    "max_points": round(q_max, 4),
                    "pending_manual_grade": False
                })

            elif q.question_type == 'ShortAnswer':
                student_text = getattr(ans, 'answer_text', None) if ans else None
                is_correct = None
                correct_ans = getattr(q, 'correct_answer', None)
                if student_text and isinstance(correct_ans, str) and correct_ans.strip():
                    if _numeric_equal(str(student_text), correct_ans):
                        is_correct = True

                manual = manual_overrides.get(q_id_str)
                if manual is not None:
                    is_correct = manual
                points = q_max if is_correct else 0.0
                earned_points += points
                result = {
                    "question_id": str(q.question_id),
                    "question_type": "ShortAnswer",
                    "student_answer_text": student_text,
                    "is_correct": is_correct,
                    "points": round(points, 4),
                    "max_points": round(q_max, 4),
                    "pending_manual_grade": manual is None
                }
                if manual is not None:
                    result["manual_override"] = True
                question_results.append(result)
            elif q.question_type == 'Other':
                # Multi-part free-form answer (JSON array string); manual grading only. A teacher
                # verdict survives regrades (Other carries no auto points on the 10-point scale).
                manual = manual_overrides.get(q_id_str)
                result = {
                    "question_id": str(q.question_id),
                    "question_type": "Other",
                    "student_answer_text": getattr(ans, 'answer_text', None) if ans else None,
                    "is_correct": manual,
                    "pending_manual_grade": manual is None
                }
                if manual is not None:
                    result["manual_override"] = True
                question_results.append(result)
        has_pending = any(qr.get("pending_manual_grade") for qr in question_results)
        final_score = round(earned_points, 2) if (auto_count > 0 or not has_pending) else None

        return final_score, {"questions": question_results}

    def apply_answer_key(self, exercise_id: UUID, keys: List[Tuple[UUID, UUID]]) -> int:
        """Set the correct option of MultipleChoice questions in place (option ids stay stable)."""
        exercise = self.exercise_repo.get_by_id(exercise_id)
        if not exercise:
            return 0
        wanted = {str(qid).lower(): str(oid).lower() for qid, oid in keys}
        updated = 0
        for q in exercise.questions:
            target = wanted.get(str(q.question_id).lower())
            if not target or q.status == 'DELETED' or q.question_type != 'MultipleChoice':
                continue
            if not any(str(o.option_id).lower() == target for o in q.answer_options):
                continue
            for o in q.answer_options:
                o.is_correct = str(o.option_id).lower() == target
            q.needs_review = False
            updated += 1
        self.db.commit()
        return updated

    def regrade_exercise(self, exercise_id: UUID) -> int:
        """Recompute and persist scores of ALL finished attempts of an exercise (the answer key is
        shared by every class it is assigned to); returns the count."""
        from models.models import ClassAssignment, StudentExerciseAttempt
        exercise = self.exercise_repo.get_by_id(exercise_id)
        if not exercise:
            return 0
        q = self.db.query(StudentExerciseAttempt).join(
            ClassAssignment, StudentExerciseAttempt.assignment_id == ClassAssignment.assignment_id
        ).filter(
            ClassAssignment.exercise_id == exercise_id,
            StudentExerciseAttempt.is_finished.is_(True),
            StudentExerciseAttempt.status != 'DELETED'
        )
        attempts = q.all()
        for att in attempts:
            score, results = self.rescore(exercise, att.detailed_results)
            # Never overwrite a teacher-set total score (manual grading decision).
            teacher_total = results.get("teacher_total_score")
            att.score = float(teacher_total) if teacher_total is not None else score
            att.detailed_results = results
        self.db.commit()
        return len(attempts)

    def rescore(self, exercise, detailed_results) -> Tuple[Optional[float], Dict[str, Any]]:
        """Re-grade stored per-question answers against the current key, keeping teacher verdicts
        (manual_override) and every non-question key (feedback, teacher_total_score, ...)."""
        old = dict(detailed_results or {})
        answers_map: Dict[str, Any] = {}
        overrides: Dict[str, bool] = {}
        for r in old.get("questions", []):
            qid = str(r.get("question_id", "")).lower()
            answers_map[qid] = SimpleNamespace(
                answer_option_id=r.get("student_answer_option_id"),
                answer_text=r.get("student_answer_text"),
            )
            if r.get("manual_override") and r.get("is_correct") is not None:
                overrides[qid] = bool(r["is_correct"])
        score, results = self._grade(exercise, answers_map, overrides)
        for k, v in old.items():
            if k != "questions":
                results[k] = v
        return score, results
