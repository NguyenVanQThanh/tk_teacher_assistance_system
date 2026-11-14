# File Name: test_pdf_export.py
# Description: Tests for question image embedding and GFM markdown table rendering in the
#              exercise PDF export (PdfExportService.generate_exercise_pdf).
# Created At: 2026-11-13
# Created By: AI Agent

import io
import uuid
from pathlib import Path
from types import SimpleNamespace

import httpx
import pymupdf
from PIL import Image

from app.modules.exercise.services import pdf_export_service
from app.modules.exercise.services.pdf_export_service import PdfExportService


# --------------------------------------------------------------------------- helpers

def _png_bytes(size=(160, 90), color=(180, 40, 40)):
    """Raw PNG bytes for a solid-colour image."""
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format="PNG")
    return buffer.getvalue()


def _write_png(path, size=(160, 90)):
    path.write_bytes(_png_bytes(size=size))
    return path


def _patch_image_reader(monkeypatch, tmp_path):
    """Make the PDF exporter read question images from a temporary directory."""
    def read_bytes(url):
        return (tmp_path / Path(url).name).read_bytes()

    monkeypatch.setattr(pdf_export_service, "read_bytes_from_url", read_bytes)


def _option(order, content, is_correct=False):
    return SimpleNamespace(display_order=order, content=content, is_correct=is_correct)


def _question(order, content, *, image_url=None, options=(), question_type="MultipleChoice",
              content_markdown=None, content_latex=None, correct_answer=None, difficulty=None):
    return SimpleNamespace(
        display_order=order,
        question_type=question_type,
        difficulty=difficulty,
        content=content,
        content_markdown=content_markdown,
        content_latex=content_latex,
        correct_answer=correct_answer,
        image_url=image_url,
        image_metadata=None,
        status="ACTIVE",
        created_at=None,
        answer_options=[_option(index, text, correct)
                        for index, (text, correct) in enumerate(options, 1)],
    )


def _exercise(questions, title="Đề kiểm tra thử", ai_metadata=None):
    return SimpleNamespace(
        exercise_id=uuid.uuid4(),
        title=title,
        ai_metadata=ai_metadata or {},
        questions=questions,
    )


def _mc_options():
    return [("Một", True), ("Hai", False), ("Ba", False), ("Bốn", False)]


def _open_pdf(pdf_bytes):
    return pymupdf.open(stream=pdf_bytes, filetype="pdf")


def _pdf_text(doc):
    return "\n".join(page.get_text() for page in doc)


# --------------------------------------------------------------------------- tests

def test_pdf_embeds_question_image_and_markdown_table(tmp_path, monkeypatch):
    """A question image and a GFM table both end up in the generated PDF."""
    _write_png(tmp_path / "figure.png")
    _patch_image_reader(monkeypatch, tmp_path)

    content = (
        "Cho bảng số liệu sau:\n"
        "| Chỉ tiêu | Giá trị |\n"
        "| --- | --- |\n"
        "| A | 1 |\n"
        "| B | 2 |\n"
        "Chọn khẳng định đúng."
    )
    question = _question(1, content, image_url="/uploads/questions/figure.png",
                         options=_mc_options())
    pdf_bytes = PdfExportService.generate_exercise_pdf(_exercise([question]))
    assert pdf_bytes.startswith(b"%PDF-")

    doc = _open_pdf(pdf_bytes)
    try:
        assert len(doc) >= 1
        text = _pdf_text(doc)
        for expected in ("Chỉ tiêu", "Giá trị", "A", "1"):
            assert expected in text
        # The table is rendered as a flowable, never as raw markdown text.
        assert "| --- |" not in text
        assert any(page.get_images(full=True) for page in doc)
    finally:
        doc.close()


def test_large_question_image_is_scaled(tmp_path, monkeypatch):
    """Oversized images are scaled proportionally to max 480x300pt."""
    _write_png(tmp_path / "big.png", size=(2000, 1500))
    _patch_image_reader(monkeypatch, tmp_path)

    question = _question(1, "Hình minh họa kèm theo.", image_url="/uploads/questions/big.png",
                         options=_mc_options())
    pdf_bytes = PdfExportService.generate_exercise_pdf(_exercise([question]))

    doc = _open_pdf(pdf_bytes)
    try:
        images = [info for page in doc for info in page.get_image_info()]
        assert images
        bbox = pymupdf.Rect(images[0]["bbox"])
        assert bbox.width <= pdf_export_service.MAX_IMAGE_WIDTH + 1
        assert bbox.height <= pdf_export_service.MAX_IMAGE_HEIGHT + 1
        # Aspect ratio 4:3 is preserved.
        assert abs(bbox.width / bbox.height - 2000 / 1500) < 0.05
    finally:
        doc.close()


def test_missing_question_image_does_not_break_pdf(tmp_path, monkeypatch):
    """A missing local image adds a warning line but the PDF is still produced."""
    _patch_image_reader(monkeypatch, tmp_path)

    question = _question(1, "Nội dung câu hỏi không có ảnh.",
                         image_url="/uploads/questions/does_not_exist.png",
                         options=_mc_options())
    pdf_bytes = PdfExportService.generate_exercise_pdf(_exercise([question]))
    assert pdf_bytes.startswith(b"%PDF-")

    doc = _open_pdf(pdf_bytes)
    try:
        text = _pdf_text(doc)
        assert "Nội dung câu hỏi không có ảnh." in text
        assert "Không tải được hình ảnh" in text
    finally:
        doc.close()


def test_invalid_markdown_table_renders_as_text(tmp_path, monkeypatch):
    """A pipe block without a valid separator is rendered as plain text, not a table."""
    _patch_image_reader(monkeypatch, tmp_path)

    content = (
        "| Chỉ tiêu | Giá trị |\n"
        "| - | - |\n"
        "| A | 1 |"
    )
    question = _question(1, content, options=_mc_options())
    pdf_bytes = PdfExportService.generate_exercise_pdf(_exercise([question]))
    assert pdf_bytes.startswith(b"%PDF-")

    doc = _open_pdf(pdf_bytes)
    try:
        text = _pdf_text(doc)
        assert "Chỉ tiêu" in text
        assert "Giá trị" in text
    finally:
        doc.close()


def test_local_image_never_hits_the_network(tmp_path, monkeypatch):
    """Local /uploads/questions images are read from disk without any HTTP call."""
    _write_png(tmp_path / "local.png")
    _patch_image_reader(monkeypatch, tmp_path)

    def exploding_get(*args, **kwargs):
        raise AssertionError("httpx.get must not be called for local images")

    monkeypatch.setattr(pdf_export_service.httpx, "get", exploding_get)

    question = _question(1, "Câu hỏi có ảnh lưu nội bộ.",
                         image_url="/uploads/questions/local.png", options=_mc_options())
    pdf_bytes = PdfExportService.generate_exercise_pdf(_exercise([question]))
    assert pdf_bytes.startswith(b"%PDF-")

    doc = _open_pdf(pdf_bytes)
    try:
        assert any(page.get_images(full=True) for page in doc)
    finally:
        doc.close()


def test_absolute_image_url_is_downloaded_once(tmp_path, monkeypatch):
    """Absolute URLs go through httpx (mocked here) and are cached per generation."""
    png = _png_bytes(size=(120, 80))
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        return httpx.Response(
            200,
            content=png,
            headers={"content-length": str(len(png))},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(pdf_export_service.httpx, "get", fake_get)
    url = "https://example.test/figure.png"

    questions = [
        _question(1, "Câu thứ nhất có ảnh từ xa.", image_url=url, options=_mc_options()),
        _question(2, "Câu thứ hai dùng lại cùng ảnh.", image_url=url, options=_mc_options()),
    ]
    pdf_bytes = PdfExportService.generate_exercise_pdf(_exercise(questions))
    assert pdf_bytes.startswith(b"%PDF-")
    assert calls == [url]  # cached for the whole generation

    doc = _open_pdf(pdf_bytes)
    try:
        assert any(page.get_images(full=True) for page in doc)
    finally:
        doc.close()


def test_absolute_image_url_failure_adds_warning(tmp_path, monkeypatch):
    """A failing download is swallowed and reported as a warning line."""
    def failing_get(url, **kwargs):
        raise httpx.ConnectError("boom", request=httpx.Request("GET", url))

    monkeypatch.setattr(pdf_export_service.httpx, "get", failing_get)

    question = _question(1, "Câu hỏi có ảnh lỗi.",
                         image_url="https://example.test/missing.png",
                         options=_mc_options())
    pdf_bytes = PdfExportService.generate_exercise_pdf(_exercise([question]))
    assert pdf_bytes.startswith(b"%PDF-")

    doc = _open_pdf(pdf_bytes)
    try:
        assert "Không tải được hình ảnh" in _pdf_text(doc)
    finally:
        doc.close()


def test_table_in_content_markdown_is_rendered(tmp_path, monkeypatch):
    """Tables carried by content_markdown are parsed when content itself has none."""
    _patch_image_reader(monkeypatch, tmp_path)

    question = _question(
        1,
        "Cho bảng thống kê:",
        content_markdown=(
            "Cho bảng thống kê:\n"
            "| Hạng | Điểm |\n"
            "| --- | --- |\n"
            "| Nhất | 9 |"
        ),
        options=_mc_options(),
    )
    pdf_bytes = PdfExportService.generate_exercise_pdf(_exercise([question]))

    doc = _open_pdf(pdf_bytes)
    try:
        text = _pdf_text(doc)
        assert "Hạng" in text
        assert "Nhất" in text
    finally:
        doc.close()


def test_latex_and_table_coexist(tmp_path, monkeypatch):
    """Inline LaTeX still renders (as images) alongside a markdown table."""
    _patch_image_reader(monkeypatch, tmp_path)

    content = (
        "Cho hàm số $y = x^2$.\n"
        "| x | y |\n"
        "| --- | --- |\n"
        "| 1 | 2 |"
    )
    question = _question(1, content, options=_mc_options())
    pdf_bytes = PdfExportService.generate_exercise_pdf(_exercise([question]))
    assert pdf_bytes.startswith(b"%PDF-")

    doc = _open_pdf(pdf_bytes)
    try:
        text = _pdf_text(doc)
        assert "x" in text and "y" in text
        # The inline formula is rendered as an image, not as raw "$y = x^2$" text.
        assert "$y = x^2$" not in text
        assert any(page.get_images(full=True) for page in doc)
    finally:
        doc.close()


def test_exercise_title_and_duration_are_used(tmp_path, monkeypatch):
    """The exercise title and ai_metadata duration replace the hardcoded header."""
    _patch_image_reader(monkeypatch, tmp_path)

    question = _question(1, "Câu hỏi kiểm tra tiêu đề.", options=_mc_options())
    exercise = _exercise([question], title="Đề kiểm tra giữa kỳ", ai_metadata={"duration_minutes": 45})
    pdf_bytes = PdfExportService.generate_exercise_pdf(exercise)

    doc = _open_pdf(pdf_bytes)
    try:
        text = _pdf_text(doc)
        assert "Đề kiểm tra giữa kỳ" in text
        assert "Thời gian làm bài: 45 phút" in text
        assert "ĐÁP ÁN" in text  # answer key still present
    finally:
        doc.close()


def test_table_segment_is_rendered_when_content_has_none(tmp_path, monkeypatch):
    """A table stripped from the stem into q.segments is still rendered."""
    _patch_image_reader(monkeypatch, tmp_path)

    question = _question(1, "Cho bảng số liệu:", options=_mc_options())
    question.segments = [
        {"type": "text", "content": "Cho bảng số liệu:"},
        {"type": "table", "content": "| Tháng | Doanh thu |\n| --- | --- |\n| Một | 10 |"},
    ]
    pdf_bytes = PdfExportService.generate_exercise_pdf(_exercise([question]))

    doc = _open_pdf(pdf_bytes)
    try:
        text = _pdf_text(doc)
        assert "Tháng" in text
        assert "Doanh thu" in text
        assert "Một" in text
    finally:
        doc.close()


def test_table_is_not_duplicated_when_content_and_segments_both_have_it(tmp_path, monkeypatch):
    """The segment table is skipped when the stem already renders the same table."""
    _patch_image_reader(monkeypatch, tmp_path)

    table = "| Chỉ tiêu | Giá trị |\n| --- | --- |\n| A | 1 |"
    question = _question(1, f"Cho bảng:\n{table}", options=_mc_options())
    question.segments = [{"type": "table", "content": table}]
    pdf_bytes = PdfExportService.generate_exercise_pdf(_exercise([question]))

    doc = _open_pdf(pdf_bytes)
    try:
        text = _pdf_text(doc)
        assert text.count("Chỉ tiêu") == 1
    finally:
        doc.close()
