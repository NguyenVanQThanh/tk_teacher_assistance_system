# File Name: test_difficulty_and_tf_schema.py
# Description: Unit tests for difficulty normalization and TrueFalse auto-options in QuestionCreate schema.
# Created At: 2026-10-06
# Created By: Tam Khang
# Updated At: 2026-10-06
# Updated By: Tam Khang

import pytest
from app.modules.exercise.schemas import QuestionCreate, QuestionTypeEnum, DifficultyEnum


def test_difficulty_normalization():
    # Vietnamese strings
    q1 = QuestionCreate(
        content="Test question 1",
        question_type=QuestionTypeEnum.ShortAnswer,
        difficulty="Nhận biết",
        correct_answer="4"
    )
    assert q1.difficulty == DifficultyEnum.NhanBiet

    q2 = QuestionCreate(
        content="Test question 2",
        question_type=QuestionTypeEnum.ShortAnswer,
        difficulty="Thông hiểu",
        correct_answer="4"
    )
    assert q2.difficulty == DifficultyEnum.ThongHieu

    q3 = QuestionCreate(
        content="Test question 3",
        question_type=QuestionTypeEnum.ShortAnswer,
        difficulty="Vận dụng",
        correct_answer="4"
    )
    assert q3.difficulty == DifficultyEnum.VanDung

    # Short codes and English keys
    q_nb = QuestionCreate(
        content="Test question NB",
        question_type=QuestionTypeEnum.ShortAnswer,
        difficulty="NB",
        correct_answer="4"
    )
    assert q_nb.difficulty == DifficultyEnum.NhanBiet

    q_enum = QuestionCreate(
        content="Test question Enum",
        question_type=QuestionTypeEnum.ShortAnswer,
        difficulty=DifficultyEnum.VanDung,
        correct_answer="4"
    )
    assert q_enum.difficulty == DifficultyEnum.VanDung


def test_true_false_auto_option_generation():
    # If no answer_options provided, but correct_answer is given
    q_tf = QuestionCreate(
        content="1 + 1 = 2",
        question_type=QuestionTypeEnum.TrueFalse,
        difficulty="NhanBiet",
        correct_answer="Đúng"
    )
    assert q_tf.answer_options is not None
    assert len(q_tf.answer_options) == 1
    assert q_tf.answer_options[0].is_correct is True
    assert "1 + 1 = 2" in q_tf.answer_options[0].content

    # If neither options nor correct_answer is given, it should raise ValueError
    with pytest.raises(ValueError, match="TrueFalse questions must have at least 1 option item"):
        QuestionCreate(
            content="1 + 1 = 2",
            question_type=QuestionTypeEnum.TrueFalse,
            difficulty="NhanBiet",
            correct_answer=None
        )
