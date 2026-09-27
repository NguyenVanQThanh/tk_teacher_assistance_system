# File Name: pdf_export_service.py
# Description: Service for generating formatted PDF documents from exercise data including LaTeX math rendering.
# Created At: 2026-08-12
# Created By: Tam Khang
# Updated At: 2026-09-27
# Updated By: Tam Khang

import io
import os
import re
import tempfile
from typing import List, Tuple, Dict, Any, Optional
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['mathtext.fontset'] = 'cm'  # Computer Modern LaTeX math fontset
matplotlib.rcParams['font.family'] = 'serif'
matplotlib.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
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
        """Register Vietnamese UTF-8 compatible Times New Roman TrueType fonts for ReportLab."""
        if cls._font_registered:
            return

        font_paths = [
            ("VietnameseFont", "C:/Windows/Fonts/times.ttf"),
            ("VietnameseFont-Bold", "C:/Windows/Fonts/timesbd.ttf"),
            ("VietnameseFont-Italic", "C:/Windows/Fonts/timesi.ttf"),
            ("VietnameseFont", "C:/Windows/Fonts/arial.ttf"),
            ("VietnameseFont-Bold", "C:/Windows/Fonts/arialbd.ttf"),
            ("VietnameseFont", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
            ("VietnameseFont-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"),
        ]

        # Add bundled matplotlib fonts as cross-platform fallbacks
        try:
            mpl_font_dir = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
            font_paths.extend([
                ("VietnameseFont", os.path.join(mpl_font_dir, "DejaVuSerif.ttf")),
                ("VietnameseFont-Bold", os.path.join(mpl_font_dir, "DejaVuSerif-Bold.ttf")),
                ("VietnameseFont-Italic", os.path.join(mpl_font_dir, "DejaVuSerif-Italic.ttf")),
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

            fig = plt.figure(figsize=(0.01, 0.01))
            fig.text(0, 0, f"${clean_latex}$", fontsize=render_fontsize)
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.01, transparent=True, dpi=300)
            plt.close(fig)
            buf.seek(0)

            from PIL import Image as PILImage
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
            plt.close('all')
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

        story = []
        temp_files: List[str] = []

        try:
            # 1. Standard National Exam Header & Title
            story.append(Paragraph("<b>ĐỀ THI MINH HỌA – TOÁN 12</b>", title_style))
            story.append(Paragraph("<b>ĐỀ THI TỔNG HỢP – PHÂN HÓA NHIỀU MỨC ĐỘ</b>", subtitle_bold_style))
            
            header_table_data = [[
                Paragraph("Thời gian làm bài: 90 phút", ParagraphStyle('LeftSub', fontName='VietnameseFont', fontSize=10, leading=12)),
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

            def clean_option_text(text: str) -> str:
                """Strip leading duplicate option labels like 'A. ', 'B. ', 'a) ', etc."""
                clean = re.sub(r"^[A-Da-d][\.:/\)]\s*", "", text.strip())
                return clean

            def format_content_with_latex(text: str, style: ParagraphStyle) -> List[Any]:
                if "$$" in text:
                    chunks = re.split(r'(\$\$[\s\S]*?\$\$)', text)
                    elements = []
                    for chunk in chunks:
                        if not chunk.strip():
                            continue
                        if chunk.startswith("$$") and chunk.endswith("$$"):
                            img_tag = cls.render_latex_to_inline_tag(chunk, temp_files, fontsize=13)
                            if img_tag:
                                center_style = ParagraphStyle('CenterMath', parent=style, alignment=1, spaceBefore=4, spaceAfter=4)
                                elements.append(Paragraph(img_tag, center_style))
                            else:
                                clean_p = chunk.strip("$").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                                elements.append(Paragraph(clean_p, style))
                        else:
                            markup = cls.format_content_to_markup(chunk, temp_files, fontsize=11)
                            if markup.strip():
                                elements.append(Paragraph(markup, style))
                    return elements
                else:
                    markup = cls.format_content_to_markup(text, temp_files, fontsize=11)
                    return [Paragraph(markup, style)]

            # 2. Render Part I (Multiple Choice 4 Options)
            if part1_questions:
                story.append(Paragraph("<b>PHẦN I. Câu hỏi trắc nghiệm 4 lựa chọn.</b>", section_style))
                for q in part1_questions:
                    q_elements = []
                    diff_str = f"[{q.difficulty}] " if q.difficulty else ""
                    q_text = q.content_latex if q.content_latex else q.content
                    q_head = f"Câu {q.display_order}. {diff_str}{q_text}"
                    q_elements.extend(format_content_with_latex(q_head, question_text_style))

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
                    story.append(KeepTogether(q_elements))

            # 3. Render Part II (True / False)
            if part2_questions:
                story.append(Spacer(1, 8))
                story.append(Paragraph("<b>PHẦN II. Câu hỏi trắc nghiệm đúng sai.</b>", section_style))
                for q in part2_questions:
                    q_elements = []
                    diff_str = f"[{q.difficulty}] " if q.difficulty else ""
                    q_text = q.content_latex if q.content_latex else q.content
                    q_head = f"Câu {q.display_order}. {diff_str}{q_text}"
                    q_elements.extend(format_content_with_latex(q_head, question_text_style))

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
                    story.append(KeepTogether(q_elements))

            # 4. Render Part III (Short Answer)
            if part3_questions:
                story.append(Spacer(1, 6))
                story.append(Paragraph("<b>PHẦN III. Câu hỏi trả lời ngắn.</b>", section_style))
                for q in part3_questions:
                    q_elements = []
                    diff_str = f"[{q.difficulty}] " if q.difficulty else ""
                    q_text = q.content_latex if q.content_latex else q.content
                    q_head = f"Câu {q.display_order}. {diff_str}{q_text}"
                    q_elements.extend(format_content_with_latex(q_head, question_text_style))
                    q_elements.append(Spacer(1, 6))
                    story.append(KeepTogether(q_elements))

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

                t1 = Table(p1_matrix, colWidths=[40, 50, 40, 50, 40, 50])
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

                t2 = Table(p2_matrix, colWidths=[50, 55, 55, 55, 55])
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
                    p3_matrix.append([
                        Paragraph(str(q.display_order), answer_key_cell_style),
                        Paragraph(q.correct_answer or "", answer_key_cell_style)
                    ])

                t3 = Table(p3_matrix, colWidths=[70, 200])
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

