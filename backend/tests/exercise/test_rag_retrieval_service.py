"""
File Name: test_rag_retrieval_service.py
Description: Unit tests for RAG retrieval helpers (mapping, RRF, query builder) with mocked DB and embedding.
Created At: 2026-11-11
Created By: AI Agent
Updated At: 2026-11-11
Updated By: AI Agent
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.modules.exercise.services import rag_retrieval_service as rag
from app.modules.exercise.services.rag_retrieval_service import RagRetrievalService as Svc


@pytest.mark.parametrize("name,key", [
    ("Toán học", "toan"), ("Vật lý", "vat_li"), ("Vật lí 12", "vat_li"),
    ("Hóa học", "hoa_hoc"), ("Sinh học", "sinh_hoc"), ("Lịch sử", "lich_su"),
    ("Địa lý", "dia_li"), ("Địa lí 10", "dia_li"),
    ("Ngữ văn 10, tập hai", "ngu_van"),
    ("Tiếng Anh 12 - Global Success", "tieng_anh"),
    ("Tin học 11 - Định hướng khoa học máy tính", "tin_hoc"),
    ("Công nghệ 10 - Thiết kế và công nghệ", "cong_nghe"),
    ("Giáo dục Kinh tế và Pháp luật 10", "gdktpl"),
    ("Âm nhạc", None), (None, None),
])
def test_subject_key(name, key):
    assert rag.subject_key_from_text(name) == key


@pytest.mark.parametrize("g,n", [("12", 12), ("Lớp 11", 11), ("Khối 10", 10), (12, 12), ("9", None), (None, None)])
def test_parse_grade(g, n):
    assert rag.parse_grade(g) == n


def test_rrf_fuse_prefers_items_in_both_lists():
    fused = rag.rrf_fuse([["a", "b", "c"], ["c", "a", "d"]])
    assert [k for k, _ in fused][:2] == ["a", "c"]
    assert fused[0][1] == pytest.approx(1 / 61 + 1 / 62)


def test_fts_query_and_vector_literal():
    assert rag.build_fts_query("om, Om!") == "om"
    assert rag.build_fts_query("dinh luat om") == "dinh | luat | om"
    assert rag.build_fts_query("!!!") == ""
    assert rag.vector_literal([1, 0.5]) == "[1.0,0.5]"


def test_sql_filters_inside_query():
    dense, fts = rag.build_search_sql("sgk")
    assert "doc_id = ANY(:doc_ids)" in dense and "doc_id = ANY(:doc_ids)" in fts
    dense, _ = rag.build_search_sql("teacher", scope=True, filter_docs=True)
    for frag in ("c.status = 'ACTIVE'", "d.status = 'Uploaded'", ":teacher_ids", ":subject_id", ":document_ids"):
        assert frag in dense
    dense, _ = rag.build_search_sql("teacher")
    assert ":teacher_ids" not in dense


def _row(cid, page=1):
    return SimpleNamespace(cid=cid, doc="d1", page=page, modality="image", content="c" + cid,
                           meta={"figure_path": "images/d1/p1_f1.png"}, title="Vat li 12")


def test_search_sgk_hybrid(monkeypatch):
    monkeypatch.setattr(rag, "_embed", lambda q: [0.1, 0.2])
    monkeypatch.setattr(Svc, "resolve_sgk_filter", staticmethod(lambda *a: ["d1"]))
    db = MagicMock()
    db.execute.return_value.fetchall.side_effect = [[_row("a"), _row("b")], [_row("b")]]
    out = Svc.search_sgk(db, "dinh luat om", "Vật lý", "12", k=2)
    assert [c.content for c in out] == ["cb", "ca"]
    assert out[0].source == "sgk" and out[0].image_path == "/sgk-images/d1/p1_f1.png"


def test_embed_failure_degrades_to_fts(monkeypatch):
    monkeypatch.setattr(rag, "_embed", lambda q: None)
    monkeypatch.setattr(Svc, "resolve_sgk_filter", staticmethod(lambda *a: ["d1"]))
    db = MagicMock()
    db.execute.return_value.fetchall.return_value = [_row("a")]
    assert len(Svc.search_sgk(db, "om", "Vật lý", "12")) == 1
    assert db.execute.call_count == 1


def test_empty_scopes_short_circuit():
    db = MagicMock()
    assert Svc.search_documents(db, "q", teacher_subject_scope=("sid", [])) == []
    assert Svc.search_documents(db, "q", document_ids=[]) == []
    db.execute.assert_not_called()


def test_expand_query_fallback_and_parse(monkeypatch):
    monkeypatch.setattr(rag, "_llm_text", lambda p: '["a", "b", "c", "d"]')
    assert Svc.expand_query("x") == ["a", "b", "c"]

    def boom(p):
        raise RuntimeError("x")

    monkeypatch.setattr(rag, "_llm_text", boom)
    assert Svc.expand_query("x") == ["x"]


def test_to_image_url():
    from app.modules.exercise.services.rag_retrieval_service import to_image_url
    assert to_image_url("images/d1/p1_f1.png") == "/sgk-images/d1/p1_f1.png"
    assert to_image_url(None) is None
