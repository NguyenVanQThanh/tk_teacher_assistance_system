# File Name: test_grading_service.py
# Description: Unit tests for F-EXE-04 Auto Grading service (GradingService).
# Created At: 2026-08-08
# Created By: Tam Khang
# Updated At: 2026-08-08
# Updated By: Tam Khang

import uuid
from unittest.mock import MagicMock
import pytest

from app.modules.exercise.services.grading_service import GradingService
from app.modules.exercise.schemas import AnswerInput


def create_mock_question(q_id, q_type, options=None, status="ACTIVE"):
    q = MagicMock()
    q.question_id = q_id
    q.question_type = q_type
    q.status = status
    q.answer_options = options or []
    return q


def create_mock_option(opt_id, is_correct):
    opt = MagicMock()
    opt.option_id = opt_id
    opt.is_correct = is_correct
    return opt


class TestGradingServiceUnit:
    """Unit tests for GradingService evaluating AC-01 through AC-05."""

    def test_all_correct_multiplechoice(self):
        """AC-01: All MultipleChoice questions answered correctly -> score = 10.00."""
        db = MagicMock()
        service = GradingService(db)

        exercise_id = uuid.uuid4()
        q1_id = uuid.uuid4()
        q2_id = uuid.uuid4()

        opt1_correct = uuid.uuid4()
        opt1_wrong = uuid.uuid4()
        opt2_correct = uuid.uuid4()

        q1 = create_mock_question(
            q1_id, "MultipleChoice",
            [create_mock_option(opt1_correct, True), create_mock_option(opt1_wrong, False)]
        )
        q2 = create_mock_question(
            q2_id, "MultipleChoice",
            [create_mock_option(opt2_correct, True)]
        )

        mock_exercise = MagicMock()
        mock_exercise.questions = [q1, q2]
        service.exercise_repo.get_by_id = MagicMock(return_value=mock_exercise)

        answers = [
            AnswerInput(question_id=q1_id, answer_option_id=opt1_correct),
            AnswerInput(question_id=q2_id, answer_option_id=opt2_correct),
        ]

        score, detailed = service.grade_attempt(exercise_id, answers)

        assert score == 10.00
        assert len(detailed["questions"]) == 2
        assert all(q["is_correct"] is True for q in detailed["questions"])
        assert all(q["pending_manual_grade"] is False for q in detailed["questions"])

    def test_one_wrong_multiplechoice(self):
        """AC-02: 5 MultipleChoice questions, 1 wrong answer -> score = 8.00."""
        db = MagicMock()
        service = GradingService(db)

        exercise_id = uuid.uuid4()
        questions = []
        answers = []

        for i in range(5):
            q_id = uuid.uuid4()
            opt_correct = uuid.uuid4()
            opt_wrong = uuid.uuid4()

            q = create_mock_question(
                q_id, "MultipleChoice",
                [create_mock_option(opt_correct, True), create_mock_option(opt_wrong, False)]
            )
            questions.append(q)

            # Mark question index 4 (5th question) as wrong answer
            selected_opt = opt_wrong if i == 4 else opt_correct
            answers.append(AnswerInput(question_id=q_id, answer_option_id=selected_opt))

        mock_exercise = MagicMock()
        mock_exercise.questions = questions
        service.exercise_repo.get_by_id = MagicMock(return_value=mock_exercise)

        score, detailed = service.grade_attempt(exercise_id, answers)

        assert score == 8.00
        assert len(detailed["questions"]) == 5
        correct_count = sum(1 for q in detailed["questions"] if q["is_correct"] is True)
        wrong_count = sum(1 for q in detailed["questions"] if q["is_correct"] is False)
        assert correct_count == 4
        assert wrong_count == 1

    def test_short_answer_pending_manual_grade(self):
        """AC-03: ShortAnswer question -> is_correct = None, pending_manual_grade = True."""
        db = MagicMock()
        service = GradingService(db)

        exercise_id = uuid.uuid4()
        mc_id = uuid.uuid4()
        opt_correct = uuid.uuid4()
        sa_id = uuid.uuid4()

        q_mc = create_mock_question(mc_id, "MultipleChoice", [create_mock_option(opt_correct, True)])
        q_sa = create_mock_question(sa_id, "ShortAnswer", [])

        mock_exercise = MagicMock()
        mock_exercise.questions = [q_mc, q_sa]
        service.exercise_repo.get_by_id = MagicMock(return_value=mock_exercise)

        answers = [
            AnswerInput(question_id=mc_id, answer_option_id=opt_correct),
            AnswerInput(question_id=sa_id, answer_text="Photosynthesis process..."),
        ]

        score, detailed = service.grade_attempt(exercise_id, answers)

        # 2 câu (1 MC + 1 SA), điểm chia đều: MC đúng được 10/2 = 5.0; SA thiếu đáp án chuẩn -> pending, 0 điểm
        assert score == 5.00
        assert len(detailed["questions"]) == 2

        sa_result = next(q for q in detailed["questions"] if q["question_id"] == str(sa_id))
        assert sa_result["question_type"] == "ShortAnswer"
        assert sa_result["is_correct"] is None
        assert sa_result["pending_manual_grade"] is True
        assert sa_result["student_answer_text"] == "Photosynthesis process..."

    def test_missing_answer_counts_as_wrong(self):
        """AC-04: Student omits an answer -> marked as wrong (is_correct = False), no exception."""
        db = MagicMock()
        service = GradingService(db)

        exercise_id = uuid.uuid4()
        q1_id = uuid.uuid4()
        q2_id = uuid.uuid4()
        opt1_correct = uuid.uuid4()
        opt2_correct = uuid.uuid4()

        q1 = create_mock_question(q1_id, "MultipleChoice", [create_mock_option(opt1_correct, True)])
        q2 = create_mock_question(q2_id, "MultipleChoice", [create_mock_option(opt2_correct, True)])

        mock_exercise = MagicMock()
        mock_exercise.questions = [q1, q2]
        service.exercise_repo.get_by_id = MagicMock(return_value=mock_exercise)

        # Only answer q1, leave q2 un-answered (omitted)
        answers = [
            AnswerInput(question_id=q1_id, answer_option_id=opt1_correct)
        ]

        score, detailed = service.grade_attempt(exercise_id, answers)

        # 2 MC questions, 1 correct, 1 omitted (wrong) -> score = 5.0
        assert score == 5.00
        q2_result = next(q for q in detailed["questions"] if q["question_id"] == str(q2_id))
        assert q2_result["is_correct"] is False
        assert q2_result["student_answer_option_id"] is None

    def test_all_short_answer_score_is_null(self):
        """AC-05: Exercise contains only ShortAnswer questions -> score = None."""
        db = MagicMock()
        service = GradingService(db)

        exercise_id = uuid.uuid4()
        sa1_id = uuid.uuid4()
        sa2_id = uuid.uuid4()

        q_sa1 = create_mock_question(sa1_id, "ShortAnswer", [])
        q_sa2 = create_mock_question(sa2_id, "ShortAnswer", [])

        mock_exercise = MagicMock()
        mock_exercise.questions = [q_sa1, q_sa2]
        service.exercise_repo.get_by_id = MagicMock(return_value=mock_exercise)

        answers = [
            AnswerInput(question_id=sa1_id, answer_text="Answer 1"),
            AnswerInput(question_id=sa2_id, answer_text="Answer 2"),
        ]

        score, detailed = service.grade_attempt(exercise_id, answers)

        # thiếu đáp án chuẩn -> chấm tay (pending), điểm tự động = 0.0
        assert score == 0.0
        assert len(detailed["questions"]) == 2
        assert all(q["pending_manual_grade"] is True for q in detailed["questions"])
        assert all(q["is_correct"] is None for q in detailed["questions"])


    def test_short_answer_correct_earns_points(self):
        """Đúng 1 câu trả lời ngắn (kể cả khác định dạng số: '2' vs '2.0') phải được cộng điểm."""
        db = MagicMock()
        service = GradingService(db)

        exercise_id = uuid.uuid4()
        sa_id = uuid.uuid4()
        q_sa = create_mock_question(sa_id, "ShortAnswer", [])
        q_sa.correct_answer = "2.0"

        mock_exercise = MagicMock()
        mock_exercise.questions = [q_sa]
        service.exercise_repo.get_by_id = MagicMock(return_value=mock_exercise)

        answers = [AnswerInput(question_id=sa_id, answer_text="2")]
        score, detailed = service.grade_attempt(exercise_id, answers)

        assert score == 10.00
        sa_result = detailed["questions"][0]
        assert sa_result["is_correct"] is True
        assert sa_result["pending_manual_grade"] is False

    def test_user_scenario_only_short_answer_correct(self):
        """Kịch bản thực tế: đề 9 câu (4 MC + 1 Đúng/Sai + 4 trả lời ngắn), chỉ đúng 1 câu trả lời ngắn -> điểm = 10/9."""
        db = MagicMock()
        service = GradingService(db)

        exercise_id = uuid.uuid4()
        questions = []
        answers = []
        for i in range(4):
            q_id = uuid.uuid4()
            opt_correct = uuid.uuid4()
            opt_wrong = uuid.uuid4()
            q = create_mock_question(q_id, "MultipleChoice",
                                     [create_mock_option(opt_correct, True), create_mock_option(opt_wrong, False)])
            questions.append(q)
            answers.append(AnswerInput(question_id=q_id, answer_option_id=opt_wrong))  # MC sai

        tf_id = uuid.uuid4()
        q_tf = create_mock_question(tf_id, "TrueFalse", [])
        q_tf.segments = [
            {"key": "a", "statement": "Ý a", "is_correct": True},
            {"key": "b", "statement": "Ý b", "is_correct": False},
        ]
        questions.append(q_tf)
        answers.append(AnswerInput(question_id=tf_id, answer_text="a:false;b:true"))  # Đ/Sai sai

        sa_correct_id = uuid.uuid4()
        q_sa_ok = create_mock_question(sa_correct_id, "ShortAnswer", [])
        q_sa_ok.correct_answer = "2"
        questions.append(q_sa_ok)
        answers.append(AnswerInput(question_id=sa_correct_id, answer_text="2"))  # trả lời ngắn ĐÚNG

        for i in range(3):
            q_id = uuid.uuid4()
            q = create_mock_question(q_id, "ShortAnswer", [])
            q.correct_answer = str(100 + i)
            questions.append(q)
            answers.append(AnswerInput(question_id=q_id, answer_text="sai"))

        mock_exercise = MagicMock()
        mock_exercise.questions = questions
        service.exercise_repo.get_by_id = MagicMock(return_value=mock_exercise)

        score, detailed = service.grade_attempt(exercise_id, answers)
        assert len(detailed["questions"]) == 9
        assert score == round(10.0 / 9, 2)  # ~1.11
        sa_res = next(q for q in detailed["questions"] if q["question_id"] == str(sa_correct_id))
        assert sa_res["is_correct"] is True

    def test_truefalse_from_segments_earns_points(self):
        """Câu Đúng/Sai lưu bằng segments (không có answer_options) vẫn chấm được và cộng điểm khi đúng cả."""
        db = MagicMock()
        service = GradingService(db)

        exercise_id = uuid.uuid4()
        tf_id = uuid.uuid4()
        q_tf = create_mock_question(tf_id, "TrueFalse", [])
        q_tf.segments = [
            {"key": "a", "statement": "Ý a", "is_correct": True},
            {"key": "b", "statement": "Ý b", "is_correct": False},
            {"key": "c", "statement": "Ý c", "is_correct": True},
            {"key": "d", "statement": "Ý d", "is_correct": False},
        ]
        mock_exercise = MagicMock()
        mock_exercise.questions = [q_tf]
        service.exercise_repo.get_by_id = MagicMock(return_value=mock_exercise)

        answers = [AnswerInput(question_id=tf_id, answer_text="a:true;b:false;c:true;d:false")]
        score, detailed = service.grade_attempt(exercise_id, answers)

        assert score == 10.00
        tf_res = detailed["questions"][0]
        assert tf_res["is_correct"] is True
        assert tf_res["sub_results"] == {"a": True, "b": True, "c": True, "d": True}

    def test_short_answer_wrong_gets_zero(self):
        """Trả lời ngắn sai -> is_correct False, không pending, không cộng điểm."""
        db = MagicMock()
        service = GradingService(db)
        exercise_id = uuid.uuid4()
        sa_id = uuid.uuid4()
        q_sa = create_mock_question(sa_id, "ShortAnswer", [])
        q_sa.correct_answer = "46"
        mock_exercise = MagicMock()
        mock_exercise.questions = [q_sa]
        service.exercise_repo.get_by_id = MagicMock(return_value=mock_exercise)

        score, detailed = service.grade_attempt(exercise_id, [AnswerInput(question_id=sa_id, answer_text="45")])
        assert score == 0.0
        assert detailed["questions"][0]["is_correct"] is False
        assert detailed["questions"][0]["pending_manual_grade"] is False
