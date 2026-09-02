# File Name: gemini_vision_parser_service.py
# Description: Service for extracting and parsing exam questions from PDF/Images using Google Gemini Multimodal Vision API.
# Created At: 2026-09-02
# Created By: Tam Khang
# Updated At: 2026-09-02
# Updated By: Tam Khang

import os
import io
import re
import json
import logging
from typing import List, Optional, Dict, Any, Tuple
from PIL import Image
import pypdfium2 as pdfium

from app.modules.exercise.schemas import QuestionTypeEnum, DifficultyEnum
from app.modules.exercise.services.import_parser_service import (
    ParsedQuestion, ParsedOption, ParseError, ParseResult
)

logger = logging.getLogger("smartlms.exercise.gemini_vision")

# Prompt for Vietnamese Math and Science exam OCR
GEMINI_SYSTEM_PROMPT = """Bạn là một chuyên gia số hóa đề thi Toán học và Khoa học tự nhiên của Bộ Giáo dục & Đào tạo Việt Nam.
Nhiệm vụ của bạn là đọc hình ảnh các trang đề thi và trích xuất TOÀN BỘ câu hỏi cùng các phương án lựa chọn thành định dạng JSON có cấu trúc chính xác tuyệt đối.

Quy tắc bóc tách bắt buộc:
1. TOÁN HỌC & LATEX:
   - Mọi công thức toán học, biểu thức đại số, phương trình, hàm số, bất đẳng thức, phân số, logarit, căn bậc hai, tích phân, giới hạn, vectơ, tọa độ điểm, góc, tập nghiệm khoảng đoạn PHẢI được viết chuẩn cú pháp LaTeX và bao bọc trong cặp dấu '$' cho công thức nội dòng (ví dụ: '$f(x) = \\frac{2x}{x^2+1}$', '$\\log_2(x-1) < 3$', '$A(1;-2;3)$', '$\\vec{n} = (2;1;-1)$', '$(1;9)$').
   - Tuyệt đối KHÔNG viết công thức toán dưới dạng text thô bị vỡ (ví dụ không viết 'x 3 - 3x 2 + 2' mà phải viết '$x^3 - 3x^2 + 2$').
   - Bảng biến thiên (nếu có) hãy chuyển đổi thành bảng Markdown Table hoặc LaTeX array biểu diễn các hàng $x$, $y'$, $y$ cùng các mũi tên $\\nearrow, \\searrow$.

2. PHÂN LOẠI CẤU TRÚC 3 PHẦN:
   - "Part1": Trắc nghiệm nhiều lựa chọn (MultipleChoice) gồm 4 phương án A, B, C, D.
   - "Part2": Trắc nghiệm Đúng/Sai (TrueFalse) gồm 1 câu dẫn và 4 ý a), b), c), d).
   - "Part3": Trắc nghiệm Trả lời ngắn (ShortAnswer) với đáp án là số hoặc biểu thức ngắn.

3. ĐỘ KHÓ (DIFFICULTY):
   - Nhận biết nhãn độ khó ở đầu câu: '[NB]' -> 'NhanBiet', '[TH]' -> 'ThongHieu', '[VD]' -> 'VanDung', '[VDC]' -> 'VanDungCao'.
4. THỨ TỰ CÂU HỎI (QUESTION ORDER):
   - BẮT BUỘC bóc tách và trả về danh sách `questions` được sắp xếp tăng dần theo đúng số thứ tự câu hỏi trong đề: Câu 1, Câu 2, Câu 3, ..., Câu N.
   - Không được đảo lộn thứ tự giữa các trang hoặc các cột.

5. CẤU TRÚC JSON ĐẦU RA (Bắt buộc trả về đúng format JSON này, không thêm markdown ticks bên ngoài):
{
  "questions": [
    {
      "question_number": 1,
      "part": "Part1",
      "question_type": "MultipleChoice",
      "difficulty": "NhanBiet",
      "content": "Cho hàm số $f(x) = x^3 - 3x^2 + 2$. Giá trị cực đại của hàm số là:",
      "content_markdown": "Cho hàm số $f(x) = x^3 - 3x^2 + 2$. Giá trị cực đại của hàm số là:",
      "content_latex": "$f(x) = x^3 - 3x^2 + 2$",
      "answer_options": [
        {"content": "$0$", "is_correct": false, "display_order": 0},
        {"content": "$2$", "is_correct": true, "display_order": 1},
        {"content": "$-2$", "is_correct": false, "display_order": 2},
        {"content": "$4$", "is_correct": false, "display_order": 3}
      ],
      "correct_answer": "B"
    }
  ]
}
"""


class GeminiVisionParserService:
    """
    Multimodal Vision Parser utilizing Google Gemini API (gemini-2.5-flash / gemini-1.5-flash)
    to perform deep mathematical OCR on exam document pages.
    """

    @staticmethod
    def get_api_key() -> Optional[str]:
        """Retrieve Gemini API Key from environment or .env file."""
        if not os.environ.get("PYTEST_CURRENT_TEST"):
            if "GEMINI_API_KEY" not in os.environ and "GOOGLE_API_KEY" not in os.environ and "GEMINI_KEY" not in os.environ:
                from dotenv import load_dotenv, find_dotenv
                load_dotenv(find_dotenv())
        return (
            os.environ.get("GEMINI_API_KEY") or
            os.environ.get("GOOGLE_API_KEY") or
            os.environ.get("GEMINI_KEY")
        )

    @staticmethod
    def get_model_name() -> str:
        """Retrieve configured model name or default to gemini-2.5-flash."""
        return os.environ.get("GEMINI_MODEL_NAME", "gemini-2.5-flash")

    @classmethod
    def is_available(cls) -> bool:
        """Check if Gemini API key is configured and libraries are present."""
        return bool(cls.get_api_key())

    @staticmethod
    def render_pdf_to_images(file_bytes: bytes, scale: float = 2.0) -> List[Image.Image]:
        """
        Renders pages of a PDF into high-resolution PIL Images using pypdfium2.
        """
        images = []
        try:
            pdf = pdfium.PdfDocument(file_bytes)
            for page in pdf:
                pil_image = page.render(scale=scale).to_pil()
                images.append(pil_image)
        except Exception as e:
            logger.error(f"Failed to render PDF pages: {e}")
            raise ValueError(f"Could not render PDF pages to images: {str(e)}")
        return images

    @classmethod
    def parse_pdf_document(
        cls,
        file_bytes: bytes,
        test_code: Optional[str] = None
    ) -> ParseResult:
        """
        Main entry point for parsing PDF exam document using Gemini Vision.
        """
        images = cls.render_pdf_to_images(file_bytes)
        if not images:
            return ParseResult(errors=[ParseError(question_number=None, message="PDF contains no renderable pages.")])

        return cls.parse_images_with_gemini(images, test_code=test_code)

    @classmethod
    def parse_images_with_gemini(
        cls,
        images: List[Image.Image],
        test_code: Optional[str] = None
    ) -> ParseResult:
        """
        Sends exam page images to Google Gemini Vision API and returns parsed structured questions.
        """
        api_key = cls.get_api_key()
        if not api_key:
            return ParseResult(errors=[ParseError(question_number=None, message="GEMINI_API_KEY is not configured.")])

        model_name = cls.get_model_name()

        try:
            # Initialize google-genai Client
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)

            contents: List[Any] = [GEMINI_SYSTEM_PROMPT]
            for idx, img in enumerate(images, 1):
                contents.append(f"--- TRANG {idx} CỦA ĐỀ THI ---")
                contents.append(img)

            contents.append("Hãy bóc tách toàn bộ các câu hỏi từ tất cả các trang trên và trả về kết quả JSON.")

            # Request structured JSON response with expanded token window
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    max_output_tokens=16384,
                    temperature=0.1,
                )
            )

            raw_json = response.text or "{}"
            return cls._process_gemini_json_response(raw_json)

        except Exception as e:
            logger.error(f"Gemini Vision API execution failed: {e}")
            return ParseResult(errors=[ParseError(question_number=None, message=f"Gemini Vision OCR error: {str(e)}")])

    @staticmethod
    def sanitize_json_latex_escapes(raw: str) -> str:
        """
        Sanitizes raw JSON string containing unescaped LaTeX backslashes in a single pass
        so that json.loads doesn't fail on \\frac, \\vec, \\log, \\mathbb, etc.
        """
        def fix_escape(match):
            full = match.group(0)
            esc_char = match.group(1)
            rest = match.group(2)
            
            if esc_char in ('"', '\\', '/'):
                return full
            if esc_char == 'n' and (not rest or not rest[0].isalpha()):
                return full
            if esc_char == 'u' and len(rest) >= 4 and re.match(r'^[0-9a-fA-F]{4}', rest):
                return full
            if esc_char in ('r', 't', 'b', 'f') and (not rest or not rest[0].isalpha()):
                return full
                
            return '\\\\' + esc_char + rest

        return re.sub(r'\\([a-zA-Z0-9"\\/])([a-zA-Z]*)', fix_escape, raw)

    @classmethod
    def _process_gemini_json_response(cls, raw_json_str: str) -> ParseResult:
        """
        Parses raw JSON string from Gemini, auto-repairs any token-truncated JSON,
        and builds sorted List[ParsedQuestion].
        """
        clean_text = raw_json_str.strip()

        # Extract JSON block between ```json ... ``` or outermost { ... }
        match_fenced = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', clean_text)
        if match_fenced:
            clean_text = match_fenced.group(1).strip()
        else:
            match_braces = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', clean_text)
            if match_braces:
                clean_text = match_braces.group(1).strip()

        # Sanitize LaTeX backslashes inside JSON
        clean_text = cls.sanitize_json_latex_escapes(clean_text)

        # Sanitize python boolean literals or None if generated
        clean_text = re.sub(r':\s*True\b', ': true', clean_text)
        clean_text = re.sub(r':\s*False\b', ': false', clean_text)
        clean_text = re.sub(r':\s*None\b', ': null', clean_text)

        data = None
        try:
            data = json.loads(clean_text)
        except json.JSONDecodeError as e:
            # Auto-repair truncated JSON if cut off at the end
            last_brace_idx = clean_text.rfind("}")
            if last_brace_idx != -1:
                repaired = clean_text[:last_brace_idx + 1]
                if not repaired.endswith("]}"):
                    if not repaired.endswith("]"):
                        repaired += "\n]}"
                    else:
                        repaired += "\n}"
                try:
                    data = json.loads(repaired)
                    logger.warning("Successfully auto-repaired truncated Gemini JSON response.")
                except Exception:
                    data = None

            if not data:
                logger.error(f"Failed to decode Gemini JSON response: {e}\nRaw: {clean_text[:500]}")
                return ParseResult(errors=[ParseError(question_number=None, message=f"Invalid JSON from Gemini Vision: {str(e)}")])

        raw_questions = data.get("questions", [])
        if not raw_questions and isinstance(data, list):
            raw_questions = data

        if not raw_questions:
            return ParseResult(errors=[ParseError(question_number=None, message="Gemini Vision did not identify any questions in document.")])

        parsed_questions: List[ParsedQuestion] = []
        for item in raw_questions:
            q_num = item.get("question_number", len(parsed_questions) + 1)
            part = item.get("part", "Part1")
            
            # Map question type enum
            q_type_str = item.get("question_type", "MultipleChoice")
            if part == "Part2" or q_type_str == "TrueFalse":
                q_type = QuestionTypeEnum.TrueFalse
            elif part == "Part3" or q_type_str == "ShortAnswer":
                q_type = QuestionTypeEnum.ShortAnswer
            else:
                q_type = QuestionTypeEnum.MultipleChoice

            # Map difficulty enum
            diff_str = item.get("difficulty")
            difficulty = None
            if diff_str:
                for d in DifficultyEnum:
                    if d.value.lower() == str(diff_str).lower():
                        difficulty = d
                        break

            content = item.get("content", "").strip()
            content_markdown = item.get("content_markdown") or content
            content_latex = item.get("content_latex")

            # Parse answer options
            options: List[ParsedOption] = []
            for opt_idx, opt in enumerate(item.get("answer_options", [])):
                opt_content = str(opt.get("content", "")).strip()
                is_corr = bool(opt.get("is_correct", False))
                d_order = int(opt.get("display_order", opt_idx))
                options.append(ParsedOption(
                    content=opt_content,
                    is_correct=is_corr,
                    display_order=d_order
                ))

            parsed_questions.append(ParsedQuestion(
                question_number=q_num,
                part=part,
                question_type=q_type,
                difficulty=difficulty,
                content=content,
                content_markdown=content_markdown,
                content_latex=content_latex,
                confidence_score=0.98,
                needs_review=False,
                image_url=item.get("image_url"),
                answer_options=options,
                correct_answer=item.get("correct_answer")
            ))

        # Sort questions strictly by Part and question_number (1, 2, 3, ..., N)
        parsed_questions.sort(key=lambda q: (
            1 if q.part == "Part1" else 2 if q.part == "Part2" else 3 if q.part == "Part3" else 4,
            q.question_number
        ))

        return ParseResult(questions=parsed_questions, errors=[])
