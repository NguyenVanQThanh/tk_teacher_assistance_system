# File Name: pdf_export_service.py
# Description: Service for generating formatted PDF documents from exercise data including LaTeX math rendering.
# Created At: 2026-08-12
# Created By: Tam Khang
# Updated At: 2026-08-13
# Updated By: Tam Khang

import io
import os
import re
import tempfile
from typing import List, Tuple, Dict, Any, Optional
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

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


class PdfExportService:
    """Service to export exercise data from database to formatted PDF document."""

    _font_registered = False

    @classmethod
    def _register_fonts(cls):
        """Register Vietnamese UTF-8 compatible TrueType fonts for ReportLab."""
        if cls._font_registered:
            return

        font_paths = [
            ("VietnameseFont", "C:/Windows/Fonts/arial.ttf"),
            ("VietnameseFont-Bold", "C:/Windows/Fonts/arialbd.ttf"),
            ("VietnameseFont", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            ("VietnameseFont-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ]

        regular_registered = False
        bold_registered = False

        for font_name, path in font_paths:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, path))
                    if font_name == "VietnameseFont":
                        regular_registered = True
                    elif font_name == "VietnameseFont-Bold":
                        bold_registered = True
                except Exception as e:
                    print(f"Warning: Could not register font {font_name} from {path}: {e}")

        if not regular_registered:
            # Fallback to Helvetica if TrueType font file is unavailable
            pdfmetrics.registerFont(TTFont("VietnameseFont", "Helvetica"))
        if not bold_registered:
            pdfmetrics.registerFont(TTFont("VietnameseFont-Bold", "Helvetica-Bold"))

        cls._font_registered = True

    @staticmethod
    def render_latex_to_image(latex_str: str, fontsize: int = 12) -> Optional[io.BytesIO]:
        """Convert a LaTeX formula string into a PNG image BytesIO stream using Matplotlib."""
        try:
            clean_latex = latex_str.strip("$").strip()
            if not clean_latex:
                return None
            
            fig = plt.figure(figsize=(0.01, 0.01))
            fig.text(0, 0, f"${clean_latex}$", fontsize=fontsize)
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.03, transparent=True, dpi=200)
            plt.close(fig)
            buf.seek(0)
            return buf
        except Exception as e:
            print(f"Warning: Failed to render LaTeX '{latex_str}': {e}")
            plt.close('all')
            return None

    @classmethod
    def _normalize_math_in_text(cls, text: str) -> str:
        """
        Normalizes vector symbols, exponents, radical/fraction expressions, and unwrapped LaTeX math formulas.
        Converts them into standard LaTeX $ ... $ syntax for Matplotlib rendering.
        """
        if not text:
            return ""

        # Clean non-printable surrogate square characters
        clean_text = re.sub(r"[\uFFFD\u25A0\u25A1]", "", text)

        # Vector arrow conversions: a\u20d7, a\u2192, a⃗ -> $\vec{a}$
        clean_text = re.sub(r'([a-zA-Z])[\u20d7\u2192⃗]', r'$\\vec{\1}$', clean_text)

        sup_map = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")

        parts = re.split(r'(\$.*?\$)', clean_text)
        new_parts = []

        for part in parts:
            if not part:
                continue
            if part.startswith("$") and part.endswith("$"):
                new_parts.append(part)
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

            fig = plt.figure(figsize=(0.01, 0.01))
            fig.text(0, 0, f"${clean_latex}$", fontsize=fontsize)
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.02, transparent=True, dpi=200)
            plt.close(fig)
            buf.seek(0)

            from PIL import Image as PILImage
            img = PILImage.open(buf)
            w, h = img.size
            aspect = w / h if h > 0 else 1.0

            target_h = max(12, int(fontsize * 1.25))
            target_w = target_h * aspect

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            temp_file.write(buf.getvalue())
            temp_file.close()

            temp_files_list.append(temp_file.name)
            img_path = temp_file.name.replace("\\", "/")
            return f'<img src="{img_path}" width="{target_w:.1f}" height="{target_h:.1f}" valign="middle"/>'
        except Exception as e:
            print(f"Warning: Failed to render LaTeX '{latex_str}': {e}")
            plt.close('all')
            return None

    @classmethod
    def format_content_to_markup(cls, raw_text: str, temp_files_list: List[str], fontsize: int = 11) -> str:
        """
        Parses text, normalizes math formulas, renders LaTeX ($...$) into temporary images,
        and returns ReportLab Paragraph HTML-compatible markup string with inline <img> tags.
        """
        if not raw_text:
            return ""

        normalized_text = cls._normalize_math_in_text(raw_text)
        parts = re.split(r"(\$.*?\$)", normalized_text)

        markup_parts = []
        for part in parts:
            if not part:
                continue
            if part.startswith("$") and part.endswith("$") and len(part) > 2:
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

    @classmethod
    def generate_exercise_pdf(cls, exercise: Exercise) -> bytes:
        """
        Generates a PDF byte stream for an Exercise containing questions and answer key table.
        """
        cls._register_fonts()

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
            fontSize=16,
            leading=20,
            alignment=1,  # Center
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            'ExamSubTitle',
            parent=styles['Normal'],
            fontName='VietnameseFont',
            fontSize=11,
            leading=14,
            alignment=1,
            textColor=colors.HexColor("#475569"),
            spaceAfter=15
        )
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Normal'],
            fontName='VietnameseFont-Bold',
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=12,
            spaceAfter=8
        )
        question_text_style = ParagraphStyle(
            'QuestionText',
            parent=styles['Normal'],
            fontName='VietnameseFont-Bold',
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=4
        )
        option_style = ParagraphStyle(
            'OptionText',
            parent=styles['Normal'],
            fontName='VietnameseFont',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334155"),
            spaceAfter=3
        )
        answer_key_header_style = ParagraphStyle(
            'AnswerKeyHeader',
            parent=styles['Normal'],
            fontName='VietnameseFont-Bold',
            fontSize=10,
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

        story = []
        temp_files: List[str] = []

        try:
            # 1. Header & Title
            title_text = exercise.title or "ĐỀ THI TRẮC NGHIỆM"
            story.append(Paragraph(title_text.upper(), title_style))
            story.append(Paragraph("Môn học: THPT QG · Thời gian làm bài: 90 phút", subtitle_style))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=15))

            # Sort questions by display_order, filtering out deleted and deduplicating multiple import runs
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

            part1_questions = [q for q in questions if q.question_type == QuestionTypeEnum.MultipleChoice.value or q.question_type == "MultipleChoice"]
            part2_questions = [q for q in questions if q.question_type == QuestionTypeEnum.TrueFalse.value or q.question_type == "TrueFalse"]
            part3_questions = [q for q in questions if q.question_type == QuestionTypeEnum.ShortAnswer.value or q.question_type == "ShortAnswer"]

            def clean_option_text(text: str) -> str:
                """Strip leading duplicate option labels like 'A. ', 'B. ', 'a) ', etc."""
                clean = re.sub(r"^[A-Da-d][\.:/\)]\s*", "", text.strip())
                return clean

            def format_content_with_latex(text: str, style: ParagraphStyle) -> List[Any]:
                markup = cls.format_content_to_markup(text, temp_files, fontsize=11)
                return [Paragraph(markup, style)]

            # 2. Render Part I
            if part1_questions:
                story.append(Paragraph("PHẦN I. Câu hỏi trắc nghiệm 4 lựa chọn.", section_style))
                for q in part1_questions:
                    q_elements = []
                    diff_str = f"[{q.difficulty}] " if q.difficulty else ""
                    q_head = f"Câu {q.display_order}. {diff_str}{q.content}"
                    q_elements.extend(format_content_with_latex(q_head, question_text_style))

                    # Options
                    opts = sorted(q.answer_options, key=lambda o: o.display_order)
                    if opts:
                        opt_cells = []
                        labels = ["A", "B", "C", "D"]
                        for idx, opt in enumerate(opts):
                            lbl = labels[idx] if idx < len(labels) else f"({idx+1})"
                            cleaned_content = clean_option_text(opt.content)
                            opt_markup = cls.format_content_to_markup(cleaned_content, temp_files, fontsize=10)
                            opt_cells.append(Paragraph(f"<b>{lbl}.</b> {opt_markup}", option_style))

                        # Format options in 2 columns
                        rows = []
                        for i in range(0, len(opt_cells), 2):
                            row = [opt_cells[i]]
                            if i + 1 < len(opt_cells):
                                row.append(opt_cells[i+1])
                            else:
                                row.append(Paragraph("", option_style))
                            rows.append(row)

                        if rows:
                            t = Table(rows, colWidths=[250, 250])
                            t.setStyle(TableStyle([
                                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                                ('TOPPADDING', (0, 0), (-1, -1), 2),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                            ]))
                            q_elements.append(t)

                    q_elements.append(Spacer(1, 8))
                    story.append(KeepTogether(q_elements))

            # 3. Render Part II
            if part2_questions:
                story.append(Spacer(1, 10))
                story.append(Paragraph("PHẦN II. Câu hỏi trắc nghiệm Đúng / Sai.", section_style))
                for q in part2_questions:
                    q_elements = []
                    diff_str = f"[{q.difficulty}] " if q.difficulty else ""
                    q_head = f"Câu {q.display_order}. {diff_str}{q.content}"
                    q_elements.extend(format_content_with_latex(q_head, question_text_style))

                    opts = sorted(q.answer_options, key=lambda o: o.display_order)
                    if opts:
                        labels = ["a", "b", "c", "d"]
                        for idx, opt in enumerate(opts):
                            lbl = labels[idx] if idx < len(labels) else f"({idx+1})"
                            cleaned_content = clean_option_text(opt.content)
                            opt_markup = cls.format_content_to_markup(cleaned_content, temp_files, fontsize=10)
                            q_elements.append(Paragraph(f"<b>{lbl})</b> {opt_markup}", option_style))

                    q_elements.append(Spacer(1, 8))
                    story.append(KeepTogether(q_elements))

            # 4. Render Part III
            if part3_questions:
                story.append(Spacer(1, 10))
                story.append(Paragraph("PHẦN III. Câu hỏi trả lời ngắn.", section_style))
                for q in part3_questions:
                    q_elements = []
                    diff_str = f"[{q.difficulty}] " if q.difficulty else ""
                    q_head = f"Câu {q.display_order}. {diff_str}{q.content}"
                    q_elements.extend(format_content_with_latex(q_head, question_text_style))
                    q_elements.append(Spacer(1, 8))
                    story.append(KeepTogether(q_elements))

            # 5. Answer Key Table Section
            story.append(Spacer(1, 15))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=10))
            story.append(Paragraph("BẢNG ĐÁP ÁN MẪU", section_style))

            table_data = [[
                Paragraph("Câu", answer_key_header_style),
                Paragraph("Đáp án đúng", answer_key_header_style)
            ]]

            for q in questions:
                ans_str = ""
                if q.question_type in [QuestionTypeEnum.MultipleChoice.value, "MultipleChoice"]:
                    opts = sorted(q.answer_options, key=lambda o: o.display_order)
                    labels = ["A", "B", "C", "D"]
                    for idx, opt in enumerate(opts):
                        if opt.is_correct:
                            ans_str = labels[idx] if idx < len(labels) else "Đúng"
                            break
                elif q.question_type in [QuestionTypeEnum.TrueFalse.value, "TrueFalse"]:
                    opts = sorted(q.answer_options, key=lambda o: o.display_order)
                    labels = ["a", "b", "c", "d"]
                    parts = []
                    for idx, opt in enumerate(opts):
                        lbl = labels[idx] if idx < len(labels) else f"({idx+1})"
                        stat = "Đúng" if opt.is_correct else "Sai"
                        parts.append(f"{lbl}) {stat}")
                    ans_str = ", ".join(parts)
                else:
                    ans_str = q.correct_answer or ""

                table_data.append([
                    Paragraph(str(q.display_order), answer_key_cell_style),
                    Paragraph(ans_str, answer_key_cell_style)
                ])

            if len(table_data) > 1:
                ans_table = Table(table_data, colWidths=[60, 440])
                ans_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                story.append(ans_table)

            doc.build(story)
            pdf_bytes = buffer.getvalue()
            buffer.close()
            return pdf_bytes
        finally:
            for fpath in temp_files:
                if os.path.exists(fpath):
                    try:
                        os.remove(fpath)
                    except Exception:
                        pass

