# File Name: test_rag_context_service.py
# Description: Unit tests for RagContextService formatting and generator failure behavior.
# Created At: 2026-11-11
# Created By: AI Agent
# Updated At: 2026-11-11
# Updated By: AI Agent

import pytest

from app.modules.exercise.services.ai_generator_service import AiExerciseGeneratorService
from app.modules.exercise.services.rag_context_service import RagContextService
from app.modules.exercise.services.rag_retrieval_service import RagChunk


def _c(source, ref, content, score=0.5, page=1):
    return RagChunk(source=source, ref=ref, page=page, modality="text", content=content, image_path=None, score=score)


def test_format_orders_sgk_first_and_dedupes():
    out = RagContextService.format_context([
        _c("teacher", "Bai tap", "gv", 0.9),
        _c("sgk", "Hoa hoc 12", "sgk low", 0.1),
        _c("sgk", "Hoa hoc 12", "sgk low", 0.1),
    ])
    assert out.startswith("[SGK Hoa hoc 12 tr.1]")
    assert out.count("sgk low") == 1
    assert "[GV Bai tap tr.1]" in out


def test_generator_raises_without_key(monkeypatch):
    monkeypatch.setattr(
        "app.modules.exercise.services.ai_generator_service.GeminiVisionParserService.get_api_key", lambda: None
    )
    with pytest.raises(RuntimeError):
        AiExerciseGeneratorService.generate_questions("Hoa", "Lop 12", "este", 1, 1, 1)


def test_sources_only_for_included_chunks_and_deduped(monkeypatch):
    monkeypatch.setattr("app.modules.exercise.services.rag_context_service.MAX_CONTEXT_CHARS", 60)
    sgk = RagChunk(source="sgk", ref="Hoa hoc 12, p.14", page=14, modality="image", content="a" * 30,
                   image_path="/sgk-images/d1/p14_f1.png", score=0.9, title="Hoa hoc 12")
    dup = RagChunk(source="sgk", ref="Hoa hoc 12, p.14", page=14, modality="image", content="a" * 30,
                   image_path="/sgk-images/d1/p14_f1.png", score=0.8, title="Hoa hoc 12")
    cut = RagChunk(source="teacher", ref="Doc", page=None, modality="text", content="b" * 200,
                   image_path=None, score=0.1, title="Doc", document_id="doc-1")
    ctx, sources = RagContextService.format_with_sources([sgk, dup, cut])
    assert sources == [{"source": "sgk", "label": "Hoa hoc 12, tr.14", "page": 14, "modality": "image",
                        "image_url": "/sgk-images/d1/p14_f1.png", "document_id": None}]
    assert "b" * 10 not in ctx
