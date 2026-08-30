# File Name: test_import_parser_service.py
# Description: Unit tests for ImportParserService (questions, answer keys, 3 parts, difficulty tags).
# Created At: 2026-08-09
# Created By: Tam Khang
# Updated At: 2026-08-09
# Updated By: Tam Khang

import pytest
from app.modules.exercise.schemas import QuestionTypeEnum, DifficultyEnum
from app.modules.exercise.services.import_parser_service import ImportParserService, ParsedOption


def test_extract_difficulty():
    assert ImportParserService.extract_difficulty("Câu 1. [NB] 2 + 2 = ?") == DifficultyEnum.NhanBiet
    assert ImportParserService.extract_difficulty("Câu 2. [TH] Nghiệm của phuong trinh...") == DifficultyEnum.ThongHieu
    assert ImportParserService.extract_difficulty("Câu 3. [VD] Tìm m để...") == DifficultyEnum.VanDung
    # Missing tag defaults to None
    assert ImportParserService.extract_difficulty("Câu 4. Trong không gian Oxyz...") is None


def test_parse_part1_question():
    text = "Câu 1. [NB] 2 + 2 x 3 bằng bao nhiêu?\nA. 8\nB. 12\nC. 6\nD. 10"
    q, err = ImportParserService.parse_part1_question(1, text, DifficultyEnum.NhanBiet, None)
    assert err is None
    assert q is not None
    assert q.question_number == 1
    assert q.question_type == QuestionTypeEnum.MultipleChoice
    assert q.difficulty == DifficultyEnum.NhanBiet
    assert len(q.answer_options) == 4
    assert q.answer_options[0].content == "A. 8"
    assert q.answer_options[1].content == "B. 12"


def test_parse_part2_question():
    text = "Câu 2. Cho hàm số y = f(x) = x^2 - 4x + 3.\na) Hàm số đồng biến trên (2, +inf).\nb) Đồ thị cắt trục tung tại (0, -3).\nc) Điểm cực tiểu là (2, -1).\nd) Min = 0."
    q, err = ImportParserService.parse_part2_question(2, text, None, None)
    assert err is None
    assert q is not None
    assert q.question_number == 2
    assert q.question_type == QuestionTypeEnum.TrueFalse
    assert q.difficulty is None  # Optional tag omitted -> None
    assert len(q.answer_options) == 4
    assert q.answer_options[0].content.startswith("a)")


def test_parse_part3_question():
    text = "Câu 3. [VD] Tính thể tích của khối chóp S.ABC."
    q, err = ImportParserService.parse_part3_question(3, text, DifficultyEnum.VanDung, None)
    assert err is None
    assert q is not None
    assert q.question_number == 3
    assert q.question_type == QuestionTypeEnum.ShortAnswer
    assert q.difficulty == DifficultyEnum.VanDung


def test_parse_answer_multi_code_table():
    tables = [
        [
            ["Câu", "Mã đề 0121", "Mã đề 0122"],
            ["1", "B", "A"],
            ["2", "a) Đúng\nb) Sai\nc) Đúng\nd) Sai", "a) Sai\nb) Đúng\nc) Sai\nd) Đúng"],
            ["3", "450", "0,66"]
        ]
    ]
    answers = ImportParserService.parse_answer_keys("", tables, target_test_code="0121")
    assert answers[1] == "B"
    assert answers[2] == {"a": True, "b": False, "c": True, "d": False}
    assert answers[3] == "450"


def test_parse_answer_single_code_table():
    tables = [
        [
            ["STT", "Đáp án"],
            ["1", "C"],
            ["2", "a) Sai, b) Sai, c) Đúng, d) Đúng"],
            ["3", "1,5"]
        ]
    ]
    answers = ImportParserService.parse_answer_keys("", tables, target_test_code=None)
    assert answers[1] == "C"
    assert answers[2] == {"a": False, "b": False, "c": True, "d": True}
    assert answers[3] == "1,5"


def test_parse_answer_text_list():
    text = """
    1. A
    2. a) Đ, b) S, c) Đ, d) S
    3. 450
    """
    answers = ImportParserService.parse_answer_keys(text, [], None)
    assert answers[1] == "A"
    assert answers[2] == {"a": True, "b": False, "c": True, "d": False}
    assert answers[3] == "450"


def test_merge_questions_and_answers_valid():
    q1, _ = ImportParserService.parse_part1_question(1, "Câu 1. 2+2=?\nA. 4\nB. 5", None, None)
    q2, _ = ImportParserService.parse_part2_question(2, "Câu 2. Mệnh đề:\na) Đúng 1\nb) Sai 2", None, None)
    q3, _ = ImportParserService.parse_part3_question(3, "Câu 3. Kết quả bằng bao nhiêu?", None, None)

    answers = {
        1: "A",
        2: {"a": True, "b": False},
        3: "450"
    }
    merged, errors = ImportParserService.merge_questions_and_answers([q1, q2, q3], answers)
    assert len(errors) == 0
    assert len(merged) == 3
    assert merged[0].answer_options[0].is_correct is True
    assert merged[1].answer_options[0].is_correct is True
    assert merged[1].answer_options[1].is_correct is False
    assert merged[2].correct_answer == "450"


def test_merge_questions_and_answers_missing_key():
    q1, _ = ImportParserService.parse_part1_question(1, "Câu 1. 2+2=?\nA. 4\nB. 5", None, None)
    answers = {}
    merged, errors = ImportParserService.merge_questions_and_answers([q1], answers)
    assert len(errors) == 1
    assert "Missing answer key" in errors[0].message


def test_convert_latex_to_markdown():
    raw_text = r"Vận tốc ban đầu $\vec{v} = \vec{a} + \vec{b}$ trong thời gian $t_1$ với phân số $\frac{x}{y}$ và $x^2$."
    converted = ImportParserService.convert_latex_to_markdown(raw_text)
    assert "v\u20d7 = a\u20d7 + b\u20d7" in converted
    assert "t₁" in converted
    assert "(x)/(y)" in converted
    assert "x²" in converted

    # Test parse_part1_question populates content_markdown, content_latex, segments, confidence, needs_review
    q, err = ImportParserService.parse_part1_question(1, f"Câu 1. {raw_text}\nA. 1\nB. 2", None, None)
    assert err is None
    assert q.content_latex == raw_text
    assert "v\u20d7 = a\u20d7 + b\u20d7" in q.content_markdown
    assert q.segments is not None
    assert len(q.segments) > 0
    assert q.needs_review is False
    assert q.confidence_score is not None


def test_normalize_latex():
    raw_latex = r"\frac { 2 x } { x ^ { 2 } + 1 }"
    norm = ImportParserService.normalize_latex(raw_latex)
    assert r"\frac{2x}{x^{2} + 1}" in norm or r"\frac{2x}" in norm


def test_validate_latex():
    valid_latex = r"\frac{2x}{x^2+1} + \sqrt{x}"
    is_valid, err = ImportParserService.validate_latex(valid_latex)
    assert is_valid is True
    assert err is None

    invalid_latex = r"\frac{2x}{x^2+1"  # Unclosed brace
    is_valid, err = ImportParserService.validate_latex(invalid_latex)
    assert is_valid is False
    assert "Unclosed brace" in err


def test_extract_segments_inline_and_display():
    text = r"Cho hàm số $f(x)=x^2+1$. Tính giá trị của: $$\int_{0}^{1} f(x) dx$$"
    segments, needs_review = ImportParserService.extract_segments(text)
    assert len(segments) == 4
    assert segments[0]["type"] == "text"
    assert segments[0]["content"] == "Cho hàm số "
    assert segments[1]["type"] == "math"
    assert segments[1]["display"] is False
    assert segments[2]["type"] == "text"
    assert segments[3]["type"] == "math"
    assert segments[3]["display"] is True
    assert needs_review is False


def test_extract_segments_with_corrupted_math():
    text = r"Tính giới hạn $\lim_{x\to 0} \frac{x}{x+1}$"
    # An actually corrupted formula with missing closing brace:
    corrupted_text = r"Tính giới hạn $\lim_{x\to 0} \frac{x}{x+1$"
    segments, needs_review = ImportParserService.extract_segments(corrupted_text)
    assert needs_review is True
    assert segments[1]["confidence"] == 0.60




