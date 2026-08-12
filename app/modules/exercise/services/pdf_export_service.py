# File Name: pdf_export_service.py
# Description: Service for generating formatted PDF documents from exercise data including LaTeX math rendering.
# Created At: 2026-08-12
# Created By: Tam Khang
# Updated At: 2026-08-12
# Updated By: Tam Khang

import io
import os
import re
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

        # 1. Header & Title
        title_text = exercise.title or "ĐỀ THI TRẮC NGHIỆM"
        story.append(Paragraph(title_text.upper(), title_style))
        story.append(Paragraph("Môn học: THPT QG · Thời gian làm bài: 90 phút", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=15))

        # Sort questions by display_order, filtering out deleted and deduplicating multiple import runs
        active_questions = [q for q in exercise.questions if getattr(q, 'status', 'ACTIVE') != 'DELETED']
        
        # Keep latest question for each display_order
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
            """
            Parses text and converts embedded LaTeX ($ ... $) into rendered Math images.
            Returns a list of Flowable elements (Paragraphs and RLImages).
            """
            # Clean non-printable surrogate squares
            clean_text = re.sub(r"[\uFFFD\u25A0\u25A1]", "", text)
            parts = re.split(r"(\$.*?\$)", clean_text)
            
            elements = []
            for part in parts:
                if not part:
                    continue
                if part.startswith("$") and part.endswith("$") and len(part) > 2:
                    img_buf = cls.render_latex_to_image(part, fontsize=11)
                    if img_buf:
                        try:
                            # Use PIL to read image size
                            from PIL import Image as PILImage
                            pil_img = PILImage.open(img_buf)
                            w, h = pil_img.size
                            img_buf.seek(0)
                            
                            # Scale height to ~16-20pt
                            aspect = w / h if h > 0 else 1.0
                            target_h = 16
                            target_w = target_h * aspect
                            
                            elements.append(RLImage(img_buf, width=target_w, height=target_h))
                        except Exception:
                            elements.append(Paragraph(part, style))
                    else:
                        elements.append(Paragraph(part, style))
                else:
                    elements.append(Paragraph(part, style))
            return elements if elements else [Paragraph(clean_text, style)]

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
                        opt_cells.append(Paragraph(f"<b>{lbl}.</b> {cleaned_content}", option_style))

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
                        q_elements.append(Paragraph(f"<b>{lbl})</b> {cleaned_content}", option_style))

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
