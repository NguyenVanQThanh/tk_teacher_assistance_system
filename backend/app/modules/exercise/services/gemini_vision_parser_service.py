# File Name: gemini_vision_parser_service.py
# Description: Service for extracting and parsing exam questions from PDF/Images using Google Gemini Multimodal Vision API.
# Created At: 2026-09-02
# Created By: Tam Khang
# Updated At: 2026-11-09
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

# LaTeX commands starting with "n" (so "\n" + letters is not mistaken for a newline escape)
_LATEX_N_COMMANDS = {"neq", "nabla", "ne", "nu", "not", "ni", "notin", "nless", "ngtr", "nleq", "ngeq", "nmid", "nparallel", "nsubseteq", "nrightarrow", "nleftarrow", "newline"}

# Prompt for Vietnamese Math and Science exam OCR
GEMINI_SYSTEM_PROMPT = """Bạn là một chuyên gia số hóa đề thi Toán học và Khoa học tự nhiên của Bộ Giáo dục & Đào tạo Việt Nam.
Nhiệm vụ của bạn là đọc hình ảnh các trang đề thi và trích xuất TOÀN BỘ câu hỏi cùng các phương án lựa chọn thành định dạng JSON có cấu trúc chính xác tuyệt đối.

Quy tắc bóc tách bắt buộc:
1. TOÁN HỌC & LATEX:
   - Mọi công thức toán học, biểu thức đại số, phương trình, hàm số, bất đẳng thức, phân số, logarit, căn bậc hai, tích phân, giới hạn, vectơ, tọa độ điểm, góc, tập nghiệm khoảng đoạn PHẢI được viết chuẩn cú pháp LaTeX và bao bọc trong cặp dấu '$' cho công thức nội dòng (ví dụ: '$f(x) = \\frac{2x}{x^2+1}$', '$\\log_2(x-1) < 3$', '$A(1;-2;3)$', '$\\vec{n} = (2;1;-1)$', '$(1;9)$').
   - Tuyệt đối KHÔNG viết công thức toán dưới dạng text thô bị vỡ (ví dụ không viết 'x 3 - 3x 2 + 2' mà phải viết '$x^3 - 3x^2 + 2$').
   - Bảng biến thiên / bảng dữ liệu (nếu có) BẮT BUỘC tách riêng ra khỏi "content", KHÔNG nhúng trực tiếp vào nội dung câu hỏi. Trả thêm trường "table": {"page": <số trang>, "bbox": [x0, y0, x1, y1], "markdown": "<bảng dạng Markdown Table>"} (bbox chuẩn hóa 0-1000 như "image", khít khung bảng, không gồm chữ xung quanh). Nếu không có bảng thì KHÔNG bịa đặt trường "table".

2. PHÂN LOẠI CẤU TRÚC 3 PHẦN:
   - "Part1": Trắc nghiệm nhiều lựa chọn (MultipleChoice) gồm 4 phương án A, B, C, D.
   - "Part2": Trắc nghiệm Đúng/Sai (TrueFalse) gồm 1 câu dẫn và 4 ý a), b), c), d).
   - "Part3": Trắc nghiệm Trả lời ngắn (ShortAnswer) với đáp án là số hoặc biểu thức ngắn.

3. ĐỘ KHÓ (DIFFICULTY):
   - Nhận biết nhãn độ khó ở đầu câu: '[NB]' -> 'NhanBiet', '[TH]' -> 'ThongHieu', '[VD]' -> 'VanDung', '[VDC]' -> 'VanDungCao'.
4. THỨ TỰ CÂU HỎI (QUESTION ORDER):
   - BẮT BUỘC bóc tách và trả về danh sách `questions` được sắp xếp tăng dần theo đúng số thứ tự câu hỏi trong đề: Câu 1, Câu 2, Câu 3, ..., Câu N.
   - Không được đảo lộn thứ tự giữa các trang hoặc các cột.

5. HÌNH ẢNH ĐÍNH KÈM CỦA CÂU HỎI (IMAGE):
   - Nếu một câu hỏi có hình vẽ / biểu đồ / đồ thị đi kèm, BẮT BUỘC thêm trường "image": {"page": <số trang gốc, chính là số trong nhãn --- TRANG n --->, "bbox": [x0, y0, x1, y1]}.
   - bbox là tọa độ của khung hình trên trang đó theo chuẩn hóa 0-1000 (phần nghìn kích thước trang): x0,y0 là góc trên-trái, x1,y1 là góc dưới-phải của hình.
   - bbox PHẢI khít vừa khung hình/bảng: KHÔNG bao gồm dòng chữ, caption, số câu hỏi hay các ký hiệu bên ngoài hình. Ưu tiên ôm trọn nét vẽ nhưng đừng quá rộng.
   - KHÔNG bịa đặt trường "image" nếu câu hỏi không có hình ảnh.
   - KHÔNG viết mô tả bằng lời về hình ảnh/bảng vào trong "content"; toàn bộ khối hình/bảng phải được cô lập qua các trường "image"/"table".

6. CẤU TRÚC TỪNG PHẦN (MỖI CÂU HỎI = ĐÚNG MỘT JSON OBJECT):
   - Phần I (Part1, MultipleChoice): "answer_options" gồm đủ 4 phương án A, B, C, D theo thứ tự. CHỈ đặt "is_correct": true cho đúng một phương án khi đề có đáp án/đáp án được đánh dấu rõ ràng; nếu KHÔNG có đáp án thì đặt "is_correct": false cho cả 4 và "correct_answer": null. TUYỆT ĐỐI KHÔNG đoán hay tự giải để chọn đáp án.
   - Phần II (Part2, TrueFalse): MỘT câu Đúng/Sai là MỘT object duy nhất, KHÔNG tách mỗi ý a), b), c), d) thành một câu riêng. "content" là câu dẫn; "answer_options" gồm 4 ý a-d (mỗi ý một phần tử, "content" là nội dung ý đó). Chỉ đặt "is_correct" (true/false) khi đề có đáp án; nếu không có thì để false và KHÔNG đoán.
   - Phần III (Part3, ShortAnswer): trả lời ngắn, KHÔNG có "answer_options" (mảng rỗng); "correct_answer" là đáp án nếu đề có, ngược lại null.
   - Phần IV / Tự luận (câu có các ý a), b), ...): ánh xạ thành "part": "Part3", "question_type": "ShortAnswer", MỘT object cho cả câu, đưa toàn bộ các ý a), b) vào "content", không có "answer_options", "correct_answer": null.

7. ĐỊNH DẠNG ĐẦU RA DẠNG STREAM NDJSON (BẮT BUỘC):
   - Trả về kết quả dưới dạng NDJSON: MỖI DÒNG là MỘT JSON object hoàn chỉnh của MỘT câu hỏi.
   - Mỗi JSON object PHẢI nằm trên MỘT dòng vật lý duy nhất: KHÔNG xuống dòng bên trong object, KHÔNG pretty print, KHÔNG thụt lề. Xuống dòng trong chuỗi phải viết là \\n.
   - KHÔNG bọc trong mảng "questions", KHÔNG thêm markdown fence, không thêm chữ nào khác ngoài các dòng JSON.
   - Ví dụ đầu ra mong đợi (mỗi dòng là một object độc lập):
{"question_number": 1, "part": "Part1", "question_type": "MultipleChoice", "difficulty": "NhanBiet", "content": "Cho hàm số $f(x) = x^3 - 3x^2 + 2$. Giá trị cực đại của hàm số là:", "answer_options": [{"content": "$0$", "is_correct": false, "display_order": 0}, {"content": "$2$", "is_correct": false, "display_order": 1}, {"content": "$3$", "is_correct": false, "display_order": 2}, {"content": "$4$", "is_correct": false, "display_order": 3}], "correct_answer": null, "image": {"page": 1, "bbox": [120, 300, 480, 620]}}
{"question_number": 1, "part": "Part2", "question_type": "TrueFalse", "difficulty": "ThongHieu", "content": "Một vật dao động điều hòa. Xét các phát biểu sau:", "answer_options": [{"content": "a) Chu kì dao động là $2$ s.", "is_correct": false, "display_order": 0}, {"content": "b) Biên độ là $5$ cm.", "is_correct": false, "display_order": 1}, {"content": "c) Tần số là $0{,}5$ Hz.", "is_correct": false, "display_order": 2}, {"content": "d) Pha ban đầu bằng $0$.", "is_correct": false, "display_order": 3}], "correct_answer": null}
{"question_number": 1, "part": "Part3", "question_type": "ShortAnswer", "difficulty": "VanDung", "content": "Tính gia tốc của vật (m/s$^2$).", "answer_options": [], "correct_answer": null}
   - Backend đọc stream theo từng object nên object cuối bị cắt do hết token sẽ tự bỏ, các câu hoàn chỉnh phía trước vẫn được giữ nguyên.
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
    def render_pdf_to_images(file_bytes: bytes, scale: float = 3.0) -> List[Image.Image]:
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
        test_code: Optional[str] = None,
        structure_hint: Optional[str] = None
    ) -> ParseResult:
        """
        Main entry point for parsing PDF exam document using Gemini Vision.
        """
        images = cls.render_pdf_to_images(file_bytes)
        if not images:
            return ParseResult(errors=[ParseError(question_number=None, message="PDF contains no renderable pages.")])

        return cls.parse_images_with_gemini(images, test_code=test_code, structure_hint=structure_hint)

    @classmethod
    def parse_images_with_gemini(
        cls,
        images: List[Image.Image],
        test_code: Optional[str] = None,
        page_numbers: Optional[List[int]] = None,
        structure_hint: Optional[str] = None
    ) -> ParseResult:
        """
        Sends exam page images to Google Gemini Vision API and returns parsed structured questions.
        page_numbers carries the original 1-based PDF page number of each image (for image bboxes).
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

            contents: List[Any] = []
            for idx, img in enumerate(images, 1):
                page_no = page_numbers[idx - 1] if page_numbers and idx - 1 < len(page_numbers) else idx
                contents.append(f"--- TRANG {page_no} CỦA ĐỀ THI ---")
                contents.append(img)

            instruction = "Hãy bóc tách toàn bộ các câu hỏi từ tất cả các trang trên và trả về kết quả JSON."
            if structure_hint:
                instruction += "\n" + structure_hint
            contents.append(instruction)

            # Stream the response (NDJSON: one question object per line) so a token-truncated
            # tail only drops the last partial line instead of invalidating the whole payload.
            stream = client.models.generate_content_stream(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=GEMINI_SYSTEM_PROMPT,
                    max_output_tokens=16384,
                    temperature=0.1,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
                )
            )
            raw_text = "".join(getattr(ch, "text", "") or "" for ch in stream)
            logger.info("Gemini chunk: pages=%s raw_chars=%d", page_numbers or list(range(1, len(images) + 1)), len(raw_text))
            return cls._process_streamed_response(raw_text or "{}", provider="Gemini")

        except Exception as e:
            logger.error(f"Gemini Vision API execution failed: {e}", exc_info=True)
            return ParseResult(errors=[ParseError(question_number=None, message=f"Gemini Vision OCR error: {str(e)}")])

    @classmethod
    def parse_images(cls, images: List[Image.Image], test_code: Optional[str] = None,
                     page_numbers: Optional[List[int]] = None,
                     structure_hint: Optional[str] = None) -> ParseResult:
        """Common provider-chain interface (used by ImportParserService)."""
        return cls.parse_images_with_gemini(images, test_code=test_code, page_numbers=page_numbers,
                                            structure_hint=structure_hint)

    @classmethod
    def complete_json(cls, system_prompt: str, user_text: str, images: Optional[List[Image.Image]] = None,
                      schema: Optional[Dict[str, Any]] = None, max_tokens: int = 1024, timeout: float = 60.0) -> str:
        """Small non-streaming JSON call (text, or low-res page images) used for exam structure analysis."""
        api_key = cls.get_api_key()
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
        from google import genai
        from google.genai import types

        contents: List[Any] = [user_text]
        for img in images or []:
            small = img.convert("RGB")
            small.thumbnail((1000, 1000))
            contents.append(small)
        cfg: Dict[str, Any] = dict(
            system_instruction=system_prompt, max_output_tokens=max_tokens, temperature=0,
            response_mime_type="application/json",
            http_options=types.HttpOptions(timeout=int(timeout * 1000)),
        )
        if schema:
            cfg["response_json_schema"] = schema
        if "flash" in cls.get_model_name():
            # Thinking tokens would eat the small output budget (only flash models allow disabling it)
            cfg["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model=cls.get_model_name(), contents=contents, config=types.GenerateContentConfig(**cfg))
        return resp.text or ""

    @classmethod
    def _build_result_from_items(cls, raw_questions: List[Any], provider: str = "Gemini") -> ParseResult:
        """Build a sorted ParseResult from a list of raw question item dicts."""
        from app.modules.exercise.services.import_parser_service import ImportParserService
        if not raw_questions:
            return ParseResult(errors=[ParseError(question_number=None, message=f"{provider} Vision did not identify any questions in document.")])

        parsed_questions: List[ParsedQuestion] = []
        for item in raw_questions:
            if not isinstance(item, dict):
                continue

            raw_q_num = item.get("question_number")
            try:
                q_num = int(raw_q_num) if raw_q_num is not None else len(parsed_questions) + 1
            except (ValueError, TypeError):
                q_num = len(parsed_questions) + 1

            part = str(item.get("part", "Part1")).strip()

            # Map question type enum
            q_type_str = str(item.get("question_type", "MultipleChoice")).strip()
            if part == "Part2" or q_type_str.lower() in ["truefalse", "true_false"]:
                q_type = QuestionTypeEnum.TrueFalse
            elif part == "Part3" or q_type_str.lower() in ["shortanswer", "short_answer"]:
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

            content = str(item.get("content", "") or "").strip()

            # Parse answer options safely (handling None / null, list of strings, etc.)
            raw_options = item.get("answer_options") or item.get("options") or []
            if not isinstance(raw_options, list):
                raw_options = []

            options: List[ParsedOption] = []
            for opt_idx, opt in enumerate(raw_options):
                if isinstance(opt, dict):
                    opt_content = str(opt.get("content") or opt.get("text") or "").strip()
                    is_corr = bool(opt.get("is_correct", False))
                    d_order = int(opt.get("display_order", opt_idx) if opt.get("display_order") is not None else opt_idx)
                elif isinstance(opt, str):
                    opt_content = str(opt).strip()
                    is_corr = False
                    d_order = opt_idx
                else:
                    continue

                if opt_content:
                    options.append(ParsedOption(
                        content=opt_content,
                        is_correct=is_corr,
                        display_order=d_order
                    ))

            # Infer correct answer from correct_answer field if not already flagged in options
            corr_ans = item.get("correct_answer")
            if corr_ans and options and not any(o.is_correct for o in options):
                corr_str = str(corr_ans).strip().upper()
                label_map = {"A": 0, "B": 1, "C": 2, "D": 3}
                if corr_str in label_map and label_map[corr_str] < len(options):
                    options[label_map[corr_str]].is_correct = True

            # Always strip Markdown tables from content so the table stays isolated in its own
            # segment. If the model gave no "table" key, reuse the removed block as the table.
            table_markdown = None
            tbl_info = item.get("table")
            if isinstance(tbl_info, dict):
                md = tbl_info.get("markdown")
                if isinstance(md, str) and md.strip():
                    table_markdown = md.strip()
            if table_markdown is None and isinstance(tbl_info, str) and tbl_info.strip():
                table_markdown = tbl_info.strip()
            content, inline_table = cls._split_inline_table(content)
            if table_markdown is None and inline_table:
                table_markdown = inline_table

            content_markdown = item.get("content_markdown") or ImportParserService.convert_latex_to_markdown(content)
            content_latex = item.get("content_latex") or content
            if inline_table:
                content_markdown = ImportParserService.strip_markdown_tables(content_markdown)
                content_latex = ImportParserService.strip_markdown_tables(content_latex)

            segments, needs_review = ImportParserService.extract_segments(content)
            if table_markdown:
                segments.append({"type": "table", "content": table_markdown, "confidence": 0.9})

            # Optional figure location reported by the vision model (normalized 0-1000 bbox)
            image_page = None
            image_bbox = None
            img_info = item.get("image")
            if isinstance(img_info, dict):
                try:
                    if img_info.get("page") is not None:
                        image_page = int(img_info.get("page"))
                except (ValueError, TypeError):
                    image_page = None
                bb = img_info.get("bbox")
                if isinstance(bb, (list, tuple)) and len(bb) == 4:
                    try:
                        image_bbox = [float(v) for v in bb]
                    except (ValueError, TypeError):
                        image_bbox = None

            # Optional table location reported by the vision model
            table_page = None
            table_bbox = None
            if isinstance(tbl_info, dict):
                try:
                    if tbl_info.get("page") is not None:
                        table_page = int(tbl_info.get("page"))
                except (ValueError, TypeError):
                    table_page = None
                bb = tbl_info.get("bbox")
                if isinstance(bb, (list, tuple)) and len(bb) == 4:
                    try:
                        table_bbox = [float(v) for v in bb]
                    except (ValueError, TypeError):
                        table_bbox = None

            parsed_questions.append(ParsedQuestion(
                question_number=q_num,
                part=part,
                question_type=q_type,
                difficulty=difficulty,
                content=content,
                content_markdown=content_markdown,
                content_latex=content_latex,
                segments=segments,
                confidence_score=0.98 if not needs_review else 0.75,
                needs_review=needs_review,
                image_url=item.get("image_url"),
                answer_options=options,
                correct_answer=str(corr_ans) if corr_ans is not None else None,
                image_page=image_page,
                image_bbox=image_bbox,
                table_page=table_page,
                table_bbox=table_bbox,
                table_markdown=table_markdown
            ))

        # Keep model stream order (= document order); ImportParserService.relabel_by_layout
        # re-orders deterministically from the PDF layout when available.

        return ParseResult(questions=parsed_questions, errors=[])

    @classmethod
    def _process_streamed_response(cls, raw_text: str, provider: str = "Gemini") -> ParseResult:
        """
        Parse a streamed vision response. Preferred format is NDJSON: one complete
        question object per line, so a token-truncated tail only drops the last partial
        line while every complete question is kept. If the model ignored NDJSON and
        returned a single JSON document, fall back to whole-document parsing.
        """
        items: List[Any] = []
        dropped = 0
        for chunk in cls._iter_top_level_objects(raw_text):
            try:
                obj = json.loads(cls.sanitize_json_latex_escapes(chunk), strict=False)
            except Exception:
                dropped += 1
                continue
            if not isinstance(obj, dict):
                continue
            if isinstance(obj.get("questions"), list):
                items.extend(o for o in obj["questions"] if isinstance(o, dict))
            elif obj.get("question_number") is not None and (obj.get("content") or obj.get("part")):
                items.append(obj)
            else:
                dropped += 1
        logger.info(
            "%s stream parsed: raw_chars=%d top_level_items=%d dropped_objects=%d",
            provider, len(raw_text), len(items), dropped,
        )
        if items:
            return cls._build_result_from_items(items, provider)
        logger.warning("%s stream yielded no question objects; trying whole-document parse.", provider)
        return cls._process_gemini_json_response(raw_text, provider=provider)

    @staticmethod
    def _iter_top_level_objects(text: str):
        """
        Yield each complete top-level {...} JSON object found in text. Uses a brace-depth
        scan that respects string literals, so both one-line NDJSON and pretty-printed
        multi-line JSON work, nested objects are never yielded on their own, and an
        unterminated (token-truncated) tail object is dropped.
        """
        depth = 0
        start = -1
        in_str = False
        esc = False
        for i, ch in enumerate(text):
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"' and depth > 0:
                in_str = True
            elif ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}" and depth > 0:
                depth -= 1
                if depth == 0:
                    yield text[start:i + 1]

    @staticmethod
    def _split_inline_table(content: str) -> Tuple[str, Optional[str]]:
        """Remove Markdown table blocks from content; return (clean_content, removed_table_or_None)."""
        from app.modules.exercise.services.import_parser_service import ImportParserService
        if not content or "|" not in content:
            return content, None
        blocks = []
        for m in re.finditer(r"(?:^[ \t]*\|.*\|[ \t]*(?:\n|$))+", content, re.M):
            blk = m.group(0).strip()
            lines = blk.splitlines()
            if len(lines) >= 2 and any(re.match(r"^\s*\|?[\s:|-]+\|?\s*$", ln) and "-" in ln for ln in lines):
                blocks.append(blk)
        if not blocks:
            return content, None
        return ImportParserService.strip_markdown_tables(content), "\n\n".join(blocks)

    @staticmethod
    def _repair_truncated_json(text: str, max_attempts: int = 60) -> Optional[Any]:
        """
        Best-effort repair of JSON cut off by the model output-token limit.
        Walks back over closing braces, drops the partial tail, and tries to close
        any open containers (], }, ]}). Returns parsed data or None.
        """
        candidates = [text]
        idx = text.rfind("}")
        attempts = 0
        while idx != -1 and attempts < max_attempts:
            candidates.append(text[:idx + 1])
            idx = text.rfind("}", 0, idx)
            attempts += 1
        for cand in candidates:
            for suffix in ("", "]", "}", "]}", "}]", "\n]}", "\n}]"):
                try:
                    return json.loads(cand + suffix, strict=False)
                except Exception:
                    continue
        return None

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
            if esc_char == 'n' and (not rest or not rest[0].isalpha() or ('n' + rest) not in _LATEX_N_COMMANDS):
                # Real newline escape unless the word is a known LaTeX command (neq, nabla, ...)
                return full
            if esc_char == 'u' and len(rest) >= 4 and re.match(r'^[0-9a-fA-F]{4}', rest):
                return full
            if esc_char in ('r', 't', 'b', 'f') and (not rest or not rest[0].isalpha()):
                return full
                
            return '\\\\' + esc_char + rest

        return re.sub(r'\\([a-zA-Z0-9"\\/])([a-zA-Z]*)', fix_escape, raw)

    @classmethod
    def _process_gemini_json_response(cls, raw_json_str: str, provider: str = "Gemini") -> ParseResult:
        """
        Parses a whole-document JSON string from a vision provider (fallback when the
        model did not follow the NDJSON stream format), auto-repairs token-truncated
        JSON, and builds a sorted List[ParsedQuestion].
        """
        from app.modules.exercise.services.import_parser_service import ImportParserService
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
            data = json.loads(clean_text, strict=False)
        except json.JSONDecodeError as e:
            # Auto-repair JSON truncated by the output-token cap (drop the partial tail)
            data = cls._repair_truncated_json(clean_text)
            if data is not None:
                logger.warning(f"Auto-repaired token-truncated {provider} JSON response (partial tail dropped).")

            if data is None:
                logger.error(f"Failed to decode {provider} JSON response: {e}\nRaw: {clean_text[:500]}")
                return ParseResult(errors=[ParseError(question_number=None, message=f"Invalid JSON from {provider} Vision: {str(e)}")])

        raw_questions = data.get("questions") if isinstance(data, dict) else (data if isinstance(data, list) else [])
        if raw_questions is None:
            raw_questions = []
        elif isinstance(raw_questions, dict):
            raw_questions = list(raw_questions.values())

        return cls._build_result_from_items(raw_questions, provider)
