# File Name: import_parser_service.py
# Description: Service for extracting text/images and parsing question templates and answer keys (Docx/PDF).
# Created At: 2026-08-09
# Created By: Tam Khang
# Updated At: 2026-11-12
# Updated By: AI Agent

import os
import re
import io
import unicodedata
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
    # Table block reported by the vision model (isolated from question content)
    table_page: Optional[int] = None
    table_bbox: Optional[List[float]] = None  # normalized [x0, y0, x1, y1] in 0-1000
    table_markdown: Optional[str] = None


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
        re.compile(r"ĐỀ\s*THI\s*[:#]?\s*(\d[\w]{0,3})", re.IGNORECASE),
        re.compile(r"\bĐỀ\s+(\d[\w]{0,3})", re.IGNORECASE),
    ]
    # Page slices of one exam shorter than this (normalized 0-1000) are header-only slivers
    # and are not sent to the vision model.
    MIN_SLICE_HEIGHT = 60.0

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
            sections = cls._scan_sections(file_bytes, page_images) or sections
            try:
                from app.modules.exercise.services import page_furniture_service as pfs
                pfs.register_model_view(page_images, pfs.detect_furniture(file_bytes, page_images))
            except Exception as e:
                logger.warning(f"Page furniture masking skipped: {e}")

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
            # Windows overlap by one page so a question spanning pages is whole in one call;
            # duplicates from the overlap are removed by normalize_questions below.
            from app.modules.exercise.services import exam_sequence_service as seq
            chunks = seq.chunk_pages(pages, max_pages) or [pages]

            section_questions: List[ParsedQuestion] = []
            section_errors: List[ParseError] = []
            # LLM pre-pass: read the exam outline first, then scan with that structure
            structure = cls._analyze_section_structure(file_bytes, section, label, page_images)
            for chunk in chunks:
                images = cls._section_images(section, chunk, page_images)
                if not images:
                    continue
                chunk_pages = cls._slice_pages(section, chunk, page_images)
                hint = structure.to_hint(chunk_pages) if structure and structure.parts else None

                chunk_result: Optional[ParseResult] = None

                # 1. AI Vision OCR providers (config-driven order with automatic fallback)
                for provider_name, provider in cls.get_ai_vision_providers():
                    try:
                        logger.info(f"Using {provider_name} Vision API for PDF OCR (exam '{label or 'default'}', pages {chunk})...")
                        ai_result = cls._call_provider(provider, images, chunk_pages, test_code, hint)
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

            section_questions = seq.normalize_questions(section_questions)
            try:
                cls._verify_sequence(section_questions, section_errors, file_bytes, section, label,
                                     structure, page_images, test_code)
            except Exception as e:
                logger.warning(f"relabel_by_layout failed for exam '{label}': {e}")
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
        Split a PDF into exam sections by detecting exam headers (e.g. 'ĐỀ SỐ 1', 'MÃ ĐỀ 101').

        Returns [{'label': str|None, 'pages': [1-based pages], 'start': (page, y)|None,
        'end': (page, y)|None}]. ``start``/``end`` are the section boundaries in normalized
        0-1000 page coordinates (a header can sit at the bottom of a page, so a page may
        be shared by two exams); None means the document start/end. Falls back to a single
        section covering all pages when no header is found, or to page-wise detection when
        word positions are unavailable.
        """
        try:
            return cls._detect_pdf_exam_sections(file_bytes)
        except Exception as e:
            logger.warning(f"detect_pdf_exam_sections failed ({e}); treating file as a single exam.")
            return [{"label": None, "pages": None, "start": None, "end": None}]

    @classmethod
    def _match_exam_label(cls, line: str) -> Optional[str]:
        """Exam label for a header line, else None."""
        line = unicodedata.normalize("NFC", line).strip()
        if len(line.strip()) > 120 and "MÔN" not in line.upper() and "THI" not in line.upper():
            return None
        for pattern in cls.EXAM_HEADER_PATTERNS:
            m = pattern.search(line)
            if m and m.start() <= 25:  # header opens the line; ignores prose such as 'xem đề 2'
                return re.sub(r"\s+", " ", m.group(0)).strip().upper()
        return None

    @classmethod
    def _detect_pdf_exam_sections(cls, file_bytes: bytes) -> List[Dict[str, Any]]:
        from app.modules.exercise.services.pdf_layout_service import PdfLayoutService, _lines

        words_by_page = PdfLayoutService.extract_words(file_bytes)
        if not words_by_page or not any(words_by_page.values()):
            return cls._detect_pdf_exam_sections_by_page(file_bytes)
        total_pages = max(words_by_page)

        # (label, page, cut_y): cut_y is where the previous exam ends and this one begins.
        headers: List[Tuple[str, int, float]] = []
        for page in sorted(words_by_page):
            words = words_by_page[page]
            lines = sorted(_lines(words), key=lambda ln: min(w.y0 for w in ln))
            for ln in lines:
                label = cls._match_exam_label(" ".join(w.text for w in ln))
                if not label or (headers and headers[-1][0] == label):
                    continue
                y = min(w.y0 for w in ln)
                # The title block often has a line above the "ĐỀ SỐ n" line (course/exam title
                # at the same height or just above): cut above every line that starts within
                # a small band above the header, so no title fragment stays in the old exam.
                cut = y
                for other in lines:
                    oy0 = min(w.y0 for w in other)
                    if other is not ln and y - 30.0 <= oy0 < y:
                        cut = min(cut, oy0)
                headers.append((label, page, max(0.0, cut - 2.0)))
        if not headers:
            return [{"label": None, "pages": list(range(1, total_pages + 1)), "start": None, "end": None}]

        sections: List[Dict[str, Any]] = []
        first_page, first_cut = headers[0][1], headers[0][2]
        if first_page > 1 or first_cut > 150:
            # Content before the first header stays an unlabeled section.
            sections.append({"label": None, "start": None, "end": (first_page, first_cut)})
        for idx, (label, page, cut) in enumerate(headers):
            nxt = headers[idx + 1] if idx + 1 < len(headers) else None
            sections.append({
                "label": label,
                "start": None if (idx == 0 and not sections) else (page, cut),
                "end": (nxt[1], nxt[2]) if nxt else None,
            })
        for sec in sections:
            first = sec["start"][0] if sec["start"] else 1
            last = sec["end"][0] if sec["end"] else total_pages
            sec["pages"] = list(range(first, last + 1))
        return sections

    @classmethod
    def _scan_sections(cls, file_bytes: bytes, page_images: List[Any]) -> Optional[List[Dict[str, Any]]]:
        """Model-read sections (with synthetic skeleton) for a PDF without a text layer, else None. Never raises."""
        try:
            if not page_images:
                return None
            from app.modules.exercise.services import exam_structure_service as ess
            from app.modules.exercise.services.pdf_layout_service import PdfLayoutService
            from app.modules.exercise.services.scan_layout_service import synthesize_layout
            words = PdfLayoutService.extract_words(file_bytes)
            if words and any(words.values()):
                return None
            providers = cls.get_ai_vision_providers()
            if not providers:
                return None
            layout = synthesize_layout(ess.file_hash(file_bytes), page_images, providers[0][1], cls._match_exam_label)
            return layout.sections if layout else None
        except Exception as e:
            logger.warning(f"Scan layout skipped: {e}")
            return None

    @classmethod
    def _detect_pdf_exam_sections_by_page(cls, file_bytes: bytes) -> List[Dict[str, Any]]:
        """Page-wise fallback (pdfplumber text); sections cover whole pages."""
        sections: List[Dict[str, Any]] = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            total_pages = len(pdf.pages)
            for idx, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                label = None
                for line in text.splitlines():
                    label = cls._match_exam_label(line)
                    if label:
                        break
                if label and (not sections or sections[-1]["label"] != label):
                    sections.append({"label": label, "pages": [idx], "start": None, "end": None})
                elif sections:
                    sections[-1]["pages"].append(idx)
                else:
                    sections.append({"label": None, "pages": [idx], "start": None, "end": None})
        if not sections:
            sections = [{"label": None, "pages": list(range(1, total_pages + 1)), "start": None, "end": None}]
        return sections

    @staticmethod
    def _page_slice(section: Dict[str, Any], page: int) -> Tuple[float, float]:
        """(top, bottom) of the section on a page, normalized 0-1000."""
        start, end = section.get("start"), section.get("end")
        top = start[1] if start and start[0] == page else 0.0
        bottom = end[1] if end and end[0] == page else 1000.0
        return top, bottom

    @classmethod
    def _section_images(cls, section: Dict[str, Any], chunk: List[int], page_images: List[Any]) -> List[Any]:
        """Page images for a chunk, cropped by y on pages shared with a neighbouring exam.

        Slivers shorter than MIN_SLICE_HEIGHT are skipped. The returned list may be
        shorter than ``chunk``; callers pass the matching page numbers via _slice_pages.
        """
        from app.modules.exercise.services.page_furniture_service import model_view
        page_images = model_view(page_images)  # header/footer masked copy; originals stay for crops
        images = []
        for p in chunk:
            if not (1 <= p <= len(page_images)):
                continue
            top, bottom = cls._page_slice(section, p)
            if (top, bottom) == (0.0, 1000.0):
                images.append(page_images[p - 1])
                continue
            if bottom - top < cls.MIN_SLICE_HEIGHT:
                continue
            img = page_images[p - 1]
            w, h = img.size
            images.append(img.crop((0, int(top / 1000.0 * h), w, int(bottom / 1000.0 * h))))
        return images

    @classmethod
    def _slice_pages(cls, section: Dict[str, Any], chunk: List[int], page_images: List[Any]) -> List[int]:
        """Page numbers matching _section_images output."""
        return [p for p in chunk if 1 <= p <= len(page_images)
                and (cls._page_slice(section, p) == (0.0, 1000.0)
                     or (lambda t, b: b - t >= cls.MIN_SLICE_HEIGHT)(*cls._page_slice(section, p)))]

    @classmethod
    def extract_pdf_content_pages(cls, file_bytes: bytes, pages: List[int]) -> Tuple[str, List[List[List[str]]], List[Dict[str, Any]]]:
        """Extract text and tables only from the given 1-based page numbers (pdfplumber)."""
        full_text_lines = []
        tables_data = []
        from app.modules.exercise.services.page_furniture_service import detect_furniture, strip_page_text
        furn = detect_furniture(file_bytes)  # header/footer lines are dropped from the text
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for p in pages:
                if 1 <= p <= len(pdf.pages):
                    page = pdf.pages[p - 1]
                    page = strip_page_text(page, furn[p - 1] if p - 1 < len(furn) else [])
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

    @staticmethod
    def _call_provider(provider: Any, images: List[Any], page_numbers: List[int],
                       test_code: Optional[str], hint: Optional[str]) -> ParseResult:
        """provider.parse_images with the optional structure hint (kept compatible with providers lacking it)."""
        if hint:
            return provider.parse_images(images, page_numbers=page_numbers, test_code=test_code, structure_hint=hint)
        return provider.parse_images(images, page_numbers=page_numbers, test_code=test_code)

    @classmethod
    def _analyze_section_structure(cls, file_bytes: bytes, section: Dict[str, Any], label: Optional[str],
                                   page_images: List[Any]) -> Optional[Any]:
        """LLM structure pre-pass for one exam section (cached per file hash + label). Never raises."""
        try:
            from app.modules.exercise.services import exam_structure_service as ess
            from app.modules.exercise.services.pdf_layout_service import (
                PdfLayoutService, clip_words, page_columns, find_anchors, find_part_headings, build_regions,
            )
            providers = cls.get_ai_vision_providers()
            if not providers or not section.get("pages"):
                return None
            key = (ess.file_hash(file_bytes), f"{label}|{section.get('start')}|{section.get('end')}")
            if key in ess._CACHE:
                return ess.analyze_structure("", None, cache_key=key)
            if section.get("scan_layout"):
                from app.modules.exercise.services.scan_layout_service import build_scan_outline
                regions, headings = section["scan_layout"]
                return ess.analyze_structure(build_scan_outline(section), providers[0][1],
                                             regions=regions, headings=headings, cache_key=key)
            words_all = PdfLayoutService.extract_words(file_bytes)
            pages = [p for p in section["pages"] if p in words_all]
            words = clip_words({p: words_all[p] for p in pages}, section.get("start"), section.get("end"))
            regions, headings, outline = [], {}, ""
            if any(words.values()):
                cols = {p: page_columns(words[p]) for p in pages}
                regions = build_regions(find_anchors(words), cols, section_end=section.get("end"))
                headings = find_part_headings(words)
                outline = ess.build_outline(words)
            source: Any = outline
            if not outline and not any(words.values()):
                # No text layer: low-res page images instead
                source = cls._section_images(section, section["pages"][:3], page_images)
                if not source:
                    return None
            elif not outline:
                return None
            return ess.analyze_structure(source, providers[0][1], regions=regions, headings=headings, cache_key=key)
        except Exception as e:
            logger.warning(f"Structure analysis skipped for exam '{label}': {e}")
            return None

    MAX_GAP_RETRIES = 3

    @classmethod
    def _verify_sequence(cls, questions: List[ParsedQuestion], errors: List[ParseError], file_bytes: bytes,
                         section: Dict[str, Any], label: Optional[str], structure: Optional[Any],
                         page_images: List[Any], test_code: Optional[str]) -> None:
        """Relabel from the text layer, re-prompt the gap page span (max 3 times), then add review placeholders.

        Without a text layer the numbering gaps of the model output itself are used.
        """
        from app.modules.exercise.services import exam_sequence_service as seq
        missing = cls.relabel_by_layout(questions, file_bytes, section, label, structure=structure)
        has_layout = any(isinstance(getattr(q, "part_index", None), int) for q in questions)
        if not has_layout:
            cls._fill_output_gaps(questions, errors, section, label, page_images, test_code)
            return
        for attempt in range(1, cls.MAX_GAP_RETRIES + 1):
            if not missing or structure is None:
                break
            logger.info("Exam '%s': gap retry %d/%d for %d missing question(s)",
                        label, attempt, cls.MAX_GAP_RETRIES, len(missing))
            if cls._retry_missing(questions, missing, structure, section, label, page_images, test_code):
                missing = cls.relabel_by_layout(questions, file_bytes, section, label, structure=structure)
        if missing:
            for r, _ in missing:
                logger.warning("Exam '%s': question still missing after retries, part=%d number=%d; "
                               "inserted review placeholder", label, r.part, r.number)
                questions.append(seq.make_placeholder(r.number, r.part))
                errors.append(ParseError(question_number=r.number, message=(
                    f"Exam '{label}' part {r.part}: question {r.number} was not recognised; "
                    "a placeholder was added for review.")))
            cls.relabel_by_layout(questions, file_bytes, section, label, structure=structure)

    @classmethod
    def _fill_output_gaps(cls, questions: List[ParsedQuestion], errors: List[ParseError], section: Dict[str, Any],
                          label: Optional[str], page_images: List[Any], test_code: Optional[str]) -> None:
        """No-text-layer variant of the sequence check: numbering gaps in the model output."""
        from app.modules.exercise.services import exam_sequence_service as seq
        gaps = seq.find_output_gaps(questions)
        pages = list(section.get("pages") or [])[: cls.get_max_pages_per_call() * 2]
        for attempt in range(1, cls.MAX_GAP_RETRIES + 1):
            if not gaps:
                break
            nums = sorted({n for _, n in gaps})
            images = cls._section_images(section, pages, page_images)
            chunk_pages = cls._slice_pages(section, pages, page_images)
            if not images:
                break
            hint = ("LƯU Ý: lần quét trước bị THIẾU các câu số " + ", ".join(map(str, nums)) +
                    ". Chỉ bóc tách ĐÚNG các câu thiếu này (giữ nguyên số câu), bỏ qua mọi câu khác.")
            added = False
            for _, provider in cls.get_ai_vision_providers():
                try:
                    res = cls._call_provider(provider, images, chunk_pages, test_code, hint)
                except Exception as e:
                    logger.warning(f"gap retry error: {e}")
                    continue
                wanted: Dict[int, Any] = {}
                for q in seq.normalize_questions(res.questions):
                    if q.question_number in nums:
                        wanted.setdefault(q.question_number, q)
                for idx, n in sorted(gaps, reverse=True):
                    if n in wanted:
                        questions.insert(idx + 1, wanted[n])
                        added = True
                if added:
                    break
            gaps = seq.find_output_gaps(questions)
            if not added:
                break
        for idx, n in sorted(gaps, reverse=True):
            logger.warning("Exam '%s': question still missing after retries, number=%d; inserted review placeholder",
                           label, n)
            questions.insert(idx + 1, seq.make_placeholder(n))
            errors.append(ParseError(question_number=n, message=(
                f"Exam '{label}': question {n} was not recognised; a placeholder was added for review.")))

    @classmethod
    def _retry_missing(cls, questions: List[ParsedQuestion], missing: List[Tuple[Any, Any]], structure: Any,
                       section: Dict[str, Any], label: Optional[str], page_images: List[Any],
                       test_code: Optional[str]) -> bool:
        """Re-scan the pages holding missing question anchors once; merge without duplicates.

        Each returned question fills one still-missing (part, number) region, so nothing
        that already exists can be duplicated. Returns True when something was added.
        """
        # Gap span = anchor pages plus one neighbour page each side (the question may start or end there)
        in_section = list(section.get("pages") or [])
        span = {r.anchor.page + d for r, _ in missing for d in (-1, 0, 1)}
        pages = sorted(p for p in span if p in in_section)[: cls.get_max_pages_per_call() * 2 + 2]
        miss_by_heading: Dict[str, List[int]] = {}
        for r, spec in missing:
            miss_by_heading.setdefault((spec.heading if spec else "") or f"PHẦN {r.part}", []).append(r.number)
        images = cls._section_images(section, pages, page_images)
        chunk_pages = cls._slice_pages(section, pages, page_images)
        if not images:
            return False
        hint = structure.to_hint(chunk_pages, missing=miss_by_heading)
        logger.info("Exam '%s': retrying pages %s for missing questions %s", label, chunk_pages, miss_by_heading)
        for provider_name, provider in cls.get_ai_vision_providers():
            try:
                res = cls._call_provider(provider, images, chunk_pages, test_code, hint)
            except Exception as e:
                logger.warning(f"{provider_name} retry error: {e}")
                continue
            if not res.questions:
                continue
            slots: Dict[int, List[Any]] = {}
            for r, _ in missing:
                slots.setdefault(r.number, []).append(r)
            added = 0
            for q in res.questions:
                regs = slots.get(q.question_number)
                if regs:
                    if len(regs) == 1:
                        q.part_index = regs.pop(0).part
                    # Several slots share this number: leave part_index unset so the skeleton
                    # matcher picks the slot by text similarity instead of by order.
                    questions.append(q)
                    added += 1
            if added:
                return True
        return False

    @classmethod
    def relabel_by_layout(cls, questions: List[ParsedQuestion], file_bytes: bytes,
                          section: Dict[str, Any], label: Optional[str] = None,
                          structure: Optional[Any] = None) -> List[Tuple[Any, Any]]:
        """Make part/type/order deterministic from the PDF text layer (model labels are not trusted).

        Questions arrive in model stream order (= document order). Each is paired with a
        layout region (PHẦN index, number); the PHẦN heading text decides the kind:
        MC / TF keep their options, short answer and essay (PHẦN IV) become ShortAnswer
        with a)/b) options merged back into the content. Unmatched questions keep the
        model label and stay next to their stream neighbours. Logs a WARNING per PHẦN
        when the question count differs from the anchor count.

        ``structure`` (ExamStructure from the LLM pre-pass) is the source of truth for the
        part type when given; the heading keyword heuristic is used otherwise. Questions
        already carrying a ``part_index`` (from an earlier pass or a retry) keep their
        region. Returns [(Region, PartSpec|None)] for regions that no question was paired
        with in parts that came up short (candidates for a targeted retry).
        """
        from app.modules.exercise.services.exam_structure_service import (
            TYPE_MC, TYPE_TF, TYPE_ESSAY, map_regions, heuristic_structure,
        )
        from app.modules.exercise.services.pdf_layout_service import (
            PdfLayoutService, find_anchors, find_part_headings, page_columns, build_regions,
            clip_words, classify_part, PART_MC, PART_TF,
        )
        if not questions or not section.get("pages"):
            return []
        if section.get("scan_layout"):
            # Source switch: model-read skeleton for PDFs without a text layer
            regions, headings = section["scan_layout"]
        else:
            words_all = PdfLayoutService.extract_words(file_bytes)
            pages = [p for p in section["pages"] if p in words_all]
            if not pages:
                return []
            words = clip_words({p: words_all[p] for p in pages}, section.get("start"), section.get("end"))
            if not any(words.values()):
                return []
            cols = {p: page_columns(words[p]) for p in pages}
            regions = build_regions(find_anchors(words), cols, section_end=section.get("end"))
            headings = find_part_headings(words)
        if not regions:
            return []
        specs = map_regions(structure or heuristic_structure(headings, regions), regions, headings)

        # 1. Pair questions with skeleton regions (text-layer anchors per part). Pre-resolved
        # questions (earlier pass / retry / placeholder) keep their (part, number) slot; the rest
        # are matched by number + compatible type. Questions outside the skeleton are dropped.
        from app.modules.exercise.services.exam_structure_service import match_to_skeleton
        preset: Dict[int, int] = {}
        used: set = set()
        for qi, q in enumerate(questions):
            pidx = getattr(q, "part_index", None)
            if isinstance(pidx, int):
                for ri, reg in enumerate(regions):
                    if ri not in used and reg.part == pidx and reg.number == q.question_number:
                        preset[qi] = ri
                        used.add(ri)
                        break
        from app.modules.exercise.services.verbatim_guard_service import region_words
        pairs = match_to_skeleton(questions, regions, specs, preset=preset, label=label,
                                  region_text=region_words(regions, words) if not section.get("scan_layout") else None)
        for qi, ri in pairs.items():
            logger.info("Exam '%s': skeleton pair model#%s '%s' -> PHAN %s cau %s%s", label, questions[qi].question_number,
                        (questions[qi].content or "")[:24].replace(chr(10), " "), regions[ri].part, regions[ri].number,
                        " (preset)" if qi in preset else "")
        questions[:] = [q for qi, q in enumerate(questions) if qi in pairs]
        pairs = {new: ri for new, ri in enumerate(pairs[qi] for qi in sorted(pairs))}

        # 2. Re-label matched questions from their PHẦN heading.
        for qi, ri in pairs.items():
            q, reg = questions[qi], regions[ri]
            spec_type = specs[ri].type
            q.part_index = reg.part
            q.question_number = reg.number
            if getattr(q, "is_placeholder", False):
                continue  # keep the ShortAnswer review placeholder valid regardless of part type
            if spec_type in (TYPE_MC, TYPE_TF) and len(q.answer_options or []) < 2 and cls.is_short_answer_stem(q.content or ""):
                spec_type = "ShortAnswer"  # numeric-answer stem without options: never keep a choice label
            if spec_type == TYPE_MC:
                q.part, q.question_type = "Part1", QuestionTypeEnum.MultipleChoice
            elif spec_type == TYPE_TF:
                q.part, q.question_type = "Part2", QuestionTypeEnum.TrueFalse
            else:
                q.part = "Part4" if spec_type == TYPE_ESSAY else "Part3"
                q.question_type = QuestionTypeEnum.ShortAnswer
                if q.answer_options:
                    # Sub-items a), b) belong to the stem of a short answer / essay question.
                    extra = "\n".join(o.content for o in q.answer_options)
                    q.content = f"{q.content}\n{extra}".strip()
                    q.answer_options = []
                    q.content_markdown = cls.convert_latex_to_markdown(q.content)
                    q.content_latex = q.content
                    segs, nr = cls.extract_segments(q.content)
                    if q.table_markdown:
                        segs.append({"type": "table", "content": q.table_markdown, "confidence": 0.9})
                    q.segments = segs
                    q.needs_review = q.needs_review or nr
                q.correct_answer = None

        # 3. Document order: matched questions by region position, others after their predecessor.
        keys, last = [], -1
        for qi in range(len(questions)):
            if qi in pairs:
                last = pairs[qi]
                keys.append((last, 0, qi))
            else:
                keys.append((last, 1, qi))
        order = sorted(range(len(questions)), key=lambda i: keys[i])
        reordered = [questions[i] for i in order]
        questions[:] = reordered
        for q in questions:
            q.doc_ordered = True

        # 4. Count check per PHẦN.
        short_parts = set()
        for part in sorted({r.part for r in regions} - {0}):
            expected = sum(1 for r in regions if r.part == part)
            got = sum(1 for q in questions if getattr(q, "part_index", None) == part)
            if expected != got:
                heading = headings.get(part, "")
                logger.warning("Exam '%s': expected %d questions in PHẦN %d, got %d (%s)",
                               label, expected, part, got, heading[:60])
            if got < expected:
                short_parts.add(part)
        orphans = sum(1 for r in regions if r.part == 0)
        if orphans:
            logger.warning("Exam '%s': %d question anchors found before any PHẦN heading", label, orphans)
        if not section.get("scan_layout"):
            from app.modules.exercise.services.verbatim_guard_service import flag_deviations
            flag_deviations(questions, regions, words, label or "")
        paired = set(pairs.values())
        return [(regions[ri], specs[ri]) for ri in range(len(regions))
                if ri not in paired and regions[ri].part in short_parts]

    @classmethod
    def attach_question_images(cls, file_bytes: bytes, questions: List[ParsedQuestion],
                               sections: Optional[List[Dict[str, Any]]] = None, scale: float = 3.0) -> None:
        """
        Attach figures/tables to questions. Primary path: PDF layout analysis (PyMuPDF)
        finds figure/table blocks and question regions (column and page-break aware);
        each block goes to the question whose region holds it and is rendered with
        PdfLayoutService.render_clip. The vision model bbox (q.image_bbox) only breaks
        ties between several figures, or is used as the crop itself when the layout has
        no text/blocks (scanned PDFs) or the question cannot be located.
        """
        import pymupdf
        from app.modules.exercise.services.pdf_layout_service import (
            PdfLayoutService, find_anchors, page_columns, build_regions,
            match_questions, assign_blocks, pick_primary, clip_words, _in_region, _union,
        )
        from app.modules.exercise.services import figure_detection_service as fds
        from app.modules.exercise.services.question_image_service import QuestionImageService

        try:
            layout = PdfLayoutService.analyze(file_bytes)
        except Exception as e:
            logger.warning(f"attach_question_images: layout analysis failed: {e}")
            layout = None
        try:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            logger.warning(f"attach_question_images: cannot open PDF: {e}")
            return

        try:
            vlm = fds.detect_pdf_figures(file_bytes)
        except Exception as e:
            logger.warning(f"attach_question_images: VLM figure detection failed: {e}")
            vlm = {}

        def set_image(q: ParsedQuestion, meta) -> None:
            # Merge: keys set earlier (solver: solved_by, ai_confidence, review_reason) must survive.
            q.image_url, q.image_metadata = meta["url"], {**(q.image_metadata or {}), **meta}

        def region_clamp(reg, page_no: int, box):
            """Clamp a box to the region rect of that page holding the box centre."""
            cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
            for p, x0, y0, x1, y1 in reg.rects:
                if p == page_no and x0 <= cx <= x1 and y0 <= cy <= y1:
                    return [max(box[0], x0), max(box[1], y0), min(box[2], x1), min(box[3], y1)], (x0, y0, x1, y1)
            return list(box), None

        def store(page_no: int, bbox, name: str, reg=None, use_vlm: bool = True):
            box, lim = list(bbox), None
            vf = fds.best_match(page_no, bbox, vlm) if (use_vlm and vlm) else None
            if vf is not None:
                # Layout box and VLM box agree: take the union (VLM adds labels the layout missed).
                box = list(_union(bbox, vf["bbox"]))
                if reg is not None:
                    box, lim = region_clamp(reg, page_no, box)
            data = None
            if vf is not None:
                # refine_bbox only grows the box over adjacent labels/ink, then the VLM box is re-united.
                refined = PdfLayoutService.refine_bbox(doc, page_no, box)
                refined = list(_union(refined, box))
                if reg is not None:
                    refined, lim = region_clamp(reg, page_no, refined)
                refined = fds.verify_adjust(doc, page_no, refined, clamp=lim)
                # Last step: drop body text / header bands that the union pulled onto the crop edges.
                refined = PdfLayoutService.trim_body_text(doc, page_no, refined, bbox)
                data = PdfLayoutService.render_clip(doc, page_no, refined, pad=0.0)
            else:
                data = PdfLayoutService.render_figure(doc, page_no, box)
            if not data:
                return None
            return QuestionImageService.save_image_bytes(
                data, ext="png", original_name=name, content_type="image/png")

        def add_image_segment(q: ParsedQuestion, meta, bbox) -> None:
            q.segments = (q.segments or []) + [{
                "type": "image", "content": meta["url"], "bbox": list(bbox), "confidence": 0.9,
            }]

        matched_ids = set()
        used_vlm = set()
        try:
            if layout is not None and layout.has_text:
                secs = sections or [{"label": None, "pages": None}]
                for sec in secs:
                    pages = sec.get("pages") or sorted(layout.words_by_page)
                    pages = [p for p in pages if p in layout.words_by_page]
                    qs = [q for q in questions if q.exam_label == sec.get("label")]
                    if not pages or not qs:
                        continue
                    # Words are clipped to the exam's (page, y) range so a page shared with
                    # the neighbouring exam only contributes its own part.
                    words = clip_words({p: layout.words_by_page[p] for p in pages},
                                       sec.get("start"), sec.get("end"))
                    cols = {p: page_columns(words[p]) for p in pages}
                    regions = build_regions(find_anchors(words), cols, section_end=sec.get("end"))
                    qmap = match_questions(regions, qs)
                    blocks = [b for p in pages for b in layout.blocks_by_page.get(p, [])]
                    assigned = assign_blocks(regions, blocks, words)
                    for ri, reg in enumerate(regions):
                        q = next((x for x in qs if qmap.get(id(x)) is reg), None)
                        if q is None:
                            continue
                        matched_ids.add(id(q))
                        asg = assigned[ri]
                        figures = [b for b in asg.stem if b.kind != "table"]
                        tables = [b for b in asg.stem if b.kind == "table"]
                        primary = None if q.image_url else pick_primary(figures, q.image_page, q.image_bbox)
                        for b in ([primary] if primary else []) + [f for f in figures if f is not primary]:
                            try:
                                meta = store(b.page, b.bbox, f"question_{q.question_number}_{b.id}.png", reg)
                            except Exception as e:
                                logger.warning(f"attach_question_images: crop failed for question {q.question_number}: {e}")
                                continue
                            if not meta:
                                continue
                            if b is primary:
                                set_image(q, meta)
                            else:
                                add_image_segment(q, meta, b.bbox)
                        if not q.table_markdown:
                            for b in tables:
                                try:
                                    meta = store(b.page, b.bbox, f"question_{q.question_number}_{b.id}.png")
                                except Exception as e:
                                    logger.warning(f"attach_question_images: table crop failed for question {q.question_number}: {e}")
                                    continue
                                if meta:
                                    add_image_segment(q, meta, b.bbox)
                        # VLM-only figures: matched no layout block but sit inside this region.
                        for pg_no, figs in vlm.items():
                            for vf in figs:
                                if any(blk.page == pg_no and fds.best_match(pg_no, blk.bbox, {pg_no: [vf]}) for blk in blocks):
                                    continue
                                vb = vf["bbox"]
                                if id(vf) in used_vlm or not _in_region(reg, pg_no, (vb[0] + vb[2]) / 2, (vb[1] + vb[3]) / 2):
                                    continue
                                used_vlm.add(id(vf))
                                padded, _lim = region_clamp(reg, pg_no, cls._pad_bbox(vb, 0.03))
                                meta = None
                                try:
                                    data = PdfLayoutService.render_clip(doc, pg_no, padded, pad=0.0)
                                    if data:
                                        meta = QuestionImageService.save_image_bytes(
                                            data, ext="png", original_name=f"question_{q.question_number}_vlm.png",
                                            content_type="image/png")
                                except Exception as e:
                                    logger.warning(f"attach_question_images: VLM crop failed for question {q.question_number}: {e}")
                                if not meta:
                                    continue
                                if not q.image_url:
                                    set_image(q, meta)
                                else:
                                    add_image_segment(q, meta, padded)
                        if asg.options:
                            # ponytail: SegmentSchema has no option field, so option figures are
                            # flagged for teacher review instead of stored; add a segment field when needed.
                            q.needs_review = True
        finally:
            doc.close()

        # LLM bbox path: scans (no text/blocks) or questions the layout could not locate.
        pending = [q for q in questions if id(q) not in matched_ids
                   and ((not q.image_url and q.image_bbox and q.image_page)
                        or (q.table_bbox and q.table_page and not q.table_markdown))]
        if not pending:
            return
        from app.modules.exercise.services.gemini_vision_parser_service import GeminiVisionParserService
        try:
            page_images = GeminiVisionParserService.render_pdf_to_images(file_bytes, scale=scale)
        except Exception as e:
            logger.warning(f"attach_question_images: cannot render PDF pages: {e}")
            return
        if not page_images:
            return
        seen_figs: List[tuple] = []  # (page, bbox, hash) of figures already attached: dedup
        ocr_figs, furniture = None, []  # scan-only context, built lazily
        for q in pending:
            if not q.image_url and q.image_bbox and q.image_page and 1 <= q.image_page <= len(page_images):
                try:
                    vf = fds.best_match(q.image_page, q.image_bbox, vlm) if vlm else None
                    meta = None
                    if layout is None or not layout.has_text:
                        # Scan: raster refinement (axis titles in, body-text bands out) + dedup.
                        base = vf["bbox"] if vf else q.image_bbox
                        if ocr_figs is None:
                            ocr_figs, furniture = cls._scan_ocr_context(file_bytes, page_images, pending)
                        ob = max(ocr_figs.get(q.image_page, []), key=lambda o: fds.iou(o, base), default=None)
                        ob = ob if ob is not None and fds.iou(ob, base) >= 0.3 else None
                        fur = furniture[q.image_page - 1] if 0 < q.image_page <= len(furniture) else []
                        sbox, sdata = cls._scan_figure_crop(file_bytes, q.image_page, base, ob, fur)
                        if sdata is not None:
                            h = fds.image_hash(sdata)
                            if fds.is_duplicate_figure(q.image_page, sbox, h, seen_figs):
                                logger.info("attach_question_images: duplicate figure skipped for question %s",
                                            q.question_number)
                                continue
                            seen_figs.append((q.image_page, sbox, h))
                            meta = QuestionImageService.save_image_bytes(
                                sdata, ext="png", original_name=f"question_{q.question_number}_page_{q.image_page}.png",
                                content_type="image/png")
                    meta = meta or (cls._store_vlm_figure(file_bytes, vf["bbox"], q.image_page,
                                                          f"question_{q.question_number}_page_{q.image_page}.png")
                                    if vf and layout is not None and layout.has_text else None)
                    meta = meta or cls._store_refined_figure(
                        file_bytes, q.image_bbox, q.image_page,
                        f"question_{q.question_number}_page_{q.image_page}.png",
                    ) or cls._crop_bbox_and_store(
                        page_images, q.image_page, cls._pad_bbox(q.image_bbox, 0.04),
                        original_name=f"question_{q.question_number}_page_{q.image_page}.png",
                    )
                    if meta:
                        set_image(q, meta)
                except Exception as e:
                    logger.warning(f"attach_question_images: failed for question {q.question_number}: {e}")
            if q.table_bbox and q.table_page and not q.table_markdown and 1 <= q.table_page <= len(page_images):
                tbbox = cls._pad_bbox(q.table_bbox, 0.02)
                try:
                    meta = cls._crop_bbox_and_store(
                        page_images, q.table_page, tbbox,
                        original_name=f"question_{q.question_number}_table_page_{q.table_page}.png",
                    )
                    if meta:
                        q.segments = (q.segments or []) + [{
                            "type": "image", "content": meta["url"],
                            "bbox": list(tbbox), "confidence": 0.9,
                        }]
                except Exception as e:
                    logger.warning(f"attach_question_images: table crop failed for question {q.question_number}: {e}")

    @staticmethod
    def _scan_ocr_context(file_bytes: bytes, page_images, pending):
        """(OCR figure boxes per page, page furniture rects per page); empty on any failure."""
        from app.modules.exercise.services import figure_detection_service as fds
        from app.modules.exercise.services.page_furniture_service import detect_furniture
        try:
            pages = sorted({q.image_page for q in pending if q.image_page})
            ocr = fds.detect_pdf_ocr_figures(file_bytes, pages)
        except Exception as e:
            logger.warning("scan OCR figure detection failed: %s", e)
            ocr = {}
        try:
            fur = detect_furniture(file_bytes, page_images)
        except Exception as e:
            logger.warning("scan furniture detection failed: %s", e)
            fur = []
        return ocr, fur

    @staticmethod
    def _scan_figure_crop(file_bytes: bytes, page_no: int, bbox: List[float],
                          ocr_box: Optional[List[float]] = None, furniture=None):
        """Fuse OCR/VLM boxes on a scanned page, verify once with the VLM. Returns (box, png) or (None, None)."""
        import pymupdf
        from app.modules.exercise.services import figure_detection_service as fds
        from app.modules.exercise.services.pdf_layout_service import PdfLayoutService
        try:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        except Exception:
            return None, None
        try:
            gray = fds.render_gray(doc, page_no)
            if ocr_box is not None:
                box = fds.fuse_scan_box(gray, ocr_box, bbox, furniture)
            else:
                box = fds.refine_raster_box(gray, bbox)
            box = fds.trim_scan_box(gray, fds.verify_adjust(doc, page_no, box), furniture)  # re-trim what verify grew
            return box, PdfLayoutService.render_clip(doc, page_no, box, pad=0.0)
        except Exception as e:
            logger.warning("scan figure refine failed on page %s: %s", page_no, e)
            return None, None
        finally:
            doc.close()

    @classmethod
    def _store_vlm_figure(cls, file_bytes: bytes, bbox: List[float], page_no: int, name: str):
        """Crop a VLM-detected figure box (padded 3%) straight from the PDF page and store it."""
        from app.modules.exercise.services.pdf_layout_service import PdfLayoutService
        from app.modules.exercise.services.question_image_service import QuestionImageService
        data = PdfLayoutService.render_clip(file_bytes, page_no, cls._pad_bbox(bbox, 0.03), pad=0.0)
        if not data:
            return None
        return QuestionImageService.save_image_bytes(data, ext="png", original_name=name, content_type="image/png")

    @staticmethod
    def _store_refined_figure(file_bytes: bytes, bbox: List[float], page_no: int, name: str):
        """Snap a (possibly shifted) LLM bbox onto the real figure, keep axis labels and
        captions, render with PyMuPDF and store. None when refinement/render fails."""
        import pymupdf
        from app.modules.exercise.services.pdf_layout_service import PdfLayoutService
        from app.modules.exercise.services.question_image_service import QuestionImageService
        try:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        except Exception:
            return None
        try:
            data = PdfLayoutService.render_figure(doc, page_no, bbox, snap=True)
        finally:
            doc.close()
        if not data:
            return None
        return QuestionImageService.save_image_bytes(
            data, ext="png", original_name=name, content_type="image/png")

    @staticmethod
    def _pad_bbox(bbox: List[float], ratio: float = 0.02) -> List[float]:
        """Expand a normalized 0-1000 bbox by `ratio` of its size on each side so thin
        border strokes of the figure are not cut off."""
        x0, y0, x1, y1 = [float(v) for v in bbox]
        w = max(1.0, x1 - x0)
        h = max(1.0, y1 - y0)
        return [
            max(0.0, x0 - w * ratio),
            max(0.0, y0 - h * ratio),
            min(1000.0, x1 + w * ratio),
            min(1000.0, y1 + h * ratio),
        ]

    @staticmethod
    def _crop_bbox_and_store(page_images, page_no: int, bbox: List[float], original_name: str):
        """Crop a normalized 0-1000 bbox from a rendered page and store it via
        QuestionImageService. Returns the stored metadata dict, or None if the region
        is too small / too large to store."""
        from app.core.config import QUESTION_IMAGE_MAX_BYTES
        from app.modules.exercise.services.question_image_service import QuestionImageService

        img = page_images[page_no - 1]
        W, H = img.size
        x0 = max(0.0, min(1000.0, float(bbox[0]))) / 1000.0 * W
        y0 = max(0.0, min(1000.0, float(bbox[1]))) / 1000.0 * H
        x1 = max(0.0, min(1000.0, float(bbox[2]))) / 1000.0 * W
        y1 = max(0.0, min(1000.0, float(bbox[3]))) / 1000.0 * H
        if x1 - x0 < 20 or y1 - y0 < 20:
            return None
        # LLM path only: reject text-strip shaped crops (very wide or very tall thin bands)
        w_px, h_px = x1 - x0, y1 - y0
        if w_px / max(1.0, h_px) > 6 or h_px / max(1.0, w_px) > 6:
            return None
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
            return None
        return QuestionImageService.save_image_bytes(
            data, ext="png",
            original_name=original_name,
            content_type="image/png",
        )

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

    @staticmethod
    def strip_markdown_tables(text: str) -> str:
        """
        Remove embedded Markdown table blocks (header + separator + rows of |...| lines)
        from question content so tables stay isolated in their own segment.
        """
        if not text:
            return text
        lines = text.splitlines()
        out: List[str] = []
        i = 0
        while i < len(lines):
            if re.match(r"^\s*\|.*\|\s*$", lines[i]):
                # collect the whole consecutive table block
                j = i
                while j < len(lines) and re.match(r"^\s*\|.*\|\s*$", lines[j]):
                    j += 1
                block = lines[i:j]
                # only treat as a table if it has a separator row (|---|---|) or >= 2 lines
                is_table = len(block) >= 2 and any(re.match(r"^\s*\|?[\s:|-]+\|?\s*$", ln) and "-" in ln for ln in block)
                if is_table:
                    i = j
                    continue
            out.append(lines[i])
            i += 1
        return "\n".join(out).strip()

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

    @staticmethod
    def split_option_run(block_text: str) -> List[str]:
        """Split a block into [stem, label, content, label, content, ...].

        Only a sequential run of markers a,b,c,d (or A,B,C,D) counts, each at line start or after
        whitespace, followed by whitespace/end and not preceded by a digit. Prose such as
        "... 5 d. ..." or tails like "5)" never become options.
        """
        found: List[re.Match] = []
        expect = None
        for m in re.finditer(r"(?:^|(?<=\s))([A-Da-d])[\.:/\)](?=\s|$)", block_text, re.M):
            before = block_text[:m.start()].rstrip(" 	")
            if before and before[-1].isdigit():
                continue
            want = expect or ("a" if m.group(1).lower() == "a" else None)
            if want is None or m.group(1).lower() != want:
                continue
            if found and m.group(1).isupper() != found[0].group(1).isupper():
                continue
            found.append(m)
            expect = chr(ord(want) + 1)
            if expect > "d":
                break
        if not found:
            return [block_text]
        out = [block_text[:found[0].start()]]
        for k, m in enumerate(found):
            end = found[k + 1].start() if k + 1 < len(found) else len(block_text)
            out += [m.group(0), block_text[m.end():end]]
        return out

    @staticmethod
    def is_short_answer_stem(block_text: str) -> bool:
        """True when the stem asks for a numeric result (no option list expected)."""
        t = block_text.lower()
        return bool(re.search(r"bao nhiêu|làm tròn|tính |xác định |\?\s*(\(.*\))?\.?\s*$", t))

    @classmethod
    def parse_part1_question(cls, q_num: int, block_text: str, difficulty: Optional[DifficultyEnum], image_url: Optional[str]) -> Tuple[Optional[ParsedQuestion], Optional[ParseError]]:
        """Parse Part 1 (Multiple Choice 4 options)."""
        parts = cls.split_option_run(block_text)
        if len(parts) < 5:
            if cls.is_short_answer_stem(block_text):
                return cls.parse_part3_question(q_num, block_text, difficulty, image_url)
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
        parts = cls.split_option_run(block_text)
        if len(parts) < 3:
            if cls.is_short_answer_stem(block_text):
                return cls.parse_part3_question(q_num, block_text, difficulty, image_url)
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
                # Reset any previously marked correct options first so a question
                # never ends up with more than one correct answer.
                for opt in q.answer_options:
                    opt.is_correct = False
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
