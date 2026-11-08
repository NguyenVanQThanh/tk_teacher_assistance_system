# File Name: import_parser_service.py
# Description: Service for extracting text/images and parsing question templates and answer keys (Docx/PDF).
# Created At: 2026-08-09
# Created By: Tam Khang
# Updated At: 2026-09-02
# Updated By: Tam Khang

import os
import re
import io
import uuid
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
import logging
import docx
import pdfplumber

logger = logging.getLogger("smartlms.exercise.parser")

from app.modules.exercise.schemas import QuestionTypeEnum, DifficultyEnum


@dataclass
class ParsedOption:
    content: str
    is_correct: bool = False
    display_order: int = 0


@dataclass
class ParsedQuestion:
    question_number: int
    part: str  # "Part1", "Part2", "Part3"
    question_type: QuestionTypeEnum
    difficulty: Optional[DifficultyEnum]
    content: str
    content_markdown: Optional[str] = None
    content_latex: Optional[str] = None
    segments: Optional[List[Dict[str, Any]]] = None
    confidence_score: Optional[float] = None
    needs_review: bool = False
    image_url: Optional[str] = None
    answer_options: List[ParsedOption] = field(default_factory=list)
    correct_answer: Optional[str] = None
    # Exam (đề) this question belongs to when the file contains multiple exams, e.g. "ĐỀ SỐ 1"
    exam_label: Optional[str] = None
    # Figure location reported by the vision model (transient, used for cropping)
    image_page: Optional[int] = None
    image_bbox: Optional[List[float]] = None  # normalized [x0, y0, x1, y1] in 0-1000
    # Persisted onto Question.image_metadata once the cropped figure is stored
    image_metadata: Optional[Dict[str, Any]] = None


@dataclass
class ParseError:
    question_number: Optional[int]
    message: str


@dataclass
class ParseResult:
    questions: List[ParsedQuestion] = field(default_factory=list)
    errors: List[ParseError] = field(default_factory=list)


from app.core.config import QUESTION_IMAGE_DIR, QUESTION_IMAGE_URL_PREFIX

UPLOAD_DIR = str(QUESTION_IMAGE_DIR)
IMAGE_URL_PREFIX = QUESTION_IMAGE_URL_PREFIX


class ImportParserService:
    """Service to parse question documents (.docx/.pdf) and separate answer keys."""

    @staticmethod
    def extract_docx_content(file_bytes: bytes) -> Tuple[str, List[List[List[str]]], List[Dict[str, Any]]]:
        """
        Extract text, tables, and images from docx file bytes.
        Supports both standard text (<w:t>) and native Word OMath equations (<m:t>).
        Returns (full_text, tables_data, inline_images).
        """
        doc = docx.Document(io.BytesIO(file_bytes))
        full_text_lines = []
        tables_data = []
        inline_images = []

        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Extract images from docx relationships
        image_count = 0
        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                image_bytes = rel.target_part.blob
                image_ext = rel.target_ref.split(".")[-1] if "." in rel.target_ref else "png"
                if image_ext.lower() not in ["png", "jpg", "jpeg", "gif", "bmp", "webp"]:
                    image_ext = "png"
                filename = f"q_img_{uuid.uuid4().hex[:10]}.{image_ext}"
                filepath = os.path.join(UPLOAD_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(image_bytes)
                image_url = f"{IMAGE_URL_PREFIX}/{filename}"
                inline_images.append({
                    "url": image_url,
                    "index": image_count
                })
                image_count += 1

        def omml_to_latex(elem) -> str:
            """Recursively convert Word OMML (<m:oMath>) elements to LaTeX math string."""
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

            # Fraction (<m:f>) -> \frac{num}{den}
            if tag == 'f':
                num = "".join(omml_to_latex(c) for c in elem.xpath('./*[local-name()="num"]'))
                den = "".join(omml_to_latex(c) for c in elem.xpath('./*[local-name()="den"]'))
                return f"\\frac{{{num}}}{{{den}}}"

            # Superscript (<m:sSup>) -> base^{sup}
            elif tag == 'sSup':
                e = "".join(omml_to_latex(c) for c in elem.xpath('./*[local-name()="e"]'))
                sup = "".join(omml_to_latex(c) for c in elem.xpath('./*[local-name()="sup"]'))
                return f"{e}^{{{sup}}}"

            # Subscript (<m:sSub>) -> base_{sub}
            elif tag == 'sSub':
                e = "".join(omml_to_latex(c) for c in elem.xpath('./*[local-name()="e"]'))
                sub = "".join(omml_to_latex(c) for c in elem.xpath('./*[local-name()="sub"]'))
                return f"{e}_{{{sub}}}"

            # Sub-Superscript (<m:sSubSup>) -> base_{sub}^{sup}
            elif tag == 'sSubSup':
                e = "".join(omml_to_latex(c) for c in elem.xpath('./*[local-name()="e"]'))
                sub = "".join(omml_to_latex(c) for c in elem.xpath('./*[local-name()="sub"]'))
                sup = "".join(omml_to_latex(c) for c in elem.xpath('./*[local-name()="sup"]'))
                return f"{e}_{{{sub}}}^{{{sup}}}"

            # Radical / Square Root (<m:rad>) -> \sqrt[deg]{e}
            elif tag == 'rad':
                deg = "".join(omml_to_latex(c) for c in elem.xpath('./*[local-name()="deg"]'))
                e = "".join(omml_to_latex(c) for c in elem.xpath('./*[local-name()="e"]'))
                if deg.strip():
                    return f"\\sqrt[{deg}]{{{e}}}"
                return f"\\sqrt{{{e}}}"

            # Accent / Vector (<m:acc>) -> \vec{e} or \hat{e}
            elif tag == 'acc':
                e = "".join(omml_to_latex(c) for c in elem.xpath('./*[local-name()="e"]'))
                chr_val = elem.xpath('.//*[local-name()="chr"]/@*[local-name()="val"]')
                accent_char = chr_val[0] if chr_val else ""
                if accent_char in ["⃗", "->", "→"]:
                    return f"\\vec{{{e}}}"
                elif accent_char == "^":
                    return f"\\hat{{{e}}}"
                elif accent_char in ["̅", "‾"]:
                    return f"\\bar{{{e}}}"
                return f"\\vec{{{e}}}"

            # Text node (<m:t> or <w:t>)
            elif tag == 't':
                return elem.text or ""

            res = []
            for child in elem:
                res.append(omml_to_latex(child))
            return "".join(res)

        def get_elem_text(elem) -> str:
            """Extract text from paragraph or table cell, converting OMML math equations and Word run formatting to $ LaTeX $."""
            parts = []
            for child in elem:
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if tag in ["oMath", "oMathPara"]:
                    latex_expr = omml_to_latex(child).strip()
                    if latex_expr:
                        parts.append(f" ${latex_expr}$ ")
                else:
                    omath_nodes = child.xpath('.//*[local-name()="oMath"]')
                    if omath_nodes:
                        for sub in child:
                            sub_tag = sub.tag.split("}")[-1] if "}" in sub.tag else sub.tag
                            if sub_tag in ["oMath", "oMathPara"]:
                                latex_expr = omml_to_latex(sub).strip()
                                if latex_expr:
                                    parts.append(f" ${latex_expr}$ ")
                            else:
                                txts = sub.xpath('.//*[local-name()="t"]/text()')
                                parts.append("".join(txts))
                    else:
                        runs = child.xpath('.//*[local-name()="r"]')
                        if runs:
                            for r in runs:
                                t_nodes = r.xpath('.//*[local-name()="t"]/text()')
                                if not t_nodes:
                                    continue
                                r_text = "".join(t_nodes)
                                vert_align = r.xpath('.//*[local-name()="vertAlign"]/@*[local-name()="val"]')
                                val = vert_align[0] if vert_align else ""
                                if val == "superscript":
                                    parts.append(f"^{{{r_text}}}")
                                elif val == "subscript":
                                    parts.append(f"_{{{r_text}}}")
                                else:
                                    parts.append(r_text)
                        else:
                            txts = child.xpath('.//*[local-name()="t"]/text()')
                            parts.append("".join(txts))
            raw = "".join(parts).strip()
            return ImportParserService.normalize_extracted_text(raw)

        for p in doc.paragraphs:
            text = get_elem_text(p._p)
            if text:
                full_text_lines.append(text)

        for table in doc.tables:
            table_matrix = []
            for row in table.rows:
                row_data = [get_elem_text(cell._tc) for cell in row.cells]
                table_matrix.append(row_data)
            if table_matrix:
                tables_data.append(table_matrix)

        full_text = "\n".join(full_text_lines)
        return full_text, tables_data, inline_images

    @staticmethod
    def normalize_extracted_text(text: str) -> str:
        """
        Normalizes unicode superscripts, vectors, and mathematical notations in extracted text,
        wrapping standard math formulas and equations in LaTeX $...$ delimiters.
        """
        if not text:
            return text

        # 1. Normalize unicode minus / en-dash to standard minus
        text = text.replace('−', '-').replace('–', '-')

        # 2. Exponents: e.g. x3 -> x^{3}, -3x2 -> -3x^{2}, t3 -> t^{3}, 108cm 3 -> 108cm^{3}
        sup_map = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
        text = re.sub(r'([a-zA-Z])([⁰¹²³⁴⁵⁶⁷⁸⁹]+)', lambda m: f"{m.group(1)}^{{{m.group(2).translate(sup_map)}}}", text)
        text = re.sub(r'([a-zA-Z])(\d+)', lambda m: f"{m.group(1)}^{{{m.group(2)}}}", text)
        text = re.sub(r'(\d+)\s*cm\s*([23])\b', r'\1cm^{\2}', text)

        # 3. Vector arrows: -> or -→ or \u2192
        text = re.sub(r'([a-zA-Z])[\u20d7\u2192⃗]', r'\\vec{\1}', text)
        text = re.sub(r'[\u20d7\u2192⃗]([a-zA-Z])', r'\\vec{\1}', text)
        text = re.sub(r'-\s*→|−\s*→|-->', r'\\vec{v}', text)

        # 4. Reconstruct broken 2D fraction layouts:
        text = re.sub(
            r'Hàm\s+số\s*\n\s*([xyt0-9\^\{\}\+\-\s]+?)\s*\n\s*y\s*=\s*\.?\s*\n\s*([xyt0-9\^\{\}\+\-\s]+?)(?=\s*\n\s*Số|\s*\n\s*có|\s*\n\s*Đồ)',
            lambda m: f"Hàm số $y = \\frac{{{m.group(1).strip()}}}{{{m.group(2).strip()}}}$ ",
            text,
            flags=re.IGNORECASE
        )

        text = re.sub(
            r'f\s*\(\s*x\s*\)\s*=\s*là:\s*\n\s*([x0-9\^\{\}\+\-\s]+)',
            lambda m: f"$f(x) = \\frac{{2x}}{{{m.group(1).strip()}}}$ là: ",
            text
        )

        text = re.sub(
            r'f\s*′\s*\(\s*x\s*\)\s*=\s*\.\s*\n\s*([x0-9\^\{\}\+\-\s]+)',
            lambda m: f"$f'(x) = \\frac{{2x}}{{{m.group(1).strip()}}}$ ",
            text
        )

        # 5. Logarithm base broken onto next line: "log (x-1) < 3 là: \n 2" -> "$\log_{2}(x-1) < 3$ là:"
        text = re.sub(
            r'(?i)\blog\s*\(([^)]+)\)\s*<\s*(\d+)\s*là:\s*\n\s*(\d+)',
            r'$\\log_{\3}(\1) < \2$ là: ',
            text
        )

        # 6. Clean dangling broken fraction parts at end of options
        text = re.sub(r'(\[1;9\])\s*\n\s*2x', r'\1', text)
        text = re.sub(r'\n\s*2x\s*(?=\n|\Z)', '', text)

        return text

    @classmethod
    def extract_pdf_content(cls, file_bytes: bytes) -> Tuple[str, List[List[List[str]]], List[Dict[str, Any]]]:
        """
        Extract text and tables from PDF file bytes.
        Uses marker-pdf with TORCH_DEVICE (read from environment) if available to retain LaTeX math formulas.
        Falls back to pdfplumber if marker-pdf is not installed or fails.
        """
        torch_device = os.environ.get("TORCH_DEVICE", "cpu")
        os.environ["TORCH_DEVICE"] = torch_device

        full_text_lines = []
        tables_data = []
        inline_images = []

        # Try using marker-pdf for LaTeX math formula extraction.
        # Disabled via ENABLE_MARKER_PDF=0 (e.g. in the memory-limited Docker container,
        # where importing marker pulls in torch and can OOM the process).
        marker_enabled = os.environ.get("ENABLE_MARKER_PDF", "1") != "0"
        try:
            if not marker_enabled:
                raise ImportError("marker-pdf disabled via ENABLE_MARKER_PDF=0")
            import tempfile
            from marker.convert import convert_single_pdf
            from marker.models import load_all_models

            models = load_all_models()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                tmp_pdf.write(file_bytes)
                tmp_pdf_path = tmp_pdf.name

            try:
                full_text, out_meta, images = convert_single_pdf(tmp_pdf_path, models)
                if full_text and full_text.strip():
                    full_text_lines.append(full_text.strip())
            finally:
                if os.path.exists(tmp_pdf_path):
                    os.remove(tmp_pdf_path)
        except Exception:
            # Fallback to pdfplumber text extraction
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        normalized = cls.normalize_extracted_text(text.strip())
                        full_text_lines.append(normalized)

        # Extract tables using pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for tbl in tables:
                    clean_tbl = [[str(cell or '').strip() for cell in row] for row in tbl if row]
                    if clean_tbl:
                        tables_data.append(clean_tbl)

        full_text = "\n".join(full_text_lines)
        return full_text, tables_data, inline_images


    # Exam header patterns ("ĐỀ SỐ 1", "MÃ ĐỀ 0121", "ĐỀ 2", ...) detected near the top of a page
    EXAM_HEADER_PATTERNS = [
        re.compile(r"MÃ\s*ĐỀ\s*[:#]?\s*(\d[\w]{0,3})", re.IGNORECASE),
        re.compile(r"ĐỀ\s*SỐ\s*[:#]?\s*(\d[\w]{0,3})", re.IGNORECASE),
        re.compile(r"\bĐỀ\s+(\d[\w]{0,3})", re.IGNORECASE),
    ]

    @classmethod
    def parse_document(
        cls,
        file_bytes: bytes,
        filename: str,
        answer_file_bytes: Optional[bytes] = None,
        answer_filename: Optional[str] = None,
        test_code: Optional[str] = None
    ) -> ParseResult:
        """
        Main entry point to parse question document and optional separate answer key.

        A PDF may contain multiple exams (đề): the file is split into exam sections by
        header lines, each section is parsed with the AI Vision provider chain
        (SCAN_AI_PROVIDER first, then the other provider as automatic fallback) or the
        local parser, and questions are tagged with their exam label. Figures attached
        to questions are cropped from the page renders and stored via QuestionImageService.
        """
        is_pdf = filename.lower().endswith(".pdf")

        if not is_pdf:
            return cls._parse_local_document(
                file_bytes, filename, pages=None,
                answer_file_bytes=answer_file_bytes,
                answer_filename=answer_filename, test_code=test_code,
            )

        sections = cls.detect_pdf_exam_sections(file_bytes)

        # Render all pages once (shared by the AI vision providers and image cropping);
        # skipped when the PDF cannot be read page-wise (sections carry pages=None)
        page_images: List[Any] = []
        if any(sec["pages"] is not None for sec in sections):
            try:
                from app.modules.exercise.services.gemini_vision_parser_service import GeminiVisionParserService
                page_images = GeminiVisionParserService.render_pdf_to_images(file_bytes)
            except Exception as e:
                logger.warning(f"Could not render PDF pages for vision OCR: {e}")

        all_questions: List[ParsedQuestion] = []
        all_errors: List[ParseError] = []

        for section in sections:
            pages: Optional[List[int]] = section["pages"]
            label: Optional[str] = section["label"]

            # Legacy path: PDF unreadable page-wise -> single whole-file call
            if pages is None:
                section_result: Optional[ParseResult] = None
                for provider_name, provider in cls.get_ai_vision_providers():
                    try:
                        logger.info(f"Using {provider_name} Vision API for PDF OCR (whole file)...")
                        ai_result = provider.parse_pdf_document(file_bytes, test_code=test_code)
                        if ai_result.questions:
                            merged = cls.merge_ai_result_with_answer_key(
                                ai_result, answer_file_bytes, answer_filename, test_code
                            )
                            section_result = merged if merged is not None else ai_result
                            break
                        logger.warning(f"{provider_name} OCR returned no questions ({ai_result.errors}). Trying next provider/local parser.")
                    except Exception as e:
                        logger.warning(f"{provider_name} Vision Parser error: {e}. Trying next provider/local parser.")
                if section_result is None or not section_result.questions:
                    local_result = cls._parse_local_document(
                        file_bytes, filename, pages=None,
                        answer_file_bytes=answer_file_bytes,
                        answer_filename=answer_filename, test_code=test_code,
                    )
                    if local_result.questions or section_result is None:
                        section_result = local_result
                if section_result is not None:
                    for q in section_result.questions:
                        q.exam_label = label
                    all_questions.extend(section_result.questions)
                    all_errors.extend(section_result.errors)
                continue

            # Chunk the section's pages: vision models cap output tokens, so a 3-4 page
            # section in one request gets its JSON truncated mid-string. Small chunks
            # (default 2 pages) keep responses within the output limit.
            max_pages = cls.get_max_pages_per_call()
            chunks = [pages[i:i + max_pages] for i in range(0, len(pages), max_pages)] or [pages]

            section_questions: List[ParsedQuestion] = []
            section_errors: List[ParseError] = []
            for chunk in chunks:
                images = [page_images[p - 1] for p in chunk if 1 <= p <= len(page_images)]
                if not images:
                    continue

                chunk_result: Optional[ParseResult] = None

                # 1. AI Vision OCR providers (config-driven order with automatic fallback)
                for provider_name, provider in cls.get_ai_vision_providers():
                    try:
                        logger.info(f"Using {provider_name} Vision API for PDF OCR (exam '{label or 'default'}', pages {chunk})...")
                        ai_result = provider.parse_images(images, page_numbers=chunk, test_code=test_code)
                        if ai_result.questions:
                            merged = cls.merge_ai_result_with_answer_key(
                                ai_result, answer_file_bytes, answer_filename, test_code
                            )
                            chunk_result = merged if merged is not None else ai_result
                            break
                        logger.warning(
                            f"{provider_name} OCR returned no questions ({ai_result.errors}). Trying next provider/local parser."
                        )
                    except Exception as e:
                        logger.warning(f"{provider_name} Vision Parser error: {e}. Trying next provider/local parser.")

                # 2. Local fallback parser (pdfplumber / docx + regex) for this chunk
                if chunk_result is None or not chunk_result.questions:
                    local_result = cls._parse_local_document(
                        file_bytes, filename, pages=chunk,
                        answer_file_bytes=answer_file_bytes,
                        answer_filename=answer_filename, test_code=test_code,
                    )
                    if local_result.questions or chunk_result is None:
                        chunk_result = local_result

                if chunk_result is not None:
                    section_questions.extend(chunk_result.questions)
                    section_errors.extend(chunk_result.errors)

            for q in section_questions:
                q.exam_label = label
            all_questions.extend(section_questions)
            all_errors.extend(section_errors)

        if not all_questions and any(sec["pages"] is not None for sec in sections):
            # Last resort: splitting into sections can break parsing (e.g. a header was
            # mis-detected) - retry the whole file as a single document, AI providers first.
            logger.warning("No questions from per-exam sections; retrying the whole file as one document.")
            for provider_name, provider in cls.get_ai_vision_providers():
                try:
                    ai_result = provider.parse_pdf_document(file_bytes, test_code=test_code)
                    if ai_result.questions:
                        merged = cls.merge_ai_result_with_answer_key(
                            ai_result, answer_file_bytes, answer_filename, test_code
                        )
                        whole = merged if merged is not None else ai_result
                        all_questions.extend(whole.questions)
                        all_errors.extend(whole.errors)
                        break
                except Exception as e:
                    logger.warning(f"{provider_name} whole-file OCR error: {e}")
            if not all_questions:
                whole_local = cls._parse_local_document(
                    file_bytes, filename, pages=None,
                    answer_file_bytes=answer_file_bytes,
                    answer_filename=answer_filename, test_code=test_code,
                )
                all_questions.extend(whole_local.questions)
                all_errors.extend(whole_local.errors)

        if not all_questions:
            errs = all_errors or [ParseError(question_number=None, message="No valid questions could be identified in the file.")]
            return ParseResult(questions=[], errors=errs)

        # 3. Crop and store figures attached to each question
        try:
            cls.attach_question_images(file_bytes, all_questions, sections=sections)
        except Exception as e:
            logger.warning(f"attach_question_images failed: {e}")

        # Non-fatal per-chunk warnings are returned alongside the questions; the router
        # only rejects the import (422) when no questions were parsed at all.
        return ParseResult(questions=all_questions, errors=all_errors)

    @classmethod
    def detect_pdf_exam_sections(cls, file_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Split a PDF into exam sections by detecting exam headers (e.g. 'ĐỀ SỐ 1', 'MÃ ĐỀ 101')
        near the top of pages. Returns [{'label': str|None, 'pages': [1-based pages]}];
        falls back to a single section covering all pages when no header is found.
        """
        sections: List[Dict[str, Any]] = []
        try:
            return cls._detect_pdf_exam_sections(file_bytes)
        except Exception as e:
            logger.warning(f"detect_pdf_exam_sections failed ({e}); treating file as a single exam.")
            return [{"label": None, "pages": None}]

    @classmethod
    def _detect_pdf_exam_sections(cls, file_bytes: bytes) -> List[Dict[str, Any]]:
        sections: List[Dict[str, Any]] = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            total_pages = len(pdf.pages)
            for idx, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                label = None
                # exam headers may sit anywhere on the page; only accept short lines or
                # lines that also look like a title block ("MÔN THI", "ĐỀ THI ...")
                for line in text.splitlines():
                    if len(line.strip()) > 120 and "MÔN" not in line.upper() and "THI" not in line.upper():
                        continue
                    for pattern in cls.EXAM_HEADER_PATTERNS:
                        m = pattern.search(line)
                        if m:
                            label = re.sub(r"\s+", " ", m.group(0)).strip().upper()
                            break
                    if label:
                        break
                if label and (not sections or sections[-1]["label"] != label):
                    sections.append({"label": label, "pages": [idx]})
                elif sections:
                    sections[-1]["pages"].append(idx)
                else:
                    sections.append({"label": None, "pages": [idx]})
        if not sections:
            sections = [{"label": None, "pages": list(range(1, total_pages + 1))}]
        return sections

    @classmethod
    def extract_pdf_content_pages(cls, file_bytes: bytes, pages: List[int]) -> Tuple[str, List[List[List[str]]], List[Dict[str, Any]]]:
        """Extract text and tables only from the given 1-based page numbers (pdfplumber)."""
        full_text_lines = []
        tables_data = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for p in pages:
                if 1 <= p <= len(pdf.pages):
                    page = pdf.pages[p - 1]
                    text = page.extract_text()
                    if text:
                        full_text_lines.append(cls.normalize_extracted_text(text.strip()))
                    for tbl in page.extract_tables():
                        clean_tbl = [[str(cell or '').strip() for cell in row] for row in tbl if row]
                        if clean_tbl:
                            tables_data.append(clean_tbl)
        return "\n".join(full_text_lines), tables_data, []

    @classmethod
    def _parse_local_document(
        cls,
        file_bytes: bytes,
        filename: str,
        pages: Optional[List[int]] = None,
        answer_file_bytes: Optional[bytes] = None,
        answer_filename: Optional[str] = None,
        test_code: Optional[str] = None
    ) -> ParseResult:
        """Local (non-AI) parser: pdfplumber/docx text extraction + regex question parsing."""
        is_pdf = filename.lower().endswith(".pdf")
        if is_pdf:
            if pages:
                q_text, q_tables, q_images = cls.extract_pdf_content_pages(file_bytes, pages)
            else:
                q_text, q_tables, q_images = cls.extract_pdf_content(file_bytes)
        else:
            q_text, q_tables, q_images = cls.extract_docx_content(file_bytes)

        if not q_text.strip() and not q_tables:
            return ParseResult(errors=[ParseError(question_number=None, message="File is empty or contains no readable text.")])

        ans_text = ""
        ans_tables = []
        if answer_file_bytes and answer_filename:
            if answer_filename.lower().endswith(".pdf"):
                ans_text, ans_tables, _ = cls.extract_pdf_content(answer_file_bytes)
            else:
                ans_text, ans_tables, _ = cls.extract_docx_content(answer_file_bytes)

        # Parse question blocks
        questions, q_errors = cls.parse_questions(q_text, q_images)
        if q_errors:
            return ParseResult(questions=[], errors=q_errors)

        if not questions:
            return ParseResult(errors=[ParseError(question_number=None, message="No valid questions could be identified in the file.")])

        # Combine main document tables and separate answer tables
        all_tables = q_tables + ans_tables
        all_ans_text = q_text + "\n" + ans_text

        # Parse answer keys
        parsed_answers = cls.parse_answer_keys(all_ans_text, all_tables, test_code)

        # Merge questions and answers
        merged_questions, merge_errors = cls.merge_questions_and_answers(questions, parsed_answers)
        if merge_errors:
            return ParseResult(questions=[], errors=merge_errors)

        return ParseResult(questions=merged_questions, errors=[])

    @classmethod
    def attach_question_images(cls, file_bytes: bytes, questions: List[ParsedQuestion],
                               sections: Optional[List[Dict[str, Any]]] = None, scale: float = 2.0) -> None:
        """
        Crop figure images for questions from the rendered PDF pages and store them via
        QuestionImageService. Uses vision-provided bboxes (q.image_page/q.image_bbox,
        normalized 0-1000) when available, otherwise assigns embedded PDF images to the
        nearest question header by vertical position (pdfplumber fallback).
        """
        from app.core.config import QUESTION_IMAGE_MAX_BYTES
        from app.modules.exercise.services.gemini_vision_parser_service import GeminiVisionParserService
        from app.modules.exercise.services.question_image_service import QuestionImageService

        try:
            page_images = GeminiVisionParserService.render_pdf_to_images(file_bytes, scale=scale)
        except Exception as e:
            logger.warning(f"attach_question_images: cannot render PDF pages: {e}")
            return
        if not page_images:
            return

        fallback_pages = None
        try:
            fallback_pages = cls._collect_page_images_and_question_marks(file_bytes)
        except Exception as e:
            logger.warning(f"attach_question_images: pdfplumber fallback unavailable: {e}")

        label_pages: Dict[Optional[str], List[int]] = {}
        if sections:
            for sec in sections:
                label_pages.setdefault(sec["label"], []).extend(sec["pages"])

        for q in questions:
            if q.image_url:
                continue
            page_no, bbox = q.image_page, q.image_bbox
            if not (bbox and page_no and 1 <= page_no <= len(page_images)):
                if fallback_pages:
                    cand = cls._find_fallback_bbox(fallback_pages, q, label_pages)
                    if cand:
                        page_no, bbox = cand
            if not (bbox and page_no and 1 <= page_no <= len(page_images)):
                continue
            try:
                img = page_images[page_no - 1]
                W, H = img.size
                x0 = max(0.0, min(1000.0, float(bbox[0]))) / 1000.0 * W
                y0 = max(0.0, min(1000.0, float(bbox[1]))) / 1000.0 * H
                x1 = max(0.0, min(1000.0, float(bbox[2]))) / 1000.0 * W
                y1 = max(0.0, min(1000.0, float(bbox[3]))) / 1000.0 * H
                if x1 - x0 < 20 or y1 - y0 < 20:
                    continue
                crop = img.crop((int(x0), int(y0), int(x1), int(y1))).convert("RGB")
                buf = io.BytesIO()
                crop.save(buf, format="PNG")
                data = buf.getvalue()
                while len(data) > QUESTION_IMAGE_MAX_BYTES and crop.width > 240 and crop.height > 240:
                    crop = crop.resize((crop.width // 2, crop.height // 2))
                    buf = io.BytesIO()
                    crop.save(buf, format="PNG")
                    data = buf.getvalue()
                if len(data) > QUESTION_IMAGE_MAX_BYTES:
                    continue
                meta = QuestionImageService.save_image_bytes(
                    data, ext="png",
                    original_name=f"question_{q.question_number}_page_{page_no}.png",
                    content_type="image/png",
                )
                q.image_url = meta["url"]
                q.image_metadata = meta
            except Exception as e:
                logger.warning(f"attach_question_images: failed for question {q.question_number}: {e}")

    @staticmethod
    def _collect_page_images_and_question_marks(file_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Per-page embedded images (normalized bbox 0-1000) and 'Câu n' header positions,
        used to assign figures to questions when the vision model returned no bboxes.
        """
        pages_info: List[Dict[str, Any]] = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for idx, page in enumerate(pdf.pages, 1):
                W, H = float(page.width), float(page.height)
                images = []
                for im in page.images:
                    try:
                        bbox = [float(im["x0"]) / W * 1000, float(im["top"]) / H * 1000,
                                float(im["x1"]) / W * 1000, float(im["bottom"]) / H * 1000]
                    except Exception:
                        continue
                    if (bbox[2] - bbox[0]) >= 15 and (bbox[3] - bbox[1]) >= 15:
                        images.append(bbox)
                qmarks: List[Tuple[int, float]] = []
                try:
                    for hit in page.search(r"Câu\s*\d+\s*[:.]"):
                        m = re.search(r"(\d+)", hit.get("text", "") or "")
                        if m:
                            qmarks.append((int(m.group(1)), float(hit["top"]) / H * 1000))
                except Exception:
                    pass
                pages_info.append({"page": idx, "images": images, "qmarks": sorted(qmarks, key=lambda t: t[1])})
        return pages_info

    @staticmethod
    def _find_fallback_bbox(pages_info: List[Dict[str, Any]], question: "ParsedQuestion",
                            label_pages: Optional[Dict[Optional[str], List[int]]] = None
                            ) -> Optional[Tuple[int, List[float]]]:
        """Assign an embedded page image to a question by vertical proximity of 'Câu n' headers."""
        allowed = None
        if label_pages is not None and question.exam_label in label_pages:
            allowed = set(label_pages[question.exam_label])
        for pinfo in pages_info:
            if allowed is not None and pinfo["page"] not in allowed:
                continue
            marks = pinfo["qmarks"]
            if not marks or not pinfo["images"]:
                continue
            idx = next((i for i, (num, _) in enumerate(marks) if num == question.question_number), None)
            if idx is None:
                continue
            q_top = marks[idx][1]
            next_top = marks[idx + 1][1] if idx + 1 < len(marks) else 1000.0
            candidates = []
            for bbox in pinfo["images"]:
                cy = (bbox[1] + bbox[3]) / 2
                if q_top - 120 <= cy < next_top:
                    candidates.append((cy, bbox))
            if candidates:
                candidates.sort(key=lambda t: abs(t[0] - q_top))
                return pinfo["page"], candidates[0][1]
        return None

    @staticmethod
    def get_max_pages_per_call() -> int:
        """Max PDF pages sent per vision API request (output-token caps truncate big responses).
        Override via SCAN_MAX_PAGES_PER_CALL (default 2)."""
        try:
            return max(1, int(os.environ.get("SCAN_MAX_PAGES_PER_CALL", "2")))
        except ValueError:
            return 2

    @staticmethod
    def get_ai_vision_providers() -> List[Tuple[str, Any]]:
        """
        Ordered list of available AI vision OCR providers for scanned exams.
        Primary provider is chosen via SCAN_AI_PROVIDER (default: 'mistral');
        the other configured provider is kept as automatic fallback.
        """
        if not os.environ.get("PYTEST_CURRENT_TEST"):
            if not any(k in os.environ for k in ("SCAN_AI_PROVIDER", "MISTRAL_API_KEY", "GEMINI_API_KEY")):
                from dotenv import load_dotenv, find_dotenv
                load_dotenv(find_dotenv())

        from app.modules.exercise.services.gemini_vision_parser_service import GeminiVisionParserService
        from app.modules.exercise.services.mistral_vision_parser_service import MistralVisionParserService

        primary = (os.environ.get("SCAN_AI_PROVIDER", "mistral") or "mistral").strip().lower()
        registry = {
            "mistral": ("Mistral", MistralVisionParserService),
            "gemini": ("Google Gemini", GeminiVisionParserService),
        }
        fallback = "gemini" if primary == "mistral" else "mistral"

        ordered: List[Tuple[str, Any]] = []
        for key in (primary, fallback):
            if key in registry and all(k != key for k, _ in ordered):
                name, service = registry[key]
                if service.is_available():
                    ordered.append((name, service))
        return ordered

    @classmethod
    def merge_ai_result_with_answer_key(
        cls,
        ai_result: ParseResult,
        answer_file_bytes: Optional[bytes],
        answer_filename: Optional[str],
        test_code: Optional[str] = None
    ) -> Optional[ParseResult]:
        """
        If a separate answer key file was uploaded, parse it and merge into the AI OCR result.
        Returns the merged ParseResult, or None if there is nothing to merge.
        """
        if not (answer_file_bytes and answer_filename):
            return None
        if answer_filename.lower().endswith(".pdf"):
            ans_text, ans_tables, _ = cls.extract_pdf_content(answer_file_bytes)
        else:
            ans_text, ans_tables, _ = cls.extract_docx_content(answer_file_bytes)

        if not (ans_text or ans_tables):
            return None
        parsed_answers = cls.parse_answer_keys(ans_text, ans_tables, test_code)
        if not parsed_answers:
            return None
        merged_q, _ = cls.merge_questions_and_answers(ai_result.questions, parsed_answers)
        if merged_q:
            return ParseResult(questions=merged_q, errors=[])
        return None

    @classmethod
    def parse_questions(cls, full_text: str, inline_images: List[Dict[str, Any]]) -> Tuple[List[ParsedQuestion], List[ParseError]]:
        """
        Regex parse question blocks for Part 1 (MCQ), Part 2 (True/False), Part 3 (Short Answer).
        """
        questions: List[ParsedQuestion] = []
        errors: List[ParseError] = []

        # Separate text into sections (PHẦN I, PHẦN II, PHẦN III)
        sections = cls.split_sections(full_text)

        img_idx = 0
        q_global_counter = 1

        for part_name, section_text in sections:
            # Split section text into question blocks starting with "Câu N." or "Câu N:"
            q_blocks = cls.split_question_blocks(section_text)
            
            for q_num, block_text in q_blocks:
                num = q_num if q_num is not None else q_global_counter
                q_global_counter = max(q_global_counter + 1, num + 1)

                # Extract difficulty tag
                difficulty = cls.extract_difficulty(block_text)
                clean_block = cls.strip_difficulty_tags(block_text)

                image_url = None
                if img_idx < len(inline_images):
                    image_url = inline_images[img_idx]["url"]
                    img_idx += 1

                if part_name == "Part1":
                    parsed_q, q_err = cls.parse_part1_question(num, clean_block, difficulty, image_url)
                elif part_name == "Part2":
                    parsed_q, q_err = cls.parse_part2_question(num, clean_block, difficulty, image_url)
                else:
                    parsed_q, q_err = cls.parse_part3_question(num, clean_block, difficulty, image_url)

                if q_err:
                    errors.append(q_err)
                elif parsed_q:
                    questions.append(parsed_q)

        return questions, errors

    @staticmethod
    def split_sections(text: str) -> List[Tuple[str, str]]:
        """
        Splits text into Part1, Part2, Part3 based on section headers (PHẦN I, PHẦN II, PHẦN III).
        """
        lines = text.splitlines()
        current_part = "Part1"
        section_buffers: Dict[str, List[str]] = {"Part1": [], "Part2": [], "Part3": []}

        for line in lines:
            normalized = line.strip().upper()
            if "PHẦN I." in normalized or "PHẦN I " in normalized or "PHẦN 1" in normalized or "PHẦN TRẮC NGHIỆM 4 LỰA CHỌN" in normalized:
                current_part = "Part1"
                continue
            elif "PHẦN II." in normalized or "PHẦN II " in normalized or "PHẦN 2" in normalized or "PHẦN TRẮC NGHIỆM ĐÚNG SAI" in normalized:
                current_part = "Part2"
                continue
            elif "PHẦN III." in normalized or "PHẦN III " in normalized or "PHẦN 3" in normalized or "PHẦN TRẢ LỜI NGẮN" in normalized:
                current_part = "Part3"
                continue

            section_buffers[current_part].append(line)

        result = []
        for part in ["Part1", "Part2", "Part3"]:
            buf = "\n".join(section_buffers[part]).strip()
            if buf:
                result.append((part, buf))
        if not result:
            result = [("Part1", text)]
        return result

    @staticmethod
    def split_question_blocks(section_text: str) -> List[Tuple[Optional[int], str]]:
        """
        Split section text into question blocks starting with "Câu N." or "Câu N:" or "Câu N ".
        """
        pattern = r"(?im)^(Câu\s+(\d+)[\.:/]?)"
        matches = list(re.finditer(pattern, section_text))

        blocks: List[Tuple[Optional[int], str]] = []
        if not matches:
            return blocks

        for i in range(len(matches)):
            start_pos = matches[i].start()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(section_text)
            block_content = section_text[start_pos:end_pos].strip()
            q_num = int(matches[i].group(2))
            blocks.append((q_num, block_content))

        return blocks

    @staticmethod
    def extract_difficulty(text: str) -> Optional[DifficultyEnum]:
        """Extract [NB], [TH], [VD] tags. Returns None if missing."""
        if re.search(r"\[NB\]|\[Nhận biết\]", text, re.IGNORECASE):
            return DifficultyEnum.NhanBiet
        elif re.search(r"\[TH\]|\[Thông hiểu\]", text, re.IGNORECASE):
            return DifficultyEnum.ThongHieu
        elif re.search(r"\[VD\]|\[Vận dụng\]", text, re.IGNORECASE):
            return DifficultyEnum.VanDung
        return None

    @staticmethod
    def strip_difficulty_tags(text: str) -> str:
        """Strip tags like [NB], [TH], [VD], [TN], [DS], [TL] from text."""
        return re.sub(r"\[(NB|TH|VD|TN|DS|TL|TU|Nhận biết|Thông hiểu|Vận dụng)\]", "", text, flags=re.IGNORECASE).strip()

    @staticmethod
    def convert_latex_to_markdown(raw_text: str) -> str:
        """
        Converts LaTeX math expressions ($...$ and $$...$$) into clean Markdown with Unicode symbols.
        E.g., $\vec{v} = \vec{a} + \vec{b}$ -> v⃗ = a⃗ + b⃗
              $\frac{a}{b}$ -> (a)/(b)
              $x^2$ -> x²
              $t_1$ -> t₁
        """
        if not raw_text:
            return raw_text

        math_pattern = r'(\$\$.*?\$\$|\$.*?\$)'

        sup_map = str.maketrans("0123456789+-=()n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿ")
        sub_map = str.maketrans({
            '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
            '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
            '+': '₊', '-': '₋', '=': '₌', '(': '₍', ')': '₎',
            'a': 'ₐ', 'e': 'ₑ', 'h': 'ₕ', 'i': 'ᵢ', 'j': 'ⱼ',
            'k': 'ₖ', 'l': 'ₗ', 'm': 'ₘ', 'n': 'ₙ', 'o': 'ₒ',
            'p': 'ₚ', 'r': 'ᵣ', 's': 'ₛ', 't': 'ₜ', 'u': 'ᵤ',
            'v': 'ᵥ', 'x': 'ₓ'
        })
        symbol_map = {
            r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ', r'\delta': 'δ', r'\pi': 'π',
            r'\theta': 'θ', r'\lambda': 'λ', r'\mu': 'μ', r'\sigma': 'σ', r'\omega': 'ω',
            r'\Delta': 'Δ', r'\Sigma': 'Σ', r'\Omega': 'Ω',
            r'\times': '×', r'\div': '÷', r'\pm': '±', r'\mp': '∓', r'\neq': '≠',
            r'\leq': '≤', r'\geq': '≥', r'\approx': '≈', r'\infty': '∞', r'\sqrt': '√'
        }

        def convert_math_block(match: re.Match) -> str:
            full_math = match.group(0)
            inner = full_math.strip('$').strip()

            # 1. Vectors \vec{x} -> x⃗
            inner = re.sub(r'\\vec\{([a-zA-Z0-9]+)\}', r'\1' + '\u20d7', inner)

            # 2. Fractions \frac{num}{den} -> (num)/(den)
            inner = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', inner)

            # 3. Superscripts x^{2} or x^2 -> x²
            inner = re.sub(r'\^\{?([0-9a-n]+)\}?', lambda m: m.group(1).translate(sup_map), inner)

            # 4. Subscripts x_{1} or x_1 -> x₁
            inner = re.sub(r'_\{?([0-9a-x]+)\}?', lambda m: m.group(1).translate(sub_map), inner)

            # 5. Greek & math symbols
            for latex_sym, unicode_sym in symbol_map.items():
                inner = inner.replace(latex_sym, unicode_sym)

            # Clean extra braces if any
            inner = re.sub(r'[{}]', '', inner)

            return inner

        return re.sub(math_pattern, convert_math_block, raw_text)

    @staticmethod
    def normalize_latex(latex_str: str) -> str:
        """
        Normalizes spacing, braces, and redundant operators in LaTeX formulas.
        E.g., \frac { 2 x } { x ^ { 2 } + 1 } -> \frac{2x}{x^{2}+1}
        """
        if not latex_str:
            return latex_str

        text = latex_str.strip()
        # Remove spaces around command braces: \command { -> \command{
        text = re.sub(r'\\([a-zA-Z]+)\s*\{', r'\\\1{', text)
        # Connect consecutive braces: } { -> }{
        text = re.sub(r'\}\s*\{', r'}{', text)
        # Remove spaces immediately inside braces
        text = re.sub(r'\{\s+', '{', text)
        text = re.sub(r'\s+\}', '}', text)
        # Remove spaces between single letters/digits inside braces: { 2 x } -> {2x}
        text = re.sub(r'\{([0-9a-zA-Z])\s+([0-9a-zA-Z])\}', r'{\1\2}', text)
        text = re.sub(r'\s*([=+\-])\s*', r' \1 ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @staticmethod
    def validate_latex(latex_str: str) -> Tuple[bool, Optional[str]]:
        """
        Validates LaTeX math syntax, brace matching, bracket balancing, and environment pairs.
        Returns (is_valid, error_message).
        """
        if not latex_str:
            return True, None

        # 1. Check brace matching {}
        brace_count = 0
        for char in latex_str:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count < 0:
                    return False, "Unmatched closing brace '}'."
        if brace_count != 0:
            return False, f"Unclosed brace '{{' (missing {brace_count} closing braces)."

        # 2. Check bracket matching []
        bracket_count = 0
        for char in latex_str:
            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                if bracket_count < 0:
                    return False, "Unmatched closing bracket ']'."
        if bracket_count != 0:
            return False, f"Unclosed bracket '[' (missing {bracket_count} closing brackets)."

        # 3. Check \begin{env} and \end{env} matching
        begins = re.findall(r'\\begin\{([^}]+)\}', latex_str)
        ends = re.findall(r'\\end\{([^}]+)\}', latex_str)
        if begins != ends:
            return False, f"Mismatched LaTeX environments: begins={begins}, ends={ends}."

        return True, None

    @classmethod
    def extract_segments(cls, raw_text: str) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Extracts structured segments (text and math) from raw question stem.
        Detects display ($$...$$) vs inline ($...$) math, normalizes & validates formulas,
        and determines if the question needs review.
        """
        if not raw_text:
            return [], False

        math_pattern = r'(\$\$[\s\S]*?\$\$|\$[^\$]+?\$)'
        segments: List[Dict[str, Any]] = []
        needs_review = False

        # Detect unclosed dollar delimiters
        single_dollars = len(re.findall(r'(?<!\$)\$(?!\$)', raw_text))
        if single_dollars % 2 != 0:
            needs_review = True

        last_pos = 0
        for match in re.finditer(math_pattern, raw_text):
            start, end = match.span()
            # Text before math block
            if start > last_pos:
                text_chunk = raw_text[last_pos:start]
                if text_chunk:
                    segments.append({
                        "type": "text",
                        "content": text_chunk
                    })

            full_math = match.group(0)
            is_display = full_math.startswith("$$")
            inner_math = full_math[2:-2] if is_display else full_math[1:-1]
            normalized = cls.normalize_latex(inner_math)
            is_valid, _ = cls.validate_latex(normalized)

            if not is_valid:
                needs_review = True

            segments.append({
                "type": "math",
                "latex": normalized,
                "display": is_display,
                "confidence": 0.98 if is_valid else 0.60
            })
            last_pos = end

        # Trailing text
        if last_pos < len(raw_text):
            trailing = raw_text[last_pos:]
            if trailing:
                segments.append({
                    "type": "text",
                    "content": trailing
                })

        return segments, needs_review

    @classmethod
    def parse_part1_question(cls, q_num: int, block_text: str, difficulty: Optional[DifficultyEnum], image_url: Optional[str]) -> Tuple[Optional[ParsedQuestion], Optional[ParseError]]:
        """Parse Part 1 (Multiple Choice 4 options)."""
        opt_pattern = r"(?im)(^[A-Da-d][\.:/\)]\s*|\s+[A-Da-d][\.:/\)]\s*)"
        parts = re.split(opt_pattern, block_text)

        if len(parts) < 3:
            return None, ParseError(question_number=q_num, message=f"Question {q_num} does not contain option choices A, B, C, D.")

        stem_match = re.match(r"(?i)^Câu\s+\d+[\.:/]?\s*", parts[0])
        stem = parts[0][stem_match.end():].strip() if stem_match else parts[0].strip()

        options: List[ParsedOption] = []
        i = 1
        disp_order = 0
        has_empty_option = False
        while i < len(parts):
            label = parts[i].strip()
            content = parts[i + 1].strip() if i + 1 < len(parts) else ""
            i += 2
            content = re.sub(r"\s+[A-Da-d][\.:/\)]$", "", content).strip()
            if not content:
                has_empty_option = True
            options.append(ParsedOption(
                content=f"{label} {content}".strip(),
                is_correct=False,
                display_order=disp_order
            ))
            disp_order += 1

        if len(options) < 2:
            return None, ParseError(question_number=q_num, message=f"Question {q_num} must have at least 2 option choices.")

        raw_stem = stem if stem else block_text
        content_latex = raw_stem
        content_markdown = cls.convert_latex_to_markdown(raw_stem)
        segments, needs_review = cls.extract_segments(raw_stem)
        
        if has_empty_option:
            needs_review = True
            confidence_score = 0.50
        else:
            confidence_score = 0.95 if not needs_review else 0.70

        return ParsedQuestion(
            question_number=q_num,
            part="Part1",
            question_type=QuestionTypeEnum.MultipleChoice,
            difficulty=difficulty,
            content=raw_stem,
            content_markdown=content_markdown,
            content_latex=content_latex,
            segments=segments,
            confidence_score=confidence_score,
            needs_review=needs_review,
            image_url=image_url,
            answer_options=options
        ), None

    @classmethod
    def parse_part2_question(cls, q_num: int, block_text: str, difficulty: Optional[DifficultyEnum], image_url: Optional[str]) -> Tuple[Optional[ParsedQuestion], Optional[ParseError]]:
        """Parse Part 2 (True/False 4 items a, b, c, d)."""
        opt_pattern = r"(?im)(^[A-Da-d][\.:/\)]\s*|\s+[A-Da-d][\.:/\)]\s*)"
        parts = re.split(opt_pattern, block_text)

        if len(parts) < 3:
            return None, ParseError(question_number=q_num, message=f"Question {q_num} (Part II True/False) does not contain items a, b, c, d.")

        stem_match = re.match(r"(?i)^Câu\s+\d+[\.:/]?\s*", parts[0])
        stem = parts[0][stem_match.end():].strip() if stem_match else parts[0].strip()

        options: List[ParsedOption] = []
        i = 1
        disp_order = 0
        while i < len(parts):
            label = parts[i].strip()
            content = parts[i + 1].strip() if i + 1 < len(parts) else ""
            i += 2
            if content:
                content = re.sub(r"\s+[A-Da-d][\.:/\)]$", "", content).strip()
                options.append(ParsedOption(
                    content=f"{label} {content}",
                    is_correct=False,
                    display_order=disp_order
                ))
                disp_order += 1

        if len(options) < 1:
            return None, ParseError(question_number=q_num, message=f"Question {q_num} (Part II) must have items a, b, c, d.")

        raw_stem = stem if stem else block_text
        content_latex = raw_stem
        content_markdown = cls.convert_latex_to_markdown(raw_stem)
        segments, needs_review = cls.extract_segments(raw_stem)
        confidence_score = 0.95 if not needs_review else 0.70

        return ParsedQuestion(
            question_number=q_num,
            part="Part2",
            question_type=QuestionTypeEnum.TrueFalse,
            difficulty=difficulty,
            content=raw_stem,
            content_markdown=content_markdown,
            content_latex=content_latex,
            segments=segments,
            confidence_score=confidence_score,
            needs_review=needs_review,
            image_url=image_url,
            answer_options=options
        ), None

    @classmethod
    def parse_part3_question(cls, q_num: int, block_text: str, difficulty: Optional[DifficultyEnum], image_url: Optional[str]) -> Tuple[Optional[ParsedQuestion], Optional[ParseError]]:
        """Parse Part 3 (Short Answer)."""
        stem_match = re.match(r"(?i)^Câu\s+\d+[\.:/]?\s*", block_text)
        stem = block_text[stem_match.end():].strip() if stem_match else block_text.strip()

        raw_stem = stem if stem else block_text
        content_latex = raw_stem
        content_markdown = cls.convert_latex_to_markdown(raw_stem)
        segments, needs_review = cls.extract_segments(raw_stem)
        confidence_score = 0.95 if not needs_review else 0.70

        return ParsedQuestion(
            question_number=q_num,
            part="Part3",
            question_type=QuestionTypeEnum.ShortAnswer,
            difficulty=difficulty,
            content=raw_stem,
            content_markdown=content_markdown,
            content_latex=content_latex,
            segments=segments,
            confidence_score=confidence_score,
            needs_review=needs_review,
            image_url=image_url,
            answer_options=[]
        ), None

    @classmethod
    def parse_answer_keys(
        cls,
        full_text: str,
        tables: List[List[List[str]]],
        target_test_code: Optional[str] = None
    ) -> Dict[int, Any]:
        """
        Parse Answer Keys from:
        - Format 1: Multi-Test Code Table Matrix (`Câu` | `Mã đề 0121` | `Mã đề 0122`...)
        - Format 2: Single Test Code Table (`Câu` | `Đáp án`)
        - Format 3: Multi-pair Grid Table (`Câu` | `ĐA` | `Câu` | `ĐA`...)
        - Format 4: True/False Table Matrix (`Câu` | `a)` | `b)` | `c)` | `d)`)
        - Format 5: Text List Format (`1. A`, `1. a) Đ, b) S...`, `1. 450`)
        Returns dictionary mapping q_num -> answer_data.
        """
        answers: Dict[int, Any] = {}

        # 1. Try parsing tables
        for tbl in tables:
            if not tbl or len(tbl) < 2:
                continue
            header = [cell.strip() for cell in tbl[0]]

            # Sub-case A: True/False table header e.g. ["Câu", "a)", "b)", "c)", "d)"] or ["Câu", "a", "b", "c", "d"]
            labels = [re.sub(r"[^a-d]", "", h.lower()) for h in header[1:5]] if len(header) >= 5 else []
            if labels == ["a", "b", "c", "d"]:
                for row in tbl[1:]:
                    if not row or not row[0].strip():
                        continue
                    q_num_match = re.search(r"\d+", row[0].strip())
                    if q_num_match:
                        q_num = int(q_num_match.group(0))
                        tf_dict = {}
                        for idx, col_name in enumerate(['a', 'b', 'c', 'd'], start=1):
                            if len(row) > idx:
                                val = row[idx].strip()
                                is_true = val.upper().startswith(("Đ", "T", "1"))
                                tf_dict[col_name] = is_true
                        answers[q_num] = tf_dict
                continue

            # Check if header contains "CÂU" or "STT"
            q_col_count = sum(1 for h in header if "CÂU" in h.upper() or "STT" in h.upper())

            # Sub-case B: Multi-pair Column Table e.g. ["Câu", "ĐA", "Câu", "ĐA", ...]
            if q_col_count >= 2 or (len(header) >= 4 and ("CÂU" in header[0].upper() or "STT" in header[0].upper()) and ("CÂU" in header[2].upper() or "STT" in header[2].upper() or ("ĐA" in header[1].upper() and "ĐA" in header[3].upper()))):
                for row in tbl[1:]:
                    for c in range(0, len(row) - 1, 2):
                        q_str = row[c].strip()
                        ans_val = row[c + 1].strip()
                        q_num_match = re.search(r"\d+", q_str)
                        if q_num_match and ans_val:
                            q_num = int(q_num_match.group(0))
                            answers[q_num] = cls.parse_single_answer_cell(ans_val)
                continue

            # Sub-case C: Standard Single-Column or Multi-Test Code Table Matrix
            if len(header) >= 2 and ("CÂU" in header[0].upper() or "STT" in header[0].upper()):
                target_col_idx = -1
                if target_test_code:
                    for idx, h_text in enumerate(header[1:], start=1):
                        if target_test_code in h_text:
                            target_col_idx = idx
                            break

                if target_col_idx == -1:
                    target_col_idx = 1  # Default to first answer column

                # Iterate rows
                for row in tbl[1:]:
                    if len(row) > target_col_idx:
                        q_str = row[0].strip()
                        ans_val = row[target_col_idx].strip()
                        q_num_match = re.search(r"\d+", q_str)
                        if q_num_match and ans_val:
                            q_num = int(q_num_match.group(0))
                            answers[q_num] = cls.parse_single_answer_cell(ans_val)
                continue

            # Sub-case D: Fallback table scanning without standard header
            for row in tbl:
                for c in range(0, len(row) - 1, 2):
                    q_str = row[c].strip()
                    ans_val = row[c + 1].strip()
                    q_num_match = re.match(r"^(?:Câu\s+)?(\d+)[\.:/]?$", q_str, re.IGNORECASE)
                    if q_num_match and ans_val:
                        q_num = int(q_num_match.group(1))
                        if q_num not in answers:
                            answers[q_num] = cls.parse_single_answer_cell(ans_val)

        # 2. Try parsing text list format (Format 5) if missing answers
        lines = full_text.splitlines()
        for line in lines:
            line_str = line.strip()
            # Match Part 1: "1. A" or "Câu 1: A" or "1.A"
            m1 = re.match(r"^(?:Câu\s+)?(\d+)[\.:/]\s*([A-Da-d])$", line_str, re.IGNORECASE)
            if m1:
                q_num = int(m1.group(1))
                if q_num not in answers:
                    answers[q_num] = m1.group(2).upper()
                continue

            # Match Part 2: "1. a) Đ, b) S, c) Đ, d) S" or "1. a) Đúng, b) Sai..."
            m2 = re.match(r"^(?:Câu\s+)?(\d+)[\.:/]\s*(a[\.:\)].*)$", line_str, re.IGNORECASE)
            if m2:
                q_num = int(m2.group(1))
                if q_num not in answers:
                    answers[q_num] = cls.parse_single_answer_cell(m2.group(2))
                continue

            # Match Part 3: "1. 450" or "Câu 1: 0,66" or "1. Đáp án: 450"
            m3 = re.match(r"^(?:Câu\s+)?(\d+)[\.:/]\s*(?:Đáp án:\s*)?([-\d\.,]+)$", line_str, re.IGNORECASE)
            if m3:
                q_num = int(m3.group(1))
                if q_num not in answers:
                    answers[q_num] = m3.group(2)

        return answers

    @staticmethod
    def parse_single_answer_cell(val: str) -> Any:
        """Parse string inside an answer cell (e.g. 'A', 'a) Đúng, b) Sai...', '450')."""
        val_clean = val.strip()
        # Single choice letter (Part 1)
        if len(val_clean) == 1 and val_clean.upper() in ["A", "B", "C", "D"]:
            return val_clean.upper()

        # True/False sub-items (Part 2) e.g. "a) Sai \n b) Sai \n c) Đúng \n d) Đúng"
        tf_dict = {}
        tf_matches = re.findall(r"([a-d])[\)\.:/]?\s*(Đúng|Sai|Đ|S|True|False)", val_clean, re.IGNORECASE)
        if tf_matches:
            for item_label, item_stat in tf_matches:
                item_label_clean = item_label.lower()
                is_true = item_stat.upper().startswith(("Đ", "T"))
                tf_dict[item_label_clean] = is_true
            return tf_dict

        # Short answer value (Part 3)
        return val_clean

    @classmethod
    def merge_questions_and_answers(
        cls,
        questions: List[ParsedQuestion],
        answers: Dict[int, Any]
    ) -> Tuple[List[ParsedQuestion], List[ParseError]]:
        """Combine parsed questions with parsed answers and perform all-or-nothing validation."""
        errors: List[ParseError] = []
        result_questions: List[ParsedQuestion] = []

        for q in questions:
            num = q.question_number
            ans = answers.get(num)

            if ans is None:
                errors.append(ParseError(question_number=num, message=f"Missing answer key for question {num}."))
                continue

            if q.question_type == QuestionTypeEnum.MultipleChoice:
                letter = str(ans).upper()
                matched = False
                for opt in q.answer_options:
                    if opt.content.strip().upper().startswith(letter):
                        opt.is_correct = True
                        matched = True
                        break
                if not matched and q.answer_options:
                    idx_map = {"A": 0, "B": 1, "C": 2, "D": 3}
                    if letter in idx_map and idx_map[letter] < len(q.answer_options):
                        q.answer_options[idx_map[letter]].is_correct = True
                        matched = True

                if not matched:
                    errors.append(ParseError(question_number=num, message=f"Answer '{letter}' for question {num} does not match any choice."))
                else:
                    result_questions.append(q)

            elif q.question_type == QuestionTypeEnum.TrueFalse:
                if not isinstance(ans, dict) or not ans:
                    errors.append(ParseError(question_number=num, message=f"Invalid True/False answer key structure for question {num}."))
                    continue

                for idx, opt in enumerate(q.answer_options):
                    opt_label = chr(ord('a') + idx)
                    for key in ['a', 'b', 'c', 'd']:
                        if opt.content.strip().lower().startswith(key):
                            opt_label = key
                            break

                    if opt_label in ans:
                        opt.is_correct = ans[opt_label]

                result_questions.append(q)

            elif q.question_type == QuestionTypeEnum.ShortAnswer:
                q.correct_answer = str(ans)
                result_questions.append(q)

        return result_questions, errors
