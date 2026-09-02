# File Name: test_gemini_vision_parser.py
# Description: Unit tests for GeminiVisionParserService and its integration with ImportParserService.
# Created At: 2026-09-02
# Created By: Tam Khang
# Updated At: 2026-09-02
# Updated By: Tam Khang

import json
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image

from app.modules.exercise.schemas import QuestionTypeEnum, DifficultyEnum
from app.modules.exercise.services.gemini_vision_parser_service import GeminiVisionParserService
from app.modules.exercise.services.import_parser_service import ImportParserService


class TestGeminiVisionParserService:
    """Test suite for GeminiVisionParserService functionality."""

    def test_is_available_when_key_present(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key_12345")
        assert GeminiVisionParserService.is_available() is True
        assert GeminiVisionParserService.get_api_key() == "test_gemini_key_12345"

    def test_is_available_when_key_absent(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_KEY", raising=False)
        assert GeminiVisionParserService.is_available() is False

    def test_process_gemini_json_response_success(self):
        sample_json = json.dumps({
            "questions": [
                {
                    "question_number": 1,
                    "part": "Part1",
                    "question_type": "MultipleChoice",
                    "difficulty": "NhanBiet",
                    "content": "Cho hàm số $f(x) = x^3 - 3x^2 + 2$. Giá trị cực đại của hàm số là:",
                    "content_markdown": "Cho hàm số $f(x) = x^3 - 3x^2 + 2$. Giá trị cực đại của hàm số là:",
                    "content_latex": "$f(x) = x^3 - 3x^2 + 2$",
                    "answer_options": [
                        {"content": "$0$", "is_correct": False, "display_order": 0},
                        {"content": "$2$", "is_correct": True, "display_order": 1},
                        {"content": "$-2$", "is_correct": False, "display_order": 2},
                        {"content": "$4$", "is_correct": False, "display_order": 3}
                    ],
                    "correct_answer": "B"
                },
                {
                    "question_number": 2,
                    "part": "Part2",
                    "question_type": "TrueFalse",
                    "difficulty": "ThongHieu",
                    "content": "Cho hàm số $y = f(x)$ liên tục trên $\\mathbb{R}$.",
                    "answer_options": [
                        {"content": "a) Hàm số đồng biến trên $(0; 2)$", "is_correct": True, "display_order": 0},
                        {"content": "b) Hàm số có 2 điểm cực trị", "is_correct": True, "display_order": 1},
                        {"content": "c) $f(0) = 5$", "is_correct": False, "display_order": 2},
                        {"content": "d) Giá trị nhỏ nhất là $-1$", "is_correct": False, "display_order": 3}
                    ]
                },
                {
                    "question_number": 3,
                    "part": "Part3",
                    "question_type": "ShortAnswer",
                    "difficulty": "VanDung",
                    "content": "Tìm số nghiệm nguyên của phương trình $\\log_2(x-1) < 3$.",
                    "answer_options": [],
                    "correct_answer": "7"
                }
            ]
        })

        result = GeminiVisionParserService._process_gemini_json_response(sample_json)
        assert len(result.errors) == 0
        assert len(result.questions) == 3

        # Verify Part 1
        q1 = result.questions[0]
        assert q1.question_number == 1
        assert q1.part == "Part1"
        assert q1.question_type == QuestionTypeEnum.MultipleChoice
        assert q1.difficulty == DifficultyEnum.NhanBiet
        assert len(q1.answer_options) == 4
        assert q1.answer_options[1].is_correct is True
        assert q1.answer_options[1].content == "$2$"

        # Verify Part 2
        q2 = result.questions[1]
        assert q2.question_number == 2
        assert q2.part == "Part2"
        assert q2.question_type == QuestionTypeEnum.TrueFalse
        assert len(q2.answer_options) == 4

        # Verify Part 3
        q3 = result.questions[2]
        assert q3.question_number == 3
        assert q3.part == "Part3"
        assert q3.question_type == QuestionTypeEnum.ShortAnswer
        assert q3.correct_answer == "7"

    def test_process_gemini_json_response_with_markdown_fences(self):
        fenced_json = """```json
        {
            "questions": [
                {
                    "question_number": 1,
                    "part": "Part1",
                    "question_type": "MultipleChoice",
                    "content": "Tính đạo hàm $f'(x)$",
                    "answer_options": [
                        {"content": "$2x$", "is_correct": true, "display_order": 0}
                    ]
                }
            ]
        }
        ```"""
        result = GeminiVisionParserService._process_gemini_json_response(fenced_json)
        assert len(result.errors) == 0
        assert len(result.questions) == 1
        assert result.questions[0].content == "Tính đạo hàm $f'(x)$"

    def test_process_gemini_invalid_json(self):
        invalid_json = "This is not valid json {"
        result = GeminiVisionParserService._process_gemini_json_response(invalid_json)
        assert len(result.errors) > 0
        assert len(result.questions) == 0

    @patch("app.modules.exercise.services.gemini_vision_parser_service.GeminiVisionParserService.parse_pdf_document")
    def test_import_parser_service_gemini_integration(self, mock_parse_pdf, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_parse_pdf.return_value = GeminiVisionParserService._process_gemini_json_response(json.dumps({
            "questions": [
                {
                    "question_number": 1,
                    "part": "Part1",
                    "question_type": "MultipleChoice",
                    "content": "Test Question from Gemini",
                    "answer_options": [
                        {"content": "$A$", "is_correct": True, "display_order": 0}
                    ]
                }
            ]
        }))

        pdf_dummy_bytes = b"%PDF-1.4 dummy content"
        res = ImportParserService.parse_document(pdf_dummy_bytes, "exam.pdf")

        assert mock_parse_pdf.called
        assert len(res.questions) == 1
        assert res.questions[0].content == "Test Question from Gemini"
