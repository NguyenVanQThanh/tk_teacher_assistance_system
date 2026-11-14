# File Name: pdf_export_service.py
# Description: Service for generating formatted PDF documents from exercise data including LaTeX math rendering.
# Created At: 2026-08-12
# Created By: Tam Khang
# Updated At: 2026-11-13
# Updated By: AI Agent

import io
import os
import re
import tempfile
from typing import List, Tuple, Dict, Any, Optional
import httpx
from PIL import Image as PILImage
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['mathtext.fontset'] = 'cm'  # Computer Modern LaTeX math fontset
matplotlib.rcParams['font.family'] = 'serif'
matplotlib.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
# Object-oriented Agg API: no global pyplot state, so PDF export stays safe in FastAPI's threadpool.
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from models.models import Exercise, Question, AnswerOption
from app.modules.exercise.schemas import QuestionTypeEnum
from app.core.storage import read_bytes_from_url


# ---------------------------------------------------------------------------
# Question image embedding (max size kept in PDF points, download hard cap in bytes).
# ---------------------------------------------------------------------------
MAX_IMAGE_WIDTH = 480.0
MAX_IMAGE_HEIGHT = 300.0
MAX_IMAGE_BYTES = 10 * 1024 * 1024
IMAGE_FETCH_TIMEOUT_SECONDS = 5.0
IMAGE_LOAD_FAILED_TEXT = "[Không tải được hình ảnh]"

# ---------------------------------------------------------------------------
# Markdown (GFM) pipe table layout.
# ---------------------------------------------------------------------------
TABLE_TOTAL_WIDTH = 520.0
TABLE_MIN_COL_WIDTH = 42.0
TABLE_MAX_COL_WIDTH = 260.0
TABLE_LARGE_ROW_THRESHOLD = 8

_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def _render_latex_png(latex: str, fontsize: float, pad_inches: float, dpi: int) -> io.BytesIO:
    """Render one LaTeX formula to PNG bytes via the object-oriented Agg API.

    A fresh ``Figure`` per call (instead of ``pyplot``) keeps no global state, so concurrent
    PDF exports in FastAPI's thread pool do not race on the pyplot figure manager.
    """
    fig = Figure(figsize=(0.01, 0.01))
    FigureCanvasAgg(fig)
    fig.text(0, 0, f"${latex}$", fontsize=fontsize)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=pad_inches,
                transparent=True, dpi=dpi)
    buf.seek(0)
    return buf


class PdfExportService:
    """Service to export exercise data from database to formatted PDF document."""

    _font_registered = False

    @classmethod
    def register_fonts(cls):
        """Register Vietnamese UTF-8 compatible Times New Roman TrueType fonts for ReportLab."""
        if cls._font_registered:
            return

        font_paths = [
            ("VietnameseFont", "C:/Windows/Fonts/times.ttf"),
            ("VietnameseFont-Bold", "C:/Windows/Fonts/timesbd.ttf"),
            ("VietnameseFont-Italic", "C:/Windows/Fonts/timesi.ttf"),
            ("VietnameseFont-BoldItalic", "C:/Windows/Fonts/timesbi.ttf"),
            ("VietnameseFont", "C:/Windows/Fonts/arial.ttf"),
            ("VietnameseFont-Bold", "C:/Windows/Fonts/arialbd.ttf"),
            ("VietnameseFont-Italic", "C:/Windows/Fonts/ariali.ttf"),
            ("VietnameseFont-BoldItalic", "C:/Windows/Fonts/arialbi.ttf"),
            ("VietnameseFont", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
            ("VietnameseFont-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"),
            ("VietnameseFont-Italic", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"),
            ("VietnameseFont-BoldItalic", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf"),
        ]

        # Add bundled matplotlib fonts as cross-platform fallbacks
        try:
            mpl_font_dir = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
            font_paths.extend([
                ("VietnameseFont", os.path.join(mpl_font_dir, "DejaVuSerif.ttf")),
                ("VietnameseFont-Bold", os.path.join(mpl_font_dir, "DejaVuSerif-Bold.ttf")),
                ("VietnameseFont-Italic", os.path.join(mpl_font_dir, "DejaVuSerif-Italic.ttf")),
                ("VietnameseFont-BoldItalic", os.path.join(mpl_font_dir, "DejaVuSerif-BoldItalic.ttf")),
            ])
        except Exception:
            pass

        regular_registered = False
        bold_registered = False

        for font_name, path in font_paths:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, path))
                    if font_name == "VietnameseFont" and not regular_registered:
                        regular_registered = True
                    elif font_name == "VietnameseFont-Bold" and not bold_registered:
                        bold_registered = True
                except Exception as e:
                    print(f"Warning: Could not register font {font_name} from {path}: {e}")

        if not regular_registered:
            try:
                pdfmetrics.registerFont(TTFont("VietnameseFont", "Vera.ttf"))
            except Exception:
                pass
        if not bold_registered:
            try:
                pdfmetrics.registerFont(TTFont("VietnameseFont-Bold", "VeraBd.ttf"))
            except Exception:
                pass

        # Map the family so <b>/<i> markup inside Paragraphs resolves to the Vietnamese
        # fonts instead of falling back to Helvetica (important on Linux/Docker where
        # C:/Windows/Fonts does not exist).
        registered = set(pdfmetrics.getRegisteredFontNames())
        if "VietnameseFont" in registered:
            normal = "VietnameseFont"
            bold = "VietnameseFont-Bold" if "VietnameseFont-Bold" in registered else normal
            italic = "VietnameseFont-Italic" if "VietnameseFont-Italic" in registered else normal
            bold_italic = ("VietnameseFont-BoldItalic"
                           if "VietnameseFont-BoldItalic" in registered else bold)
            try:
                pdfmetrics.registerFontFamily(
                    "VietnameseFont",
                    normal=normal,
                    bold=bold,
                    italic=italic,
                    boldItalic=bold_italic,
                )
            except Exception as e:
                print(f"Warning: Could not register VietnameseFont family: {e}")

        cls._font_registered = True

    @staticmethod
    def render_latex_to_image(latex_str: str, fontsize: int = 12) -> Optional[io.BytesIO]:
        """Convert a LaTeX formula string into a PNG image BytesIO stream using Matplotlib."""
        try:
            clean_latex = latex_str.strip("$").strip()
            if not clean_latex:
                return None
            return _render_latex_png(clean_latex, fontsize, 0.03, 200)
        except Exception as e:
            print(f"Warning: Failed to render LaTeX '{latex_str}': {e}")
            return None

    @classmethod
    def _normalize_math_in_text(cls, text: str) -> str:
        """
        Normalizes vector symbols, exponents, radical/fraction expressions, and unwrapped LaTeX math formulas.
        Converts them into standard LaTeX $ ... $ syntax for Matplotlib rendering.
        """
        if not text:
            return ""

        clean_text = re.sub(r"[\uFFFD\u25A0\u25A1]", "", text)
        clean_text = clean_text.replace(r"\mathbb{R}", r"\mathbf{R}")
        clean_text = re.sub(r'\\R(?![a-zA-Z])', r'\\mathbf{R}', clean_text)
        clean_text = re.sub(r'\\ge(?![a-zA-Z])', r'\\geq', clean_text)
        clean_text = re.sub(r'\\le(?![a-zA-Z])', r'\\leq', clean_text)

        # Vector arrow conversions: a\u20d7, a\u2192, a⃗ -> $\vec{a}$
        clean_text = re.sub(r'([a-zA-Z])[\u20d7\u2192⃗]', r'$\\vec{\1}$', clean_text)

        sup_map = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")

        parts = re.split(r'(\$\$.*?\$\$|\$.*?\$)', clean_text)
        new_parts = []

        for part in parts:
            if not part:
                continue
            if (part.startswith("$$") and part.endswith("$$")) or (part.startswith("$") and part.endswith("$")):
                # Ensure blackboard bold R is compatible
                p = part.replace(r"\mathbb{R}", r"\mathbf{R}")
                p = re.sub(r'\\R(?![a-zA-Z])', r'\\mathbf{R}', p)
                new_parts.append(p)
            else:
                p = part
                # Unwrapped vector commands: \vec{a} or \vec a -> $\vec{a}$
                p = re.sub(r'\\vec\{([^}]+)\}', r'$\\vec{\1}$', p)
                p = re.sub(r'\\vec\s+([a-zA-Z])', r'$\\vec{\1}$', p)

                # Unicode superscripts: x² -> $x^2$, t³ -> $t^3$
                def replace_unicode_sup(match):
                    var = match.group(1)
                    num = match.group(2).translate(sup_map)
                    return f"${var}^{{{num}}}$"
                p = re.sub(r'([a-zA-Z])([⁰¹²³⁴⁵⁶⁷⁸⁹]+)', replace_unicode_sup, p)

                # Plain text variable exponent patterns like t3, t2, 6t2, x2 (e.g. s(t) = t3-6t2+9t)
                def replace_var_exp(match):
                    prefix = match.group(1) or ""
                    var = match.group(2)
                    exp = match.group(3)
                    return f"${prefix}{var}^{{{exp}}}$"

                p = re.sub(r'(\d*)([a-zA-Z])([2-9])(?![0-9a-zA-Z])', replace_var_exp, p)

                # Unwrapped LaTeX math functions: \sqrt{...}, \frac{...}{...}
                p = re.sub(r'(\\sqrt(?:\[.*?\])?\{.*?\})', r'$\1$', p)
                p = re.sub(r'(\\frac\{.*?\}\{.*?\})', r'$\1$', p)

                new_parts.append(p)

        result = "".join(new_parts)
        result = result.replace('\u20d7', '')
        return result

    @classmethod
    def render_latex_to_inline_tag(cls, latex_str: str, temp_files_list: List[str], fontsize: int = 11) -> Optional[str]:
        """Convert a LaTeX formula string into a temporary PNG image file and return a ReportLab inline <img> tag."""
        try:
            clean_latex = latex_str.strip("$").strip()
            if not clean_latex:
                return None

            clean_latex = clean_latex.replace(r"\mathbb{R}", r"\mathbf{R}")
            clean_latex = re.sub(r'\\R(?![a-zA-Z])', r'\\mathbf{R}', clean_latex)
            clean_latex = re.sub(r'\\ge(?![a-zA-Z])', r'\\geq', clean_latex)
            clean_latex = re.sub(r'\\le(?![a-zA-Z])', r'\\leq', clean_latex)

            has_multilevel = bool(re.search(r'\\frac|\\sqrt|\\int|\\sum|\\lim|\\prod', clean_latex))
            render_fontsize = max(13.5, float(fontsize) * 1.25) if has_multilevel else max(12.5, float(fontsize) * 1.15)

            buf = _render_latex_png(clean_latex, render_fontsize, 0.01, 300)

            img = PILImage.open(buf)
            w, h = img.size

            # Convert 300 DPI pixels to PDF points (72 points/inch)
            target_w = (w / 300.0) * 72.0 * 1.05
            target_h = (h / 300.0) * 72.0 * 1.05

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            temp_file.write(buf.getvalue())
            temp_file.close()

            temp_files_list.append(temp_file.name)
            img_path = temp_file.name.replace("\\", "/")
            return f'<img src="{img_path}" width="{target_w:.1f}" height="{target_h:.1f}" valign="middle"/>'
        except Exception as e:
            print(f"Warning: Failed to render LaTeX '{latex_str}': {e}")
            return None

    @classmethod
    def format_content_to_markup(cls, raw_text: str, temp_files_list: List[str], fontsize: int = 11) -> str:
        """
        Parses text, normalizes math formulas, renders LaTeX ($...$ and $$...$$) into temporary images,
        and returns ReportLab Paragraph HTML-compatible markup string with inline <img> tags.
        """
        if not raw_text:
            return ""

        normalized_text = cls._normalize_math_in_text(raw_text)
        parts = re.split(r"(\$\$.*?\$\$|\$.*?\$)", normalized_text)

        markup_parts = []
        for part in parts:
            if not part:
                continue
            if ((part.startswith("$$") and part.endswith("$$")) or (part.startswith("$") and part.endswith("$"))) and len(part) > 2:
                img_tag = cls.render_latex_to_inline_tag(part, temp_files_list, fontsize=fontsize)
                if img_tag:
                    markup_parts.append(img_tag)
                else:
                    clean_p = part.strip("$").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    markup_parts.append(clean_p)
            else:
                escaped = part.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                markup_parts.append(escaped)

        return "".join(markup_parts)

    # ------------------------------------------------------------------ markdown tables

    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape a plain string for use inside a ReportLab Paragraph."""
        return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    @staticmethod
    def _is_table_separator(line: str) -> bool:
        """True for a GFM table separator row such as ``| --- | :---: |``."""
        return bool(_TABLE_SEPARATOR_RE.match(line or ""))

    @staticmethod
    def _split_table_row(line: str) -> List[str]:
        """Split one pipe-table row into trimmed cells (outer pipes are optional)."""
        text = (line or "").strip()
        if text.startswith("|"):
            text = text[1:]
        if text.endswith("|"):
            text = text[:-1]
        return [cell.strip() for cell in text.split("|")]

    @classmethod
    def split_table_blocks(cls, text: str) -> List[Tuple[str, str]]:
        """Split text into ``("text"|"table", value)`` blocks, mirroring tableMarkdown.js.

        A table starts on a line containing ``|`` followed by a separator row and runs
        until the next line without a pipe. Everything else is kept as text.
        """
        lines = str(text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
        blocks: List[Tuple[str, str]] = []
        buffer: List[str] = []

        def flush() -> None:
            if buffer:
                blocks.append(("text", "\n".join(buffer)))
                buffer.clear()

        index = 0
        while index < len(lines):
            line = lines[index]
            if ("|" in line and index + 1 < len(lines)
                    and cls._is_table_separator(lines[index + 1]) and len(line.strip()) > 1):
                end = index + 2
                while end < len(lines) and "|" in lines[end]:
                    end += 1
                flush()
                blocks.append(("table", "\n".join(lines[index:end])))
                index = end
            else:
                buffer.append(line)
                index += 1
        flush()
        return blocks

    @classmethod
    def _parse_markdown_table(cls, markdown: str) -> Optional[Tuple[List[str], List[List[str]]]]:
        """Parse a GFM pipe table into (header cells, body rows); None when invalid."""
        lines = [line.strip() for line in str(markdown or "").splitlines() if line.strip()]
        if len(lines) < 2 or "|" not in lines[0] or len(lines[0]) < 2:
            return None
        if not cls._is_table_separator(lines[1]):
            return None
        header = cls._split_table_row(lines[0])
        width = len(header)
        if width == 0:
            return None

        def normalize(line: str) -> List[str]:
            cells = cls._split_table_row(line)[:width]
            cells.extend([""] * (width - len(cells)))
            return cells

        rows = [normalize(line) for line in lines[2:] if "|" in line]
        return header, rows

    @staticmethod
    def _table_col_widths(header: List[str], rows: List[List[str]]) -> List[float]:
        """Column widths proportional to the longest cell, scaled to ~520pt in total."""
        ncols = max(1, len(header))
        weights: List[float] = []
        for col in range(ncols):
            lengths = [len(header[col]) if col < len(header) else 0]
            lengths.extend(len(row[col]) for row in rows if col < len(row))
            weights.append(max(4.0, min(60.0, float(max(lengths)))))
        total = sum(weights) or 1.0
        min_width = min(TABLE_MIN_COL_WIDTH, TABLE_TOTAL_WIDTH / ncols)
        if ncols == 1:
            max_width = TABLE_TOTAL_WIDTH
        else:
            max_width = max(min_width, min(TABLE_MAX_COL_WIDTH,
                                           TABLE_TOTAL_WIDTH - min_width * (ncols - 1)))
        widths = [min(max_width, max(min_width, TABLE_TOTAL_WIDTH * weight / total))
                  for weight in weights]
        scale = TABLE_TOTAL_WIDTH / sum(widths)
        return [width * scale for width in widths]

    @classmethod
    def _build_markdown_table(cls, markdown: str, temp_files: List[str],
                              base_style: ParagraphStyle) -> Optional[Any]:
        """Render a GFM pipe table as a ReportLab Table; None when the table is invalid.

        Long tables are marked (``_pdf_large_table``) so ``_append_question`` can let them
        split across pages; ``repeatRows=1`` repeats the header row when that happens.
        Small tables are left unwrapped because the surrounding question is already kept
        together (nesting KeepTogether inside KeepTogether would force a page break).
        """
        parsed = cls._parse_markdown_table(markdown)
        if parsed is None:
            return None
        header, rows = parsed

        cell_style = ParagraphStyle(
            'TableText',
            parent=base_style,
            fontName='VietnameseFont',
            fontSize=9.5,
            leading=12.5,
            alignment=0,  # left
            spaceBefore=0,
            spaceAfter=0,
            textColor=colors.HexColor("#1E293B")
        )
        header_style = ParagraphStyle(
            'TableHeader',
            parent=cell_style,
            fontName='VietnameseFont-Bold',
            textColor=colors.HexColor("#0F172A")
        )

        def cell_paragraph(value: str, style: ParagraphStyle) -> Paragraph:
            markup = cls.format_content_to_markup(value, temp_files, fontsize=9.5)
            return Paragraph(markup if markup.strip() else "&nbsp;", style)

        data = [[cell_paragraph(value, header_style) for value in header]]
        for row in rows:
            data.append([cell_paragraph(value, cell_style) for value in row])

        table = Table(data, colWidths=cls._table_col_widths(header, rows), repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        if len(data) > TABLE_LARGE_ROW_THRESHOLD:
            # Marker consumed by _append_question: do not wrap a long table in KeepTogether.
            table._pdf_large_table = True
        return table

    @classmethod
    def _format_text_with_latex(cls, text: str, style: ParagraphStyle,
                                temp_files: List[str]) -> List[Any]:
        """Render plain text, converting inline/block LaTeX into images (existing behavior)."""
        if not isinstance(text, str):
            text = "" if text is None else str(text)
        if "$$" in text:
            chunks = re.split(r'(\$\$[\s\S]*?\$\$)', text)
            elements: List[Any] = []
            for chunk in chunks:
                if not chunk.strip():
                    continue
                if chunk.startswith("$$") and chunk.endswith("$$"):
                    img_tag = cls.render_latex_to_inline_tag(chunk, temp_files, fontsize=13)
                    if img_tag:
                        center_style = ParagraphStyle(
                            'CenterMath', parent=style, alignment=1, spaceBefore=4, spaceAfter=4
                        )
                        elements.append(Paragraph(img_tag, center_style))
                    else:
                        elements.append(Paragraph(cls._escape_html(chunk.strip("$")), style))
                else:
                    markup = cls.format_content_to_markup(chunk, temp_files, fontsize=11)
                    if markup.strip():
                        elements.append(Paragraph(markup, style))
            return elements
        markup = cls.format_content_to_markup(text, temp_files, fontsize=11)
        return [Paragraph(markup, style)] if markup.strip() else []

    @classmethod
    def _format_content_blocks(cls, text: str, style: ParagraphStyle, temp_files: List[str],
                               prefix: str = "") -> List[Any]:
        """Render content split into text and markdown-table blocks.

        ``prefix`` (e.g. "Câu 1. ") is prepended to the first text block so the question
        header keeps flowing inline; when the content starts with a table the prefix gets
        its own paragraph above it.
        """
        if not isinstance(text, str):
            text = "" if text is None else str(text)
        elements: List[Any] = []
        pending = prefix or ""
        for kind, value in cls.split_table_blocks(text):
            if kind == "table":
                table = cls._build_markdown_table(value, temp_files, style)
                if table is not None:
                    if pending:
                        markup = cls.format_content_to_markup(pending, temp_files, fontsize=11)
                        if markup.strip():
                            elements.append(Paragraph(markup, style))
                        pending = ""
                    elements.append(Spacer(1, 4))
                    elements.append(table)
                    elements.append(Spacer(1, 4))
                    continue
            elements.extend(cls._format_text_with_latex(pending + value, style, temp_files))
            pending = ""
        if pending:
            markup = cls.format_content_to_markup(pending, temp_files, fontsize=11)
            if markup.strip():
                elements.append(Paragraph(markup, style))
        return elements

    @classmethod
    def _question_content_text(cls, question: Any) -> str:
        """Stem text for a question: content_latex, else content, else content_markdown.

        Markdown tables are parsed from whichever field carries them: when the LaTeX/plain
        content has no table but ``content_markdown`` does, the markdown version is used.
        """
        content_latex = getattr(question, 'content_latex', None)
        content = getattr(question, 'content', None)
        content_markdown = getattr(question, 'content_markdown', None)
        base = content_latex if isinstance(content_latex, str) and content_latex.strip() else content
        if not isinstance(base, str):
            base = "" if base is None else str(base)
        markdown = content_markdown if isinstance(content_markdown, str) else ""
        if markdown.strip() and not cls._contains_table(base) and cls._contains_table(markdown):
            return markdown
        return base

    @classmethod
    def _contains_table(cls, text: str) -> bool:
        """True when the text contains at least one GFM pipe table."""
        return any(kind == "table" for kind, _ in cls.split_table_blocks(text))

    @staticmethod
    def _append_question(story: List[Any], elements: List[Any]) -> None:
        """Append a question, keeping it together unless it holds a long (splittable) table."""
        if any(getattr(element, '_pdf_large_table', False) for element in elements):
            story.extend(elements)
        else:
            story.append(KeepTogether(elements))

    # ------------------------------------------------------------------ question images

    @staticmethod
    def _is_remote_image_url(image_url: str) -> bool:
        """True for absolute http(s) image URLs."""
        return bool(re.match(r"^https?://", image_url or "", re.IGNORECASE))

    @staticmethod
    def _download_remote_image(image_url: str) -> Optional[bytes]:
        """Download a remote image with a short timeout and a hard size cap (None on failure)."""
        try:
            response = httpx.get(image_url, timeout=IMAGE_FETCH_TIMEOUT_SECONDS, follow_redirects=True)
            response.raise_for_status()
            declared = response.headers.get("content-length")
            if declared is not None:
                try:
                    if int(declared) > MAX_IMAGE_BYTES:
                        print(f"Warning: Question image exceeds {MAX_IMAGE_BYTES} bytes: {image_url}")
                        return None
                except (TypeError, ValueError):
                    pass
            data = response.content
            if not data or len(data) > MAX_IMAGE_BYTES:
                print(f"Warning: Question image is empty or too large: {image_url}")
                return None
            return data
        except Exception as exc:
            print(f"Warning: Could not download question image {image_url}: {exc}")
            return None

    @classmethod
    def _load_image_bytes(cls, image_url: str, cache: Dict[str, Optional[bytes]]) -> Optional[bytes]:
        """Load image bytes for a question image URL, cached by URL for one PDF build."""
        if image_url in cache:
            return cache[image_url]
        data: Optional[bytes] = None
        try:
            data = read_bytes_from_url(image_url)
        except FileNotFoundError:
            # Not in our storage: absolute URLs may still be fetched over HTTP.
            if cls._is_remote_image_url(image_url):
                data = cls._download_remote_image(image_url)
            else:
                print(f"Warning: Question image not found: {image_url}")
        except RuntimeError:
            # Storage misconfiguration (e.g. R2 credentials missing) must be visible.
            raise
        except Exception as exc:
            print(f"Warning: Could not read question image {image_url}: {exc}")
            data = None
        if data is not None and (not data or len(data) > MAX_IMAGE_BYTES):
            print(f"Warning: Question image is empty or too large: {image_url}")
            data = None
        cache[image_url] = data
        return data

    @classmethod
    def _build_image_flowable(cls, data: bytes) -> Optional[RLImage]:
        """Build a proportionally scaled ReportLab image (max 480x300pt) from raw bytes."""
        try:
            with PILImage.open(io.BytesIO(data)) as pil_image:
                width, height = pil_image.size
                image_format = (pil_image.format or "").upper()
                if width <= 0 or height <= 0:
                    return None
                if image_format not in ("PNG", "JPEG", "JPG", "GIF", "BMP"):
                    # ReportLab only reads a few formats directly: normalize through Pillow.
                    converted = io.BytesIO()
                    target = pil_image
                    if target.mode not in ("RGB", "RGBA"):
                        target = target.convert("RGBA" if "A" in target.getbands() else "RGB")
                    target.save(converted, format="PNG")
                    data = converted.getvalue()
            scale = min(1.0, MAX_IMAGE_WIDTH / width, MAX_IMAGE_HEIGHT / height)
            flowable = RLImage(io.BytesIO(data), width=width * scale, height=height * scale)
            flowable.hAlign = "LEFT"
            return flowable
        except Exception as exc:
            print(f"Warning: Could not render question image: {exc}")
            return None

    @classmethod
    def _question_image_flowables(cls, question: Any, cache: Dict[str, Optional[bytes]],
                                  warning_style: ParagraphStyle) -> List[Any]:
        """Image flowables for ``question.image_url`` (empty when absent/unsupported)."""
        image_url = getattr(question, "image_url", None)
        if not isinstance(image_url, str) or not image_url.strip():
            return []
        image_url = image_url.strip()
        if not cls._is_remote_image_url(image_url) and not image_url.startswith("/"):
            return []  # unsupported URL form: nothing to embed
        data = cls._load_image_bytes(image_url, cache)
        flowable = cls._build_image_flowable(data) if data else None
        if flowable is None:
            return [Paragraph(IMAGE_LOAD_FAILED_TEXT, warning_style)]
        return [Spacer(1, 4), flowable, Spacer(1, 4)]

    @classmethod
    def _segment_table_flowables(cls, question: Any, temp_files: List[str],
                                 style: ParagraphStyle) -> List[Any]:
        """Tables stored in ``question.segments`` (e.g. stripped from the stem by the vision parser).

        Skipped when the question content already carries a table so the same table is never
        rendered twice.
        """
        if cls._contains_table(cls._question_content_text(question)):
            return []
        segments = getattr(question, 'segments', None)
        if not isinstance(segments, list):
            return []
        elements: List[Any] = []
        for segment in segments:
            if not isinstance(segment, dict) or segment.get('type') != 'table':
                continue
            markdown = segment.get('content')
            if not isinstance(markdown, str) or not markdown.strip():
                continue
            table = cls._build_markdown_table(markdown, temp_files, style)
            if table is not None:
                elements.extend([Spacer(1, 4), table, Spacer(1, 4)])
        return elements

    @classmethod
    def generate_exercise_pdf(cls, exercise: Exercise) -> bytes:
        """
        Generates a PDF byte stream for an Exercise containing questions and answer key table.
        """
        cls.register_fonts()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom Paragraph Styles with VietnameseFont
        title_style = ParagraphStyle(
            'ExamTitle',
            parent=styles['Normal'],
            fontName='VietnameseFont-Bold',
            fontSize=15,
            leading=18,
            alignment=1,  # Center
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=3
        )
        subtitle_bold_style = ParagraphStyle(
            'ExamSubTitleBold',
            parent=styles['Normal'],
            fontName='VietnameseFont-Bold',
            fontSize=12,
            leading=15,
            alignment=1,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=4
        )
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Normal'],
            fontName='VietnameseFont-Bold',
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=10,
            spaceAfter=6
        )
        question_text_style = ParagraphStyle(
            'QuestionText',
            parent=styles['Normal'],
            fontName='VietnameseFont-Bold',
            fontSize=11,
            leading=17,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=3
        )
        option_style = ParagraphStyle(
            'OptionText',
            parent=styles['Normal'],
            fontName='VietnameseFont',
            fontSize=10.5,
            leading=18,
            textColor=colors.HexColor("#334155"),
            spaceAfter=2
        )
        answer_key_header_style = ParagraphStyle(
            'AnswerKeyHeader',
            parent=styles['Normal'],
            fontName='VietnameseFont-Bold',
            fontSize=9.5,
            leading=12,
            alignment=1,
            textColor=colors.HexColor("#1E293B")
        )
        answer_key_cell_style = ParagraphStyle(
            'AnswerKeyCell',
            parent=styles['Normal'],
            fontName='VietnameseFont',
            fontSize=9,
            leading=12,
            alignment=1,
            textColor=colors.HexColor("#334155")
        )
        image_warning_style = ParagraphStyle(
            'ImageWarning',
            parent=styles['Normal'],
            fontName='VietnameseFont',
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#B91C1C"),
            spaceBefore=2,
            spaceAfter=2
        )

        story = []
        temp_files: List[str] = []
        # One cache per generation: the same image URL is never fetched/read twice.
        image_cache: Dict[str, Optional[bytes]] = {}

        try:
            # 1. Exam header: use the exercise title and duration when available.
            exercise_title = getattr(exercise, 'title', None)
            if not isinstance(exercise_title, str) or not exercise_title.strip():
                exercise_title = "ĐỀ THI MINH HỌA – TOÁN 12"
            story.append(Paragraph(f"<b>{cls._escape_html(exercise_title.strip())}</b>", title_style))
            story.append(Paragraph("<b>ĐỀ THI TỔNG HỢP – PHÂN HÓA NHIỀU MỨC ĐỘ</b>", subtitle_bold_style))

            duration_minutes = None
            exercise_metadata = getattr(exercise, 'ai_metadata', None)
            if isinstance(exercise_metadata, dict):
                candidate = exercise_metadata.get('duration_minutes')
                if isinstance(candidate, (int, float)) and not isinstance(candidate, bool) and candidate > 0:
                    duration_minutes = int(candidate)
            duration_text = (f"Thời gian làm bài: {duration_minutes} phút"
                             if duration_minutes else "Thời gian làm bài: 90 phút")

            header_table_data = [[
                Paragraph(duration_text, ParagraphStyle('LeftSub', fontName='VietnameseFont', fontSize=10, leading=12)),
                Paragraph("<i>Không kể thời gian phát đề</i>", ParagraphStyle('RightSub', fontName='VietnameseFont', fontSize=10, leading=12, alignment=2))
            ]]
            header_table = Table(header_table_data, colWidths=[260, 260])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(header_table)
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#475569"), spaceAfter=10))

            # Sort questions by display_order, filtering out deleted
            active_questions = [q for q in exercise.questions if getattr(q, 'status', 'ACTIVE') != 'DELETED']
            
            def get_sort_key(item):
                val = getattr(item, 'created_at', None)
                if val is None or hasattr(val, '_mock_name'):
                    return 0
                return val

            latest_questions_map = {}
            for q in sorted(active_questions, key=get_sort_key):
                latest_questions_map[q.display_order] = q

            questions = sorted(latest_questions_map.values(), key=lambda q: q.display_order)

            part1_questions = [q for q in questions if q.question_type in (QuestionTypeEnum.MultipleChoice.value, "MultipleChoice")]
            part2_questions = [q for q in questions if q.question_type in (QuestionTypeEnum.TrueFalse.value, "TrueFalse")]
            part3_questions = [q for q in questions if q.question_type in (QuestionTypeEnum.ShortAnswer.value, "ShortAnswer")]

            other_questions = [q for q in questions if q.question_type == "Other"]

            def clean_option_text(text: str) -> str:
                """Strip leading duplicate option labels like 'A. ', 'B. ', 'a) ', etc."""
                clean = re.sub(r"^[A-Da-d][\.:/\)]\s*", "", text.strip())
                return clean

            def question_prefix(q: Any) -> str:
                """Inline question header ("Câu 3. [Vận dụng] ") rendered before the stem."""
                difficulty = getattr(q, 'difficulty', None)
                diff_str = f"[{difficulty}] " if isinstance(difficulty, str) and difficulty else ""
                return f"Câu {q.display_order}. {diff_str}"

            # 2. Render Part I (Multiple Choice 4 Options)
            if part1_questions:
                story.append(Paragraph("<b>PHẦN I. Câu hỏi trắc nghiệm 4 lựa chọn.</b>", section_style))
                for q in part1_questions:
                    q_elements = []
                    q_elements.extend(cls._format_content_blocks(
                        cls._question_content_text(q), question_text_style, temp_files, prefix=question_prefix(q)
                    ))
                    q_elements.extend(cls._question_image_flowables(q, image_cache, image_warning_style))
                    q_elements.extend(cls._segment_table_flowables(q, temp_files, question_text_style))

                    # Options
                    opts = sorted(q.answer_options, key=lambda o: o.display_order)
                    if opts:
                        opt_cells = []
                        labels = ["A", "B", "C", "D"]
                        max_len = 0
                        for idx, opt in enumerate(opts):
                            lbl = labels[idx] if idx < len(labels) else f"({idx+1})"
                            cleaned_content = clean_option_text(opt.content)
                            max_len = max(max_len, len(cleaned_content))
                            opt_markup = cls.format_content_to_markup(cleaned_content, temp_files, fontsize=10)
                            opt_cells.append(Paragraph(f"<b>{lbl}.</b> {opt_markup}", option_style))

                        # Dynamic column layout: 4 columns if very short, 2 columns if medium, 1 column if long
                        if max_len <= 15 and len(opt_cells) == 4:
                            rows = [opt_cells]
                            col_widths = [130, 130, 130, 130]
                        elif max_len <= 45:
                            rows = []
                            for i in range(0, len(opt_cells), 2):
                                row = [opt_cells[i]]
                                if i + 1 < len(opt_cells):
                                    row.append(opt_cells[i+1])
                                else:
                                    row.append(Paragraph("", option_style))
                                rows.append(row)
                            col_widths = [260, 260]
                        else:
                            rows = [[c] for c in opt_cells]
                            col_widths = [520]

                        t = Table(rows, colWidths=col_widths)
                        t.setStyle(TableStyle([
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('LEFTPADDING', (0, 0), (-1, -1), 0),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                            ('TOPPADDING', (0, 0), (-1, -1), 4),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ]))
                        q_elements.append(t)

                    q_elements.append(Spacer(1, 8))
                    cls._append_question(story, q_elements)

            # 3. Render Part II (True / False)
            if part2_questions:
                story.append(Spacer(1, 8))
                story.append(Paragraph("<b>PHẦN II. Câu hỏi trắc nghiệm đúng sai.</b>", section_style))
                for q in part2_questions:
                    q_elements = []
                    q_elements.extend(cls._format_content_blocks(
                        cls._question_content_text(q), question_text_style, temp_files, prefix=question_prefix(q)
                    ))
                    q_elements.extend(cls._question_image_flowables(q, image_cache, image_warning_style))
                    q_elements.extend(cls._segment_table_flowables(q, temp_files, question_text_style))

                    opts = sorted(q.answer_options, key=lambda o: o.display_order)
                    if opts:
                        labels = ["a", "b", "c", "d"]
                        for idx, opt in enumerate(opts):
                            lbl = labels[idx] if idx < len(labels) else f"({idx+1})"
                            cleaned_content = clean_option_text(opt.content)
                            opt_markup = cls.format_content_to_markup(cleaned_content, temp_files, fontsize=10)
                            q_elements.append(Spacer(1, 2))
                            q_elements.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>{lbl})</b> {opt_markup}", option_style))

                    q_elements.append(Spacer(1, 8))
                    cls._append_question(story, q_elements)

            # 4. Render Part III (Short Answer)
            if part3_questions:
                story.append(Spacer(1, 6))
                story.append(Paragraph("<b>PHẦN III. Câu hỏi trả lời ngắn.</b>", section_style))
                for q in part3_questions:
                    q_elements = []
                    q_elements.extend(cls._format_content_blocks(
                        cls._question_content_text(q), question_text_style, temp_files, prefix=question_prefix(q)
                    ))
                    q_elements.extend(cls._question_image_flowables(q, image_cache, image_warning_style))
                    q_elements.extend(cls._segment_table_flowables(q, temp_files, question_text_style))
                    q_elements.append(Spacer(1, 6))
                    cls._append_question(story, q_elements)

            # Part IV (Other): stem followed by numbered sub-questions; no answer key rows
            if other_questions:
                story.append(Spacer(1, 6))
                story.append(Paragraph("<b>PHẦN IV. Câu hỏi khác.</b>", section_style))
                for q in other_questions:
                    q_elements = []
                    q_elements.extend(cls._format_content_blocks(
                        cls._question_content_text(q), question_text_style, temp_files,
                        prefix=f"Câu {q.display_order}. "
                    ))
                    q_elements.extend(cls._question_image_flowables(q, image_cache, image_warning_style))
                    q_elements.extend(cls._segment_table_flowables(q, temp_files, question_text_style))
                    for idx, opt in enumerate(sorted(q.answer_options, key=lambda o: o.display_order), 1):
                        q_elements.extend(cls._format_content_blocks(
                            opt.content, option_style, temp_files, prefix=f"{idx}) "
                        ))
                    q_elements.append(Spacer(1, 6))
                    cls._append_question(story, q_elements)

            # 5. Answer Key Section (Clean 3-Table Design)
            story.append(Spacer(1, 12))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#475569"), spaceAfter=8))
            story.append(Paragraph("<b>ĐÁP ÁN TOÁN 12</b>", title_style))

            # Part 1 Answer Table (3 columns: 1-4, 5-8, 9-12)
            if part1_questions:
                story.append(Paragraph("<b>PHẦN I – TRẮC NGHIỆM 4 LỰA CHỌN</b>", subtitle_bold_style))
                p1_matrix = [[
                    Paragraph("<b>Câu</b>", answer_key_header_style), Paragraph("<b>ĐA</b>", answer_key_header_style),
                    Paragraph("<b>Câu</b>", answer_key_header_style), Paragraph("<b>ĐA</b>", answer_key_header_style),
                    Paragraph("<b>Câu</b>", answer_key_header_style), Paragraph("<b>ĐA</b>", answer_key_header_style)
                ]]
                labels = ["A", "B", "C", "D"]
                p1_answers = {}
                for q in part1_questions:
                    opts = sorted(q.answer_options, key=lambda o: o.display_order)
                    ans = ""
                    for idx, opt in enumerate(opts):
                        if opt.is_correct:
                            ans = labels[idx] if idx < len(labels) else "A"
                            break
                    p1_answers[q.display_order] = ans

                for row_idx in range(1, 5):
                    c1, c2, c3 = row_idx, row_idx + 4, row_idx + 8
                    p1_matrix.append([
                        Paragraph(str(c1), answer_key_cell_style), Paragraph(p1_answers.get(c1, ""), answer_key_cell_style),
                        Paragraph(str(c2), answer_key_cell_style), Paragraph(p1_answers.get(c2, ""), answer_key_cell_style),
                        Paragraph(str(c3), answer_key_cell_style), Paragraph(p1_answers.get(c3, ""), answer_key_cell_style),
                    ])

                t1 = Table(p1_matrix, colWidths=[40, 50, 40, 50, 40, 50], repeatRows=1)
                t1.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#64748B")),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ]))
                story.append(t1)

            # Part 2 Answer Table (Câu 13-16 with a, b, c, d)
            if part2_questions:
                story.append(Spacer(1, 8))
                story.append(Paragraph("<b>PHẦN II – TRẮC NGHIỆM ĐÚNG / SAI</b>", subtitle_bold_style))
                p2_matrix = [[
                    Paragraph("<b>Câu</b>", answer_key_header_style),
                    Paragraph("<b>a)</b>", answer_key_header_style),
                    Paragraph("<b>b)</b>", answer_key_header_style),
                    Paragraph("<b>c)</b>", answer_key_header_style),
                    Paragraph("<b>d)</b>", answer_key_header_style)
                ]]
                for q in part2_questions:
                    opts = sorted(q.answer_options, key=lambda o: o.display_order)
                    a_stat = "Đ" if len(opts) > 0 and opts[0].is_correct else "S"
                    b_stat = "Đ" if len(opts) > 1 and opts[1].is_correct else "S"
                    c_stat = "Đ" if len(opts) > 2 and opts[2].is_correct else "S"
                    d_stat = "Đ" if len(opts) > 3 and opts[3].is_correct else "S"
                    p2_matrix.append([
                        Paragraph(str(q.display_order), answer_key_cell_style),
                        Paragraph(a_stat, answer_key_cell_style),
                        Paragraph(b_stat, answer_key_cell_style),
                        Paragraph(c_stat, answer_key_cell_style),
                        Paragraph(d_stat, answer_key_cell_style),
                    ])

                t2 = Table(p2_matrix, colWidths=[50, 55, 55, 55, 55], repeatRows=1)
                t2.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#64748B")),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ]))
                story.append(t2)

            # Part 3 Answer Table (Câu 17-20 with Đáp số)
            if part3_questions:
                story.append(Spacer(1, 8))
                story.append(Paragraph("<b>PHẦN III – TRẢ LỜI NGẮN</b>", subtitle_bold_style))
                p3_matrix = [[
                    Paragraph("<b>Câu</b>", answer_key_header_style),
                    Paragraph("<b>Đáp số</b>", answer_key_header_style)
                ]]
                for q in part3_questions:
                    answer_text = q.correct_answer if isinstance(q.correct_answer, str) else ""
                    p3_matrix.append([
                        Paragraph(str(q.display_order), answer_key_cell_style),
                        Paragraph(answer_text, answer_key_cell_style)
                    ])

                t3 = Table(p3_matrix, colWidths=[70, 200], repeatRows=1)
                t3.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#64748B")),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ]))
                story.append(t3)

            doc.build(story)
            pdf_bytes = buffer.getvalue()
            buffer.close()
            return pdf_bytes
        finally:
            for fpath in temp_files:
                if os.path.exists(fpath):
                    try:
                        os.unlink(fpath)
                    except Exception:
                        pass

