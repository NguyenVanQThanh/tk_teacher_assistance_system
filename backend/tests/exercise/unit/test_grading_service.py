# File Name: test_grading_service.py
# Description: Unit tests for F-EXE-04 Auto Grading service (GradingService).
# Created At: 2026-08-08
# Created By: Tam Khang
# Updated At: 2026-11-17
# Updated By: AI Agent

import uuid
from unittest.mock import MagicMock
import pytest

from app.modules.exercise.services.grading_service import GradingService, build_answer_key
from app.modules.exercise.schemas import AnswerInput


def create_mock_question(q_id, q_type, options=None, status="ACTIVE"):
    q = MagicMock()
    q.question_id = q_id
    q.question_type = q_type
    q.status = status
    q.display_order = 0
    q.created_at = None
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

        # MC part and short-answer part split the 10 points evenly (3:3) -> MC question worth 5.0
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

        assert score is None
        assert len(detailed["questions"]) == 2
        assert all(q["pending_manual_grade"] is True for q in detailed["questions"])
        assert all(q["is_correct"] is None for q in detailed["questions"])


    def test_true_false_partial_credit_and_numeric_short_answer(self):
        """Parts are weighted 3/4/3; TF gets partial credit; short answers compare numerically."""
        service = GradingService(MagicMock())
        mc_id, tf_id, sa_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        mc_ok = uuid.uuid4()
        q_mc = create_mock_question(mc_id, "MultipleChoice", [create_mock_option(mc_ok, True)])
        opts = []
        for letter, correct in zip("abcd", (True, True, False, False)):
            o = create_mock_option(uuid.uuid4(), correct)
            o.content = f"{letter}) statement"
            opts.append(o)
        q_tf = create_mock_question(tf_id, "TrueFalse", opts)
        q_sa = create_mock_question(sa_id, "ShortAnswer", [])
        q_sa.correct_answer = "2.50"
        ex = MagicMock()
        ex.questions = [q_mc, q_tf, q_sa]
        service.exercise_repo.get_by_id = MagicMock(return_value=ex)

        answers = [
            AnswerInput(question_id=mc_id, answer_option_id=mc_ok),
            AnswerInput(question_id=tf_id, answer_text="a:true;b:true;c:true;d:false"),  # 3 of 4 correct
            AnswerInput(question_id=sa_id, answer_text="2,5"),
        ]
        score, _ = service.grade_attempt(uuid.uuid4(), answers)
        assert score == 3.0 + 4.0 * 0.5 + 3.0


def _kq(qid, qtype, opts=(), status="ACTIVE", ca=None):
    return type("Q", (), dict(question_id=qid, question_type=qtype, status=status, explanation="ex",
                              correct_answer=ca, answer_options=list(opts)))()


def _ko(content, ok, oid=None):
    return type("O", (), dict(option_id=oid or uuid.uuid4(), content=content, is_correct=ok))()


def test_build_answer_key_all_types():
    ids = [uuid.uuid4() for _ in range(5)]
    oid = uuid.uuid4()
    ex = type("E", (), dict(questions=[
        _kq(ids[0], "MultipleChoice", [_ko("A", False), _ko("B", True, oid)]),
        # options out of order: label follows the 'a) ' prefix, not the position
        _kq(ids[1], "TrueFalse", [_ko("b) two", False), _ko("a) one", True)]),
        _kq(ids[2], "ShortAnswer", ca="2,5"),
        _kq(ids[3], "Other"),
        _kq(ids[4], "ShortAnswer", status="DELETED", ca="9"),
    ]))()
    key = build_answer_key(ex)
    assert key[str(ids[0]).lower()]["correct_option_id"] == str(oid)
    assert key[str(ids[1]).lower()]["correct_values"] == {"b": False, "a": True}
    assert key[str(ids[1]).lower()]["statements"] == {"b": "two", "a": "one"}
    assert key[str(ids[2]).lower()]["correct_answer"] == "2,5"
    assert key[str(ids[3]).lower()] == {"explanation": "ex"}
    assert str(ids[4]).lower() not in key
