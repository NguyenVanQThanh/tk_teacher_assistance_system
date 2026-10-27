# File Name: grading_service.py
# Description: Internal auto-grading engine for exercise attempts (F-EXE-04).
# Created At: 2026-08-05
# Created By: Tam Khang
# Updated At: 2026-10-04
# Updated By: Tam Khang

from typing import List, Tuple, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.modules.exercise.schemas import AnswerInput
from app.modules.exercise.repository import ExerciseRepository


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
        Grades an attempt submission. Evaluates MultipleChoice questions automatically
        and marks ShortAnswer questions as pending manual grading.

        Returns (score, detailed_results_dict).
        """
        exercise = self.exercise_repo.get_by_id(exercise_id)
        if not exercise:
            return None, {"questions": [], "error": "Exercise not found"}

        answers_map = {str(ans.question_id).lower(): ans for ans in answers}
        def get_display_order(q):
            val = getattr(q, 'display_order', 0)
            return val if isinstance(val, (int, float)) else 0

        active_questions = sorted(
            [q for q in exercise.questions if getattr(q, 'status', None) != 'DELETED'],
            key=get_display_order
        )
        mc_questions = [q for q in active_questions if q.question_type == 'MultipleChoice']

        total_mc_count = len(mc_questions)
        points_per_mc = (10.0 / total_mc_count) if total_mc_count > 0 else 0.0

        earned_points = 0.0
        question_results = []

        for q in active_questions:
            q_id_str = str(q.question_id).lower()
            ans = answers_map.get(q_id_str)

            if q.question_type == 'MultipleChoice':
                is_correct = False
                selected_option_id = None

                if ans and ans.answer_option_id:
                    selected_option_id = ans.answer_option_id
                    # Match option against correct option
                    matched_opt = next(
                        (opt for opt in q.answer_options if str(opt.option_id).lower() == str(selected_option_id).lower()),
                        None
                    )
                    if matched_opt and matched_opt.is_correct:
                        is_correct = True
                        earned_points += points_per_mc

                question_results.append({
                    "question_id": str(q.question_id),
                    "question_type": "MultipleChoice",
                    "student_answer_option_id": str(selected_option_id) if selected_option_id else None,
                    "is_correct": is_correct,
                    "pending_manual_grade": False
                })

            elif q.question_type == 'TrueFalse':
                student_text = ans.answer_text if ans else None
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
                question_results.append({
                    "question_id": str(q.question_id),
                    "question_type": "TrueFalse",
                    "student_answer_text": student_text,
                    "is_correct": all_correct,
                    "sub_results": sub_results,
                    "pending_manual_grade": False
                })

            elif q.question_type == 'ShortAnswer':
                student_text = ans.answer_text if ans else None
                is_correct = None
                correct_ans = getattr(q, 'correct_answer', None)
                if student_text and isinstance(correct_ans, str) and correct_ans.strip():
                    norm_student = str(student_text).strip().replace(',', '.')
                    norm_correct = correct_ans.strip().replace(',', '.')
                    if norm_student.lower() == norm_correct.lower():
                        is_correct = True

                question_results.append({
                    "question_id": str(q.question_id),
                    "question_type": "ShortAnswer",
                    "student_answer_text": student_text,
                    "is_correct": is_correct,
                    "pending_manual_grade": True
                })
        has_pending = any(qr.get("pending_manual_grade") for qr in question_results)
        final_score = round(earned_points, 2) if (total_mc_count > 0 or not has_pending) else None

        detailed_results = {
            "questions": question_results
        }

        return final_score, detailed_results
