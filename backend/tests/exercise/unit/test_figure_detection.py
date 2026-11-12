# File Name: test_figure_detection.py
# Description: Unit tests for VLM figure detection parsing and its reconciliation with PDF layout blocks (VLM mocked).
# Created At: 2026-11-10
# Created By: AI Agent
# Updated At: 2026-11-10
# Updated By: AI Agent

from _font import FONT
import pymupdf

from app.modules.exercise.schemas import QuestionTypeEnum
from app.modules.exercise.services import figure_detection_service as fds
from app.modules.exercise.services.import_parser_service import ImportParserService, ParsedQuestion
from app.modules.exercise.services.question_image_service import QuestionImageService

PW, PH = 600.0, 800.0


def _norm(x0, y0, x1, y1):
    return [x0 / PW * 1000, y0 / PH * 1000, x1 / PW * 1000, y1 / PH * 1000]


def _q(n=1):
    return ParsedQuestion(question_number=n, part="Part1", question_type=list(QuestionTypeEnum)[0],
                          difficulty=None, content=f"Cau {n}")


def _setup(monkeypatch, vlm):
    saved = []

    def fake_save(data, ext="png", original_name="image", content_type=None):
        saved.append(pymupdf.Pixmap(data))
        return {"url": f"/img/{len(saved)}", "name": original_name}

    monkeypatch.setattr(QuestionImageService, "save_image_bytes", staticmethod(fake_save))
    monkeypatch.setattr(fds, "detect_pdf_figures", lambda fb: vlm)
    return saved


def _plot_pdf() -> bytes:
    doc = pymupdf.open()
    pg = doc.new_page(width=PW, height=PH)
    pg.insert_font(fontname="f", fontfile=FONT)
    pg.insert_text((60, 80), "Câu 1: Cho đồ thị.", fontname="f", fontsize=11)
    pg.draw_rect(pymupdf.Rect(200, 120, 400, 250), width=1)
    pg.draw_line((300, 120), (300, 250), width=1)
    pg.insert_text((60, 500), "Câu 2: Nội dung.", fontname="f", fontsize=11)
    return doc.tobytes()


def test_parse_tolerance():
    txt = '```json\n{"figures": [{"bbox": [10, 20, 300, 400], "caption": "c", "kind": "graph"}, {"bbox": [1]}, {"bbox": [5,5,6,6]}, 3]}\n```'
    out = fds.parse_figures(txt)
    assert len(out) == 1 and out[0]["bbox"] == [10.0, 20.0, 300.0, 400.0]
    assert fds.parse_figures('noise [{"bbox": [300, 400, 10, 20]}] tail')[0]["bbox"] == [10.0, 20.0, 300.0, 400.0]
    assert fds.parse_figures("garbage") == [] and fds.parse_figures("") == []


def test_union_grows_layout_box(monkeypatch):
    data = _plot_pdf()
    saved = _setup(monkeypatch, {})
    q = _q()
    ImportParserService.attach_question_images(data, [q, _q(2)])
    base_w = saved[0].width
    # VLM box reaches 60pt further right than the layout block (a far-away axis title).
    saved.clear()
    monkeypatch.setattr(fds, "detect_pdf_figures", lambda fb: {1: [{"bbox": _norm(200, 120, 470, 250), "caption": "", "kind": "graph"}]})
    q = _q()
    ImportParserService.attach_question_images(data, [q, _q(2)])
    assert q.image_url and saved[0].width > base_w + 40


def test_vlm_only_figure_without_text_layer(monkeypatch):
    doc = pymupdf.open()
    doc.new_page(width=PW, height=PH)
    saved = _setup(monkeypatch, {1: [{"bbox": _norm(100, 100, 400, 300), "caption": "", "kind": "diagram"}]})
    q = _q()
    q.image_page, q.image_bbox = 1, _norm(110, 110, 390, 290)
    ImportParserService.attach_question_images(doc.tobytes(), [q])
    assert q.image_url
    # 300x200pt box padded 3% each side, 250 dpi.
    assert abs(saved[0].width - 318 * 250 / 72) < 25


def test_vlm_failure_keeps_layout(monkeypatch):
    data = _plot_pdf()
    saved = _setup(monkeypatch, {})
    ImportParserService.attach_question_images(data, [_q(), _q(2)])
    ref = (saved[0].width, saved[0].height)
    monkeypatch.setattr(fds, "_ask", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    assert fds.detect_page_figures(b"x") == []
    monkeypatch.setattr(fds, "detect_page_figures", lambda png: [])
    monkeypatch.setattr(fds, "enabled", lambda: True)
    monkeypatch.setattr(fds, "detect_pdf_figures", fds.detect_pdf_figures.__wrapped__ if hasattr(fds.detect_pdf_figures, "__wrapped__") else lambda fb: {1: []})
    saved.clear()
    ImportParserService.attach_question_images(data, [_q(), _q(2)])
    assert (saved[0].width, saved[0].height) == ref


def test_metadata_merge_keeps_solver_keys(monkeypatch):
    data = _plot_pdf()
    _setup(monkeypatch, {})
    q = _q()
    q.image_metadata = {"solved_by": "ai", "ai_confidence": 0.9, "review_reason": "low"}
    ImportParserService.attach_question_images(data, [q, _q(2)])
    assert q.image_url and q.image_metadata["solved_by"] == "ai" and q.image_metadata["url"] == q.image_url
    assert q.image_metadata["review_reason"] == "low"
