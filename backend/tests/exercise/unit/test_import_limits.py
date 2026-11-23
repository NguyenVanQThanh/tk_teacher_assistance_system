# File Name: test_import_limits.py
# Description: Unit tests for the OCR import caps (PDF page cap, guest import quota).
# Created At: 2026-11-18
# Created By: AI Agent
# Updated At: 2026-11-18
# Updated By: AI Agent

from types import SimpleNamespace

import fitz
import pytest
from fastapi import HTTPException

from app.core import config
from app.modules.exercise.routers import exercises as ex


def _pdf(pages: int) -> bytes:
    doc = fitz.open()
    for _ in range(pages):
        doc.new_page()
    return doc.tobytes()


def test_page_cap_rejects_long_pdf(monkeypatch):
    monkeypatch.setattr(config, "IMPORT_MAX_PDF_PAGES", 2)
    ex._enforce_import_page_cap("a.pdf", _pdf(2))
    with pytest.raises(HTTPException) as e:
        ex._enforce_import_page_cap("a.pdf", _pdf(3))
    assert e.value.status_code == 413 and e.value.detail["code"] == "ERR-EXE-IMPORT_TOO_MANY_PAGES"


def test_page_cap_ignores_docx_but_rejects_corrupt_pdf():
    ex._enforce_import_page_cap("a.docx", b"x" * 10)
    with pytest.raises(HTTPException) as e:
        ex._enforce_import_page_cap("a.pdf", b"not a pdf")
    assert e.value.status_code == 422 and e.value.detail["code"] == "ERR-EXE-IMPORT_FILE_UNREADABLE"


class _Q:
    def __init__(self, n):
        self.n = n

    def filter(self, *a):
        return self

    def count(self):
        return self.n


def test_guest_import_limit(monkeypatch):
    monkeypatch.setattr(config, "GUEST_IMPORT_LIMIT", 3)
    guest = SimpleNamespace(is_guest=True, user_id="u")
    ex._enforce_guest_import_limit(SimpleNamespace(query=lambda *a: _Q(2), get_bind=lambda: SimpleNamespace(dialect=SimpleNamespace(name="sqlite"))), guest)
    with pytest.raises(HTTPException) as e:
        ex._enforce_guest_import_limit(SimpleNamespace(query=lambda *a: _Q(3), get_bind=lambda: SimpleNamespace(dialect=SimpleNamespace(name="sqlite"))), guest)
    assert e.value.status_code == 403 and e.value.detail["code"] == "ERR-EXE-GUEST_IMPORT_LIMIT"
    # regular users are never capped
    ex._enforce_guest_import_limit(SimpleNamespace(query=lambda *a: _Q(99)), SimpleNamespace(is_guest=False, user_id="u"))
