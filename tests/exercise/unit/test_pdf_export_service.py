# File Name: test_pdf_export_service.py
# Description: Unit tests for PdfExportService PDF generation and LaTeX math formula rendering.
# Created At: 2026-08-12
# Created By: Tam Khang
# Updated At: 2026-08-12
# Updated By: Tam Khang

import uuid
import pytest
from unittest.mock import MagicMock

from models.models import Exercise, Question, AnswerOption
from app.modules.exercise.services.pdf_export_service import PdfExportService
from app.modules.exercise.schemas import QuestionTypeEnum, DifficultyEnum


def test_latex_to_image_render():
    """Test LaTeX formula string rendering to PNG BytesIO."""
    latex_str = "$y = f(x) = x^3 - 3x^2 + 2$"
    img_buf = PdfExportService.render_latex_to_image(latex_str)
    assert img_buf is not None
    assert len(img_buf.getvalue()) > 0


def test_generate_exercise_pdf_success():
    """Test generating a full exercise PDF byte stream."""
    exercise_id = uuid.uuid4()
    exercise = MagicMock(spec=Exercise)
    exercise.exercise_id = exercise_id
    exercise.title = "Đề thi minh họa Toán 12"

    # Question 1: Multiple Choice
    q1 = MagicMock(spec=Question)
    q1.display_order = 1
    q1.question_type = QuestionTypeEnum.MultipleChoice.value
    q1.difficulty = DifficultyEnum.NhanBiet.value
    q1.content = "Cho hàm số $f(x) = x^3 - 3x^2 + 2$. Giá trị cực đại là:"
    
    opt1 = MagicMock(spec=AnswerOption)
    opt1.display_order = 1
    opt1.content = "0"
    opt1.is_correct = True

    opt2 = MagicMock(spec=AnswerOption)
    opt2.display_order = 2
    opt2.content = "2"
    opt2.is_correct = False

    q1.answer_options = [opt1, opt2]

    # Question 2: Short Answer
    q2 = MagicMock(spec=Question)
    q2.display_order = 2
    q2.question_type = QuestionTypeEnum.ShortAnswer.value
    q2.difficulty = DifficultyEnum.VanDung.value
    q2.content = "Tính khoảng cách từ $A(1; 2; 3)$ đến mặt phẳng."
    q2.correct_answer = "5"
    q2.answer_options = []

    exercise.questions = [q1, q2]

    pdf_bytes = PdfExportService.generate_exercise_pdf(exercise)
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF-")
