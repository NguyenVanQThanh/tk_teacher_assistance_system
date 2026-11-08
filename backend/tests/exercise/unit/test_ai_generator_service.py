# File Name: test_ai_generator_service.py
# Description: Unit tests for AI exercise generator: no duplicate questions across parts and cognitive-level distribution (NhanBiet/ThongHieu/VanDung).
# Created At: 2026-11-08
# Created By: Tam Khang

import pytest

from app.modules.exercise.services.ai_generator_service import AiExerciseGeneratorService as S


def _keys(questions):
    return [S._question_dedupe_key(q) for q in questions]


def test_dedupe_questions_removes_duplicates():
    qs = [
        {"part": "Part1", "content": "Câu 1: Đun nóng este X?", "answer_options": []},
        {"part": "Part1", "content": "Câu 9: Đun nóng este X?"},  # trùng nội dung, khác số câu
        {"part": "Part1", "content": "Câu 2: Este nào sau đây là no?", "answer_options": []},
        {"part": "Part2", "content": "Câu 3: Xét mệnh đề", "segments": [
            {"key": "a", "statement": "Ý a", "is_correct": True},
            {"key": "b", "statement": "Ý b", "is_correct": False},
        ]},
        {"part": "Part2", "content": "Xét mệnh đề", "segments": [  # trùng cả nội dung lẫn segments
            {"key": "a", "statement": "Ý a", "is_correct": True},
            {"key": "b", "statement": "Ý b", "is_correct": False},
        ]},
    ]
    out = S._dedupe_questions(qs)
    assert len(out) == 3
    assert len(set(_keys(out))) == len(out)


def test_difficulty_plan_ratio():
    plan = S._difficulty_plan(15)
    assert plan["NhanBiet"] + plan["ThongHieu"] + plan["VanDung"] == 15
    assert plan["NhanBiet"] == 6 and plan["ThongHieu"] == 6 and plan["VanDung"] == 3
    assert S._difficulty_plan(1) == {"NhanBiet": 1, "ThongHieu": 0, "VanDung": 0}
    assert S._difficulty_plan(3) == {"NhanBiet": 1, "ThongHieu": 1, "VanDung": 1}


def test_assign_difficulty_distribution_per_part():
    qs = (
        [{"part": "Part1", "difficulty": None} for _ in range(10)]
        + [{"part": "Part2", "difficulty": None} for _ in range(3)]
        + [{"part": "Part3", "difficulty": None} for _ in range(6)]
    )
    out = S._assign_difficulty_distribution(qs)
    for part, n in (("Part1", 10), ("Part2", 3), ("Part3", 6)):
        diffs = [q["difficulty"] for q in out if q["part"] == part]
        assert set(diffs) == {"NhanBiet", "ThongHieu", "VanDung"}
        assert len(diffs) == n
    p1 = [q["difficulty"] for q in out if q["part"] == "Part1"]
    assert p1.count("NhanBiet") == 4 and p1.count("ThongHieu") == 4 and p1.count("VanDung") == 2


def test_fallback_questions_unique_across_all_parts():
    qs = S._generate_curriculum_questions(
        subject_name="Hóa học",
        grade_name="Lớp 12",
        topic_prompt="Este và Lipit",
        part1_count=15,
        part2_count=3,
        part3_count=6,
    )
    keys = _keys(qs)
    assert len(keys) == len(set(keys)), "fallback phải không có câu trùng lặp"
    parts = {q["part"] for q in qs}
    assert parts == {"Part1", "Part2", "Part3"}
    # số câu mỗi phần không vượt quá số câu duy nhất có trong pool mở rộng
    assert sum(1 for q in qs if q["part"] == "Part1") >= 10
    assert sum(1 for q in qs if q["part"] == "Part2") >= 3
    assert sum(1 for q in qs if q["part"] == "Part3") >= 6


def test_fallback_unique_for_other_subjects():
    for subject, topic in [
        ("Lịch sử", "Cách mạng tháng Tám 1945"),
        ("Toán học", "Hàm số bậc ba"),
        ("Ngữ văn", "Văn học trung đại"),
    ]:
        qs = S._generate_curriculum_questions(
            subject_name=subject, grade_name="Lớp 12", topic_prompt=topic,
            part1_count=15, part2_count=3, part3_count=6,
        )
        keys = _keys(qs)
        assert len(keys) == len(set(keys)), f"{subject}: phát hiện câu trùng lặp"


def test_generate_questions_fallback_path_no_api_key(monkeypatch):
    monkeypatch.setattr(
        "app.modules.exercise.services.ai_generator_service.GeminiVisionParserService.get_api_key",
        classmethod(lambda cls: None),
    )
    qs = S.generate_questions(
        subject_name="Hóa học", grade_name="Lớp 12", topic_prompt="Este và Lipit",
        part1_count=15, part2_count=3, part3_count=6,
    )
    keys = _keys(qs)
    assert len(keys) == len(set(keys)), "không được có câu trùng lặp ở cả 3 phần"
    for part in ("Part1", "Part2", "Part3"):
        diffs = {q["difficulty"] for q in qs if q["part"] == part}
        assert diffs <= {"NhanBiet", "ThongHieu", "VanDung"}
    # mỗi phần phải có đủ cả 3 cấp độ nhận thức khi số câu >= 3
    for part, n in (("Part1", 15), ("Part2", 3), ("Part3", 6)):
        got = sum(1 for q in qs if q["part"] == part)
        if got >= 3:
            diffs = {q["difficulty"] for q in qs if q["part"] == part}
            assert diffs == {"NhanBiet", "ThongHieu", "VanDung"}


def test_generate_questions_dedupes_ai_output(monkeypatch):
    fake_ai = [
        {"part": "Part1", "question_type": "MultipleChoice", "difficulty": "NhanBiet",
         "content": "Câu 1: Đun este X?", "answer_options": [{"content": "A", "is_correct": True, "display_order": 0}]},
        {"part": "Part1", "question_type": "MultipleChoice", "difficulty": "NhanBiet",
         "content": "Câu 5: Đun este X?", "answer_options": [{"content": "A", "is_correct": True, "display_order": 0}]},  # trùng
        {"part": "Part1", "question_type": "MultipleChoice", "difficulty": "VanDung",
         "content": "Câu 2: Este no là?", "answer_options": [{"content": "B", "is_correct": True, "display_order": 0}]},
        {"part": "Part2", "question_type": "TrueFalse", "difficulty": "ThongHieu",
         "content": "Câu 3: Xét mệnh đề", "segments": [{"key": "a", "statement": "Ý a", "is_correct": True}]},
        {"part": "Part3", "question_type": "ShortAnswer", "difficulty": "VanDung",
         "content": "Câu 4: Số liên kết pi?", "correct_answer": "1"},
    ]
    monkeypatch.setattr(
        "app.modules.exercise.services.ai_generator_service.GeminiVisionParserService.get_api_key",
        classmethod(lambda cls: "fake-key"),
    )
    monkeypatch.setattr(S, "_call_gemini_generator", classmethod(lambda cls, **kw: list(fake_ai)))
    qs = S.generate_questions(
        subject_name="Hóa học", grade_name="Lớp 12", topic_prompt="Este",
        part1_count=2, part2_count=1, part3_count=1,
    )
    keys = _keys(qs)
    assert len(keys) == len(set(keys))
    assert len(qs) == 4  # 2 câu Part1 (đã loại 1 trùng) + 1 Part2 + 1 Part3
    p1 = [q["difficulty"] for q in qs if q["part"] == "Part1"]
    assert set(p1) == {"NhanBiet", "ThongHieu"}  # 2 câu -> 1 NB + 1 TH theo phân bố


def test_provider_chain_mistral_primary_gemini_fallback(monkeypatch):
    """Mistral là provider chính; chỉ khi Mistral fail mới gọi Gemini."""
    calls = []

    def fake_mistral(**kw):
        calls.append("mistral")
        return [
            {"part": "Part1", "question_type": "MultipleChoice", "difficulty": None,
             "content": "Câu 1: Nội dung từ Mistral?", "answer_options": [{"content": "A", "is_correct": True, "display_order": 0}]},
        ]

    def fake_gemini(**kw):
        calls.append("gemini")
        return [
            {"part": "Part1", "question_type": "MultipleChoice", "difficulty": None,
             "content": "Câu 1: Nội dung từ Gemini?", "answer_options": [{"content": "A", "is_correct": True, "display_order": 0}]},
        ]

    monkeypatch.setattr(S, "_get_mistral_config", staticmethod(lambda: ("m-key", "pixtral-12b-2409", "https://api.mistral.ai/v1/chat/completions")))
    monkeypatch.setattr(
        "app.modules.exercise.services.ai_generator_service.GeminiVisionParserService.get_api_key",
        classmethod(lambda cls: "g-key"),
    )
    monkeypatch.setattr(S, "_call_mistral_generator", classmethod(lambda cls, **kw: fake_mistral(**kw)))
    monkeypatch.setattr(S, "_call_gemini_generator", classmethod(lambda cls, **kw: fake_gemini(**kw)))

    qs = S.generate_questions("Hóa học", "Lớp 12", "Este", 1, 0, 0)
    assert calls == ["mistral"]  # Mistral trả đủ số câu -> không cần gọi Gemini
    assert qs[0]["content"].startswith("Câu 1: Nội dung từ Mistral")


def test_provider_chain_gemini_only_when_mistral_fails(monkeypatch):
    calls = []

    def fake_mistral(**kw):
        calls.append("mistral")
        raise RuntimeError("Mistral API down")

    def fake_gemini(**kw):
        calls.append("gemini")
        return [
            {"part": "Part1", "question_type": "MultipleChoice", "difficulty": None,
             "content": "Câu 1: Nội dung từ Gemini?", "answer_options": [{"content": "A", "is_correct": True, "display_order": 0}]},
        ]

    monkeypatch.setattr(S, "_get_mistral_config", staticmethod(lambda: ("m-key", "m", "u")))
    monkeypatch.setattr(
        "app.modules.exercise.services.ai_generator_service.GeminiVisionParserService.get_api_key",
        classmethod(lambda cls: "g-key"),
    )
    monkeypatch.setattr(S, "_call_mistral_generator", classmethod(lambda cls, **kw: fake_mistral(**kw)))
    monkeypatch.setattr(S, "_call_gemini_generator", classmethod(lambda cls, **kw: fake_gemini(**kw)))

    qs = S.generate_questions("Hóa học", "Lớp 12", "Este", 1, 0, 0)
    assert calls == ["mistral", "gemini"]
    assert qs[0]["content"].startswith("Câu 1: Nội dung từ Gemini")


def test_parse_json_loose_handles_fences_and_python_literals():
    raw = '```json\n{"questions": [{"is_correct": True, "x": None, "y": False}]}\n```'
    data = S._parse_json_loose(raw)
    assert data["questions"][0]["is_correct"] is True
    assert data["questions"][0]["x"] is None
    assert data["questions"][0]["y"] is False
