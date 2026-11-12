# File Name: grading_report_service.py
# Description: Builds CSV and PDF grading result reports from attempt list items.
# Created At: 2026-11-12
# Created By: AI Agent
# Updated At: 2026-11-13
# Updated By: AI Agent

import csv
import io
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from app.modules.exercise.schemas import AttemptListItemOut
from app.modules.exercise.services.pdf_export_service import PdfExportService

HEADERS = ["Student", "Class", "Exercise", "Score", "Status", "Submitted At"]
STATUS_LABELS = {"pending_grading": "Pending grading", "pending_review": "Pending review", "approved": "Graded"}


def _rows(items: List[AttemptListItemOut]) -> List[list]:
    rows = []
    for a in items:
        st = a.status if a.status in STATUS_LABELS else ("approved" if a.score is not None else "pending_grading")
        when = a.end_time or a.start_time
        rows.append([
            a.student_name, a.class_name, a.exercise_title,
            "" if a.score is None else f"{a.score:.2f}",
            STATUS_LABELS[st],
            when.strftime("%Y-%m-%d %H:%M") if when else "",
        ])
    return rows


def _csv_safe(v: str) -> str:
    """Neutralise spreadsheet formula injection."""
    return "'" + v if v[:1] in ("=", "+", "-", "@", "\t", "\r") else v


def build_csv(items: List[AttemptListItemOut]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(HEADERS)
    for r in _rows(items):
        w.writerow([_csv_safe(str(c)) for c in r])
    return ("﻿" + buf.getvalue()).encode("utf-8")  # BOM so Excel detects UTF-8


def build_pdf(items: List[AttemptListItemOut]) -> bytes:
    PdfExportService.register_fonts()
    styles = getSampleStyleSheet()
    for name in ("Title", "Normal"):
        styles[name].fontName = "VietnameseFont"
    out = io.BytesIO()
    doc = SimpleDocTemplate(out, pagesize=landscape(A4), title="Grading Report")
    scores = [a.score for a in items if a.score is not None]
    avg = f"{sum(scores) / len(scores):.2f}" if scores else "-"
    data = [HEADERS] + [[Paragraph(str(c), styles["Normal"]) for c in r] for r in _rows(items)]
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "VietnameseFont"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    doc.build([
        Paragraph("Grading Report", styles["Title"]),
        Paragraph(f"Submissions: {len(items)} | Graded: {len(scores)} | Average score: {avg}", styles["Normal"]),
        Spacer(1, 12), table,
    ])
    return out.getvalue()
