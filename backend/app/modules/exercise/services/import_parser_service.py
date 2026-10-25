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


@dataclass
class ParseError:
    question_number: Optional[int]
    message: str


@dataclass
class ParseResult:
    questions: List[ParsedQuestion] = field(default_factory=list)
    errors: List[ParseError] = field(default_factory=list)


UPLOAD_DIR = os.path.join("uploads", "questions")


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
                image_url = f"/uploads/questions/{filename}"
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

        # Try using marker-pdf for LaTeX math formula extraction
        try:
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
        Integrates GeminiVisionParserService as top-priority AI OCR for PDFs with automatic fallback.
        """
        is_pdf = filename.lower().endswith(".pdf")

        # 1. Try Gemini Multimodal Vision API first if available and file is PDF
        if is_pdf:
            try:
                from app.modules.exercise.services.gemini_vision_parser_service import GeminiVisionParserService
                if GeminiVisionParserService.is_available():
                    logger.info("Using Google Gemini Multimodal Vision API for PDF OCR...")
                    gemini_result = GeminiVisionParserService.parse_pdf_document(file_bytes, test_code=test_code)
                    if gemini_result.questions and not gemini_result.errors:
                        # If a separate answer key file was uploaded, merge answer keys
                        if answer_file_bytes and answer_filename:
                            if answer_filename.lower().endswith(".pdf"):
                                ans_text, ans_tables, _ = cls.extract_pdf_content(answer_file_bytes)
                            else:
                                ans_text, ans_tables, _ = cls.extract_docx_content(answer_file_bytes)
                            
                            if ans_text or ans_tables:
                                parsed_answers = cls.parse_answer_keys(ans_text, ans_tables, test_code)
                                if parsed_answers:
                                    merged_q, merge_errs = cls.merge_questions_and_answers(gemini_result.questions, parsed_answers)
                                    if merged_q:
                                        return ParseResult(questions=merged_q, errors=[])

                        return gemini_result
                    else:
                        logger.warning(f"Gemini OCR did not return questions ({gemini_result.errors}). Falling back to local parser.")
            except Exception as e:
                logger.warning(f"Gemini Vision Parser encountered an error: {e}. Falling back to local parser.")

        # 2. Local Fallback Parser (pdfplumber / docx + regex)
        if is_pdf:
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
