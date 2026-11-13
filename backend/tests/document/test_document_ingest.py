# File Name: test_document_ingest.py
# Description: Unit tests for document ingestion (chunking, status transitions, VLM and embedding handling).
# Created At: 2026-11-11
# Created By: AI Agent
# Updated At: 2026-11-11
# Updated By: AI Agent

from unittest.mock import MagicMock

import pytest
from PIL import Image

from app.core.storage import LocalStorage
from app.modules.document.services import document_ingest_service as svc
from app.modules.document.services.document_ingest_service import DocumentIngestService


def test_extract_figures_strips_caption_lines():
    md, caps = svc.extract_figures("Text $x^2$\n[HÌNH: Đồ thị parabol]\nMore")
    assert caps == ["Đồ thị parabol"]
    assert "HÌNH" not in md and "$x^2$" in md


def test_chunk_page_text_table_image():
    md = "# Title\n\nSome text $E=mc^2$.\n\n| a | b |\n| --- | --- |\n| 1 | 2 |\n"
    chunks = svc.chunk_page(3, md, [{"caption": "Hình mạch điện", "path": "x/p3.png"}])
    assert [c["modality"] for c in chunks] == ["text", "table", "image"]
    assert chunks[2]["meta"]["figure_path"] == "x/p3.png"
    assert all(c["page"] == 3 for c in chunks)


def test_big_paragraph_split_keeps_math_intact():
    para = " ".join(f"Câu số {i} dùng $a_{i}+b$ ở đây." for i in range(400))
    chunks = svc.chunk_page(1, para)
    assert len(chunks) > 1
    assert all(c["content"].count("$") % 2 == 0 for c in chunks)


def test_vlm_prompt_and_response(monkeypatch):
    monkeypatch.setattr(svc.MistralVisionParserService, "get_api_key", staticmethod(lambda: "k"))
    seen = {}

    def post(payload, headers):
        seen["p"] = payload
        return "$H_2O$"

    out = svc.vlm_transcribe(Image.new("RGB", (10, 10)), 2, post=post)
    assert out == "$H_2O$"
    assert "LaTeX" in seen["p"]["messages"][0]["content"]
    assert seen["p"]["messages"][1]["content"][1]["type"] == "image_url"


def test_retry_then_raise(monkeypatch):
    monkeypatch.setattr(svc.time, "sleep", lambda s: None)
    calls = {"n": 0}

    def boom():
        calls["n"] += 1
        raise RuntimeError("x")

    with pytest.raises(RuntimeError):
        svc._with_retry(boom, "t")
    assert calls["n"] == svc.MAX_RETRIES


def test_embed_batches(monkeypatch):
    monkeypatch.setattr(svc.MistralVisionParserService, "get_api_key", staticmethod(lambda: "k"))
    monkeypatch.setattr(svc.config, "EMBED_BATCH_SIZE", 2)
    sizes = []

    def post(payload, headers):
        sizes.append(len(payload["input"]))
        return [[0.0] * 3 for _ in payload["input"]]

    assert len(svc.embed_texts(["a", "b", "c"], post=post)) == 3
    assert sizes == [2, 1]


def _db(row=("/uploads/documents/f.pdf", "pdf")):
    db = MagicMock()
    db.execute.return_value.first.return_value = row
    return db


def _statuses(db):
    return [c.args[1]["s"] for c in db.execute.call_args_list if "ingest_status" in str(c.args[0])]


def test_ingest_success_transitions(monkeypatch, tmp_path):
    monkeypatch.setattr(svc, "get_storage", lambda: LocalStorage(tmp_path))
    (tmp_path / "documents").mkdir()
    (tmp_path / "documents" / "f.pdf").write_bytes(b"x")
    monkeypatch.setattr(DocumentIngestService, "build_chunks",
                        staticmethod(lambda *a, **k: [{"page": 1, "modality": "text", "content": "hi", "meta": {}}]))
    monkeypatch.setattr(svc, "embed_texts", lambda t: [[0.1, 0.2] for _ in t])
    db = _db()
    DocumentIngestService._run(db, "d1")
    assert _statuses(db) == ["PROCESSING", "DONE"]
    sql = " ".join(str(c.args[0]) for c in db.execute.call_args_list)
    assert "SET status = 'DELETED'" in sql and "DELETE FROM" not in sql


def test_ingest_failure_sets_failed(monkeypatch, tmp_path):
    monkeypatch.setattr(svc, "get_storage", lambda: LocalStorage(tmp_path))
    db = _db()  # file missing
    DocumentIngestService._run(db, "d1")
    assert _statuses(db) == ["PROCESSING", "FAILED"]
    assert "Stored file missing" in db.execute.call_args_list[-1].args[1]["e"]
    db.rollback.assert_called_once()


def test_unsupported_type():
    with pytest.raises(ValueError):
        DocumentIngestService.build_chunks("doc", b"", "d")
