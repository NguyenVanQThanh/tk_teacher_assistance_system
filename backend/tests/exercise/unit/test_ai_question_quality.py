# File Name: test_ai_question_quality.py
# Description: Unit tests for deterministic AI question quality validators and the optional LLM judge.
# Created At: 2026-11-17
# Created By: AI Agent
# Updated At: 2026-11-17
# Updated By: AI Agent

import pytest

from app.modules.exercise.services import ai_generator_service as gen
from app.modules.exercise.services.ai_generator_service import (
    AiExerciseGeneratorService as Svc, validate_question, validate_short,
)


def mcq(content="Q", opts=("a", "b", "c", "d"), correct=0):
    return {"content": content,
            "answer_options": [{"content": o, "is_correct": i == correct} for i, o in enumerate(opts)]}


def tf(content="Q", statements=("s1", "s2", "s3", "s4")):
    return {"content": content, "segments": [
        {"key": k, "statement": s, "is_correct": i % 2 == 0} for i, (k, s) in enumerate(zip("abcd", statements))]}


@pytest.mark.parametrize("raw,expected", [("12", "12"), ("-1,5", "-1,5"), ("0,25", "0,25"), ("2025", "2025"),
                                          ("2.5", "2,5")])
def test_short_numeric_ok(raw, expected):
    assert validate_short({"correct_answer": raw})[0] == {"correct_answer": expected}


@pytest.mark.parametrize("raw", ["12345", "-12,5", "abc", "1/2", "phản ứng trùng hợp"])
def test_short_rejected(raw):
    assert validate_short({"correct_answer": raw})[0] is None


@pytest.mark.parametrize("stem", ["Liệt kê các chất sau", "Nêu tên chất X", "Giải thích hiện tượng", "Vì sao A tan?"])
def test_part3_list_question_rejected(stem):
    out, err = validate_question("Part3", {"content": stem, "correct_answer": "2"})
    assert out is None and "numeric" in err


def test_meta_reference_rejected_per_part():
    assert validate_question("Part1", mcq("Theo SGK, chất nào đúng?"))[0] is None
    assert validate_question("Part1", mcq("Q", ("a", "trong sách giáo khoa", "c", "d")))[0] is None
    assert validate_question("Part2", tf("Q", ("s1", "s2", "theo đoạn văn trên", "s4")))[0] is None
    assert validate_question("Part3", {"content": "Đoạn văn trên nói gì? Tính số mol", "correct_answer": "2"})[0] is None
    ok, _ = validate_question("Part3", {"content": "Tính số mol", "correct_answer": "2", "source_ref": "SGK Hoa hoc 12 tr.14"})
    assert ok["source_ref"] == "SGK Hoa hoc 12 tr.14"


def test_mcq_all_of_the_above_rejected():
    assert validate_question("Part1", mcq("Q", ("a", "b", "c", "Tất cả các đáp án trên")))[0] is None


def test_tf_duplicate_statements_rejected():
    assert validate_question("Part2", tf("Q", ("Giống nhau", "giống NHAU", "x", "y")))[0] is None


def test_dedup_ignores_case_and_diacritics(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "k")
    monkeypatch.setattr(gen.config, "AI_PART_MAX_RETRIES", 1)
    calls = []

    def fake(cls, api_key, part, prompt, temperature):
        calls.append(prompt)
        if len(calls) == 1:
            return [{"content": "Tính số mol", "correct_answer": "1"}, {"content": "TINH SO MOL", "correct_answer": "2"}]
        return [{"content": "Tính khối lượng", "correct_answer": "3"}]

    monkeypatch.setattr(Svc, "_call_mistral_part", classmethod(fake))
    out = Svc.generate_part("Part3", ["NhanBiet"] * 2, "", "", "r", "Hoa", "12")
    assert [q["correct_answer"] for q in out] == ["1", "3"]


def _two_mcq_fake(calls):
    def fake(cls, api_key, part, prompt, temperature):
        calls.append(prompt)
        if len(calls) == 1:
            return [mcq("Q1"), mcq("Q2")]
        return [mcq("Q3")]
    return classmethod(fake)


def test_judge_rejects_and_regenerates_only_rejected(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "k")
    monkeypatch.setattr(gen.config, "AI_JUDGE_ENABLED", True)
    monkeypatch.setattr(gen.config, "AI_PART_MAX_RETRIES", 2)
    calls = []
    monkeypatch.setattr(Svc, "_call_mistral_part", _two_mcq_fake(calls))
    judged = []

    def judge(cls, part, items_json, context, subject_name=""):
        judged.append(items_json)
        if len(judged) == 1:
            return [{"i": 0, "ans": "A", "ok": True}, {"i": 1, "ans": "C", "ok": False, "why": "ambiguous"}]
        return [{"i": 0, "ans": "A", "ok": True}]

    monkeypatch.setattr(Svc, "_call_judge", classmethod(judge))
    out = Svc.generate_part("Part1", ["NhanBiet"] * 2, "", "", "r", "Hoa", "12")
    assert [q["content"] for q in out] == ["Q1", "Q3"]
    assert "exactly 1 NEW" in calls[1] and "reviewer: ambiguous" in calls[1]
    assert "is_correct" not in judged[0]


def test_judge_failure_fails_open(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "k")
    monkeypatch.setattr(gen.config, "AI_JUDGE_ENABLED", True)
    monkeypatch.setattr(Svc, "_call_mistral_part", _two_mcq_fake([]))

    def boom(cls, *a):
        raise RuntimeError("down")

    monkeypatch.setattr(Svc, "_call_judge", classmethod(boom))
    assert len(Svc.generate_part("Part1", ["NhanBiet"] * 2, "", "", "r", "Hoa", "12")) == 2


def test_judge_rejected_questions_are_never_persisted(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "k")
    monkeypatch.setattr(gen.config, "AI_JUDGE_ENABLED", True)
    monkeypatch.setattr(gen.config, "AI_PART_MAX_RETRIES", 0)
    monkeypatch.setattr(Svc, "_call_mistral_part", _two_mcq_fake([]))
    monkeypatch.setattr(Svc, "_call_judge", classmethod(
        lambda cls, part, items, ctx, subj="": [{"i": 0, "ok": False, "why": "bad"}, {"i": 1, "ok": False, "why": "bad"}]))
    with pytest.raises(RuntimeError):
        Svc.generate_part("Part1", ["NhanBiet"] * 2, "", "", "r", "Hoa", "12")


def test_judge_disabled_not_called(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "k")
    monkeypatch.setattr(gen.config, "AI_JUDGE_ENABLED", False)
    monkeypatch.setattr(Svc, "_call_mistral_part", _two_mcq_fake([]))

    def boom(cls, *a):
        raise AssertionError("judge must not be called")

    monkeypatch.setattr(Svc, "_call_judge", classmethod(boom))
    assert len(Svc.generate_part("Part1", ["NhanBiet"] * 2, "", "", "r", "Hoa", "12")) == 2


def test_reviewing_stage_reported(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "k")
    monkeypatch.setattr(gen.config, "AI_JUDGE_ENABLED", True)
    monkeypatch.setattr(Svc, "_call_mistral_part", _two_mcq_fake([]))
    monkeypatch.setattr(Svc, "_call_judge", classmethod(lambda cls, part, items, ctx, subj="": []))
    stages = []
    Svc.generate_part("Part1", ["NhanBiet"] * 2, "", "", "r", "Hoa", "12", on_stage=stages.append)
    assert stages == ["REVIEWING", "GENERATING"]


def test_passage_reference_allowed_with_long_stem_only():
    long_stem = "Đọc đoạn trích sau. " + "x" * 300 + " Theo đoạn trích trên, ý nào đúng?"
    assert validate_question("Part1", mcq(long_stem))[0] is not None
    assert validate_question("Part1", mcq("Theo đoạn trích trên, ý nào đúng?"))[0] is None
    assert validate_question("Part1", mcq("Theo SGK " + "x" * 300))[0] is None
    assert validate_question("Part1", mcq("Theo SGK, chất nào đúng?"))[0] is None


def test_subject_rule_in_prompt():
    args = ("Part1", ["NhanBiet"], "", "", "")
    assert "in English" in gen.build_part_prompt(*args, "Tiếng Anh", "Lớp 12")
    assert "in English" not in gen.build_part_prompt(*args, "Hóa học", "Lớp 12")
    assert gen._subject_rule("Âm nhạc") == ""


def test_judge_answer_replaces_disputed_key():
    q1 = {"answer_options": [{"content": c, "is_correct": c == "a"} for c in "abcd"], "explanation": "old"}
    q2 = {"segments": [{"key": k, "statement": k, "is_correct": True} for k in "abcd"],
          "answer_options": [{"content": k, "is_correct": True} for k in "abcd"], "explanation": "old"}
    q3 = {"correct_answer": "5", "explanation": "old"}
    assert gen._adopt_judge_key("Part1", q1, "c") and [o["is_correct"] for o in q1["answer_options"]] == [False, False, True, False]
    assert gen._adopt_judge_key("Part2", q2, "DSSD")
    assert [s["is_correct"] for s in q2["segments"]] == [True, False, False, True]
    assert [o["is_correct"] for o in q2["answer_options"]] == [True, False, False, True]
    assert gen._adopt_judge_key("Part3", q3, "12,5") and q3["correct_answer"] == "12,5" and q3["explanation"] is None
    assert not gen._adopt_judge_key("Part1", q1, "E") and not gen._adopt_judge_key("Part2", q2, "DSX")
    assert not gen._adopt_judge_key("Part3", q3, "twelve")


def test_review_batch_adopts_reviewer_answer(monkeypatch):
    monkeypatch.setattr(gen.config, "AI_JUDGE_ENABLED", True)
    monkeypatch.setattr(Svc, "_call_judge", classmethod(lambda cls, part, items, ctx, subj="": [{"i": 0, "ans": "B", "ok": True}]))
    q = {"content": "Q", "answer_options": [{"content": c, "is_correct": c == "a"} for c in "abcd"]}
    assert Svc.review_batch("Part1", [q], "") == [None]
    assert [o["is_correct"] for o in q["answer_options"]] == [False, True, False, False]
