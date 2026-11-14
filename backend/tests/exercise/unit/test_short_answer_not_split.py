# File Name: test_short_answer_not_split.py
# Description: Short-answer stems with prose like "kJ. " or "5)" must not be split into fake options.
# Created At: 2026-11-12
# Created By: AI Agent
# Updated At: 2026-11-12
# Updated By: AI Agent

import pytest

from app.modules.exercise.schemas import QuestionTypeEnum
from app.modules.exercise.services.import_parser_service import ImportParserService as P

STEMS = [
    "Câu 1. Một lượng khí nhận một nhiệt lượng 35,4 kJ do được đun nóng, khí giãn nở và thực hiện một công "
    "20,0 kJ ra môi trường xung quanh. Nội năng của khối khí này đã biến thiên một lượng bao nhiêu kilôjun (kJ)? "
    "(Kết quả làm tròn đến hàng phần mười). 5) 6) 7)",
    "Câu 2. Khí nhận công là 450 J. Trong quá trình này, nhiệt lượng cung cấp 7100 J. Bao nhiêu % "
    "tổng nhiệt lượng làm tăng nội năng (làm tròn đến phần nguyên)? 5)",
]


@pytest.mark.parametrize("stem", STEMS)
@pytest.mark.parametrize("fn", [P.parse_part1_question, P.parse_part2_question])
def test_prose_never_becomes_options(stem, fn):
    q, err = fn(1, stem, None, None)
    assert err is None
    assert q.question_type == QuestionTypeEnum.ShortAnswer and q.answer_options == []


def test_real_options_still_split():
    q, _ = P.parse_part1_question(1, "Câu 1. Chọn. A. một B. hai\nC. ba D. bốn", None, None)
    assert len(q.answer_options) == 4
    q, _ = P.parse_part2_question(1, "Câu 1. Xét:\na) x\nb) y\nc) z\nd) w", None, None)
    assert len(q.answer_options) == 4
