# File Name: test_grading_report_service.py
# Description: Unit tests for grading report export: CSV formula-injection guard and PDF smoke test.
# Created At: 2026-11-13
# Created By: AI Agent
# Updated At: 2026-11-13
# Updated By: AI Agent

import csv
import io
import uuid
from datetime import datetime

from app.modules.exercise.schemas import AttemptListItemOut
from app.modules.exercise.services.grading_report_service import build_csv, build_pdf


def _item(name: str, score=None) -> AttemptListItemOut:
    return AttemptListItemOut(
        attempt_id=uuid.uuid4(), assignment_id=uuid.uuid4(), student_id=uuid.uuid4(),
        student_name=name, class_id=uuid.uuid4(), class_name="Lớp 12A1", exercise_id=uuid.uuid4(),
        exercise_title="Kiểm tra", score=score, is_finished=True, status="approved",
        end_time=datetime(2026, 11, 13, 8, 30),
    )


def test_csv_neutralises_formula_injection():
    data = build_csv([_item('=HYPERLINK("x")', 7.5), _item("@cmd"), _item("+1"), _item("-2"),
                      _item("\tx"), _item("Nguyễn An")])
    assert data.startswith("﻿".encode("utf-8"))
    rows = list(csv.reader(io.StringIO(data.decode("utf-8-sig"))))
    assert rows[0][0] == "Student"
    assert [r[0] for r in rows[1:]] == ["'=HYPERLINK(\"x\")", "'@cmd", "'+1", "'-2", "'\tx", "Nguyễn An"]
    assert rows[1][3] == "7.50" and rows[2][3] == ""


def test_pdf_smoke():
    assert build_pdf([_item("Nguyễn An", 8.0), _item("Trần Bình")]).startswith(b"%PDF")
    assert build_pdf([]).startswith(b"%PDF")
