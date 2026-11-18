# File Name: test_vision_provider_order.py
# Description: OCR provider selection: Mistral only by default, Gemini is opt-in with Mistral fallback.
# Created At: 2026-11-18
# Created By: AI Agent
# Updated At: 2026-11-18
# Updated By: AI Agent

from app.modules.exercise.services.import_parser_service import ImportParserService as P


def _names(monkeypatch, provider, avail=True):
    from app.modules.exercise.services.gemini_vision_parser_service import GeminiVisionParserService as G
    from app.modules.exercise.services.mistral_vision_parser_service import MistralVisionParserService as M
    monkeypatch.setattr(G, "is_available", classmethod(lambda cls: avail))
    monkeypatch.setattr(M, "is_available", classmethod(lambda cls: avail))
    if provider is None:
        monkeypatch.delenv("SCAN_AI_PROVIDER", raising=False)
    else:
        monkeypatch.setenv("SCAN_AI_PROVIDER", provider)
    return [n for n, _ in P.get_ai_vision_providers()]


def test_default_is_mistral_only(monkeypatch):
    assert _names(monkeypatch, None) == ["Mistral"]
    assert _names(monkeypatch, "mistral") == ["Mistral"]


def test_gemini_is_opt_in_with_mistral_fallback(monkeypatch):
    assert _names(monkeypatch, "gemini") == ["Google Gemini", "Mistral"]


def test_ocr_prompt_skips_non_question_content():
    from app.modules.exercise.services.mistral_vision_parser_service import MISTRAL_PROMPT_ADDENDUM as A
    assert "BỎ QUA" in A and "\"questions\": []" in A
