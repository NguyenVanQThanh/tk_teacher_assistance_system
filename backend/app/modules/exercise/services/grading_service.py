# File Name: grading_service.py
# Description: Internal auto-grading engine for exercise attempts (F-EXE-04).
# Created At: 2026-08-05
# Created By: Tam Khang
# Updated At: 2026-09-27
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

        answers_map = {ans.question_id: ans for ans in answers}
        active_questions = [q for q in exercise.questions if q.status != 'DELETED']
        mc_questions = [q for q in active_questions if q.question_type == 'MultipleChoice']

        total_mc_count = len(mc_questions)
        points_per_mc = (10.0 / total_mc_count) if total_mc_count > 0 else 0.0

        earned_points = 0.0
        question_results = []

        for q in active_questions:
            ans = answers_map.get(q.question_id)

            if q.question_type == 'MultipleChoice':
                is_correct = False
                selected_option_id = None

                if ans and ans.answer_option_id:
                    selected_option_id = ans.answer_option_id
                    # Match option against correct option
                    matched_opt = next(
                        (opt for opt in q.answer_options if opt.option_id == selected_option_id),
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
                question_results.append({
                    "question_id": str(q.question_id),
                    "question_type": "TrueFalse",
                    "student_answer_text": student_text,
                    "is_correct": None,
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

        final_score = round(earned_points, 2) if total_mc_count > 0 else None

        detailed_results = {
            "questions": question_results
        }

        return final_score, detailed_results
