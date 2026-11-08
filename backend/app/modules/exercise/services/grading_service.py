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

    @staticmethod
    def _norm_answer_text(s: Any) -> str:
        return str(s).strip().replace(',', '.').lower()

    @classmethod
    def _answers_match(cls, student: Any, correct: Any) -> bool:
        """So khớp câu trả lời ngắn: chuẩn hóa dấu phẩy/thập phân, không phân biệt hoa thường;
        nếu là số thì so sánh theo giá trị (2 == 2.0)."""
        ns = cls._norm_answer_text(student)
        nc = cls._norm_answer_text(correct)
        if ns == nc:
            return True
        try:
            return abs(float(ns) - float(nc)) < 1e-9
        except (ValueError, TypeError):
            return False

    def grade_attempt(
        self,
        exercise_id: UUID,
        answers: List[AnswerInput]
    ) -> Tuple[Optional[float], Dict[str, Any]]:
        """
        Grades an attempt submission. Tự động chấm cả 3 loại câu (MultipleChoice, TrueFalse, ShortAnswer);
        điểm chia đều trên tổng số câu hỏi (thang 10). ShortAnswer chỉ "pending_manual_grade" khi đề không có
        correct_answer để so sánh.

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
        # Điểm chia đều cho TẤT CẢ câu hỏi (Trắc nghiệm + Đúng/Sai + Trả lời ngắn), tổng thang điểm 10
        total_questions = len(active_questions)
        points_per_question = (10.0 / total_questions) if total_questions > 0 else 0.0

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
                        earned_points += points_per_question

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

                # Danh sách ý Đúng/Sai: ưu tiên answer_options, nếu không có thì lấy từ segments (key/is_correct)
                tf_items = []
                if q.answer_options:
                    for idx, opt in enumerate(q.answer_options):
                        opt_label = chr(ord('a') + idx)
                        content_lower = (opt.content or '').strip().lower()
                        for key in ['a', 'b', 'c', 'd']:
                            if content_lower.startswith(key):
                                opt_label = key
                                break
                        tf_items.append((opt_label, bool(opt.is_correct)))
                else:
                    segments = getattr(q, 'segments', None) or []
                    for idx, seg in enumerate(segments):
                        if isinstance(seg, dict):
                            key = str(seg.get('key') or chr(ord('a') + idx)).lower()
                            tf_items.append((key, bool(seg.get('is_correct'))))

                tf_correct_count = 0
                tf_total_count = len(tf_items)
                sub_results = {}
                for opt_label, opt_correct in tf_items:
                    user_val = sub_answers.get(opt_label)
                    is_sub_correct = (user_val == opt_correct) if user_val is not None else False
                    sub_results[opt_label] = is_sub_correct
                    if is_sub_correct:
                        tf_correct_count += 1

                all_correct = (tf_correct_count == tf_total_count) if tf_total_count > 0 else False
                if all_correct:
                    earned_points += points_per_question
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
                correct_ans = getattr(q, 'correct_answer', None)
                correct_ans = correct_ans if isinstance(correct_ans, str) and correct_ans.strip() else None

                is_correct = None
                pending = False
                if student_text and student_text.strip() and correct_ans:
                    if GradingService._answers_match(student_text, correct_ans):
                        is_correct = True
                        earned_points += points_per_question
                    else:
                        is_correct = False
                elif correct_ans:
                    # học sinh chưa trả lời -> sai; vẫn chấm được tự động
                    is_correct = False
                else:
                    # đề không có đáp án chuẩn -> cần chấm tay
                    pending = True

                question_results.append({
                    "question_id": str(q.question_id),
                    "question_type": "ShortAnswer",
                    "student_answer_text": student_text,
                    "is_correct": is_correct,
                    "pending_manual_grade": pending
                })
        has_pending = any(qr.get("pending_manual_grade") for qr in question_results)
        final_score = round(earned_points, 2)

        detailed_results = {
            "questions": question_results
        }

        return final_score, detailed_results
