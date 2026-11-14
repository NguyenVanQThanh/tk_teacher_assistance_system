# File Name: mistral_vision_parser_service.py
# Description: Service for extracting and parsing exam questions from PDF/Images using Mistral AI Vision API, with config-driven provider selection.
# Created At: 2026-11-08
# Created By: Tam Khang
# Updated At: 2026-11-10
# Updated By: AI Agent

import os
import io
import base64
import json
import logging
import time
from typing import List, Optional, Any

import httpx
from PIL import Image

from app.modules.exercise.services.import_parser_service import ParseError, ParseResult
from app.modules.exercise.services.gemini_vision_parser_service import (
    GeminiVisionParserService,
    GEMINI_SYSTEM_PROMPT as VISION_OCR_SYSTEM_PROMPT,
)

logger = logging.getLogger("smartlms.exercise.mistral_vision")

DEFAULT_MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
# pixtral-12b-2409 was retired by Mistral on 2025-12-31. Cheaper alternative: mistral-small-2603.
DEFAULT_MISTRAL_MODEL = "mistral-large-4-0"
# Optional OCR-first path (SCAN_OCR_FIRST=true): Mistral OCR text is passed to the model as
# the single source of truth for "Cau N" text, the images stay for figures/layout.
DEFAULT_MISTRAL_OCR_MODEL = "mistral-ocr-2512"

# Mistral-specific addendum appended to the shared (Gemini) prompt.
MISTRAL_PROMPT_ADDENDUM = """

QUY TẮC BỔ SUNG (BẮT BUỘC):
- Các ý a), b), c), d) của câu Đúng/Sai là CÁC MỆNH ĐỀ của MỘT câu duy nhất, TUYỆT ĐỐI KHÔNG tách thành các câu riêng. Một câu Đúng/Sai luôn có đủ 4 ý trong "answer_options".
- Loại câu hỏi do TIÊU ĐỀ PHẦN quyết định (PHẦN I = trắc nghiệm nhiều lựa chọn, PHẦN II = đúng/sai với các ý a-d, PHẦN III = trả lời ngắn, tự luận tách riêng), KHÔNG phụ thuộc việc câu có hình/bảng hay không.
- CHÉP NGUYÊN VĂN từng chữ của đề: không diễn đạt lại, không tóm tắt, không thay từ đồng nghĩa, không dịch, không sửa ngữ pháp/chính tả; giữ đủ mọi câu, mọi số liệu, mọi đơn vị ở đề bài và từng phương án.
- Không bịa nội dung: chỉ chép đúng chữ có trên trang. Không tự tạo câu hỏi hay phương án không có trong ảnh.
- Chép ĐẦY ĐỦ mọi câu, kể cả câu có bảng/hình/đồ thị; không bỏ sót câu nào ngay sau một hình. Số câu chạy liên tục 1..N trong mỗi phần.
- Câu bị ngắt giữa hai trang: chép đầy đủ phần có trên các trang được gửi; câu chưa kết thúc ở cuối trang cuối thì bỏ qua (sẽ nằm ở lượt sau)."""
# Pixtral officially recommends ~1568px per side, but exam scans need the extra
# resolution for accurate figure bboxes; 3136 keeps full render detail (scale 3.0
# A4 ~= 2480x3508 -> still downscaled a bit, yet far sharper than 1568).
MISTRAL_MAX_IMAGE_SIDE = int(os.environ.get("MISTRAL_MAX_IMAGE_SIDE", "3136"))
DEFAULT_MISTRAL_MAX_TOKENS = 16384
# Transcription temperature: 0 is rejected by mistral-large-4-0 (HTTP 400 greedy/top_p), so use a tiny value.
MISTRAL_PARSE_TEMPERATURE = float(os.environ.get("MISTRAL_PARSE_TEMPERATURE", "0.02"))


def flatten_content(content: Any) -> str:
    """Flatten Mistral message/delta content into plain text.

    Accepts str, None, or a list of str / dict / objects with `.text`. Reasoning
    ("thinking") chunks are ignored so only the final answer text is returned.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, (list, tuple)):
        return "".join(flatten_content(c) for c in content)
    if isinstance(content, dict):
        if content.get("type") == "thinking" or "thinking" in content:
            return ""
        return flatten_content(content.get("text"))
    if getattr(content, "type", None) == "thinking" or hasattr(content, "thinking"):
        return ""
    return flatten_content(getattr(content, "text", None))


def raise_for_status_logged(response: httpx.Response) -> None:
    """raise_for_status, logging status + error body (never headers) for HTTP 4xx at WARNING."""
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError:
        if response.status_code == 400 or 400 <= response.status_code < 500:
            try:
                response.read()
                body = response.text[:1000]
            except Exception:
                body = "<unreadable>"
            logger.warning("Mistral HTTP %s error body: %s", response.status_code, body)
        raise


class MistralVisionParserService:
    """
    Multimodal Vision Parser utilizing Mistral AI API (Pixtral models)
    to perform deep mathematical OCR on exam document pages.
    """

    @staticmethod
    def get_api_key() -> Optional[str]:
        """Retrieve Mistral API Key from environment or .env file."""
        if not os.environ.get("PYTEST_CURRENT_TEST"):
            if "MISTRAL_API_KEY" not in os.environ and "MISTRAL_KEY" not in os.environ:
                from dotenv import load_dotenv, find_dotenv
                load_dotenv(find_dotenv())
        return os.environ.get("MISTRAL_API_KEY") or os.environ.get("MISTRAL_KEY")

    @staticmethod
    def get_model_name() -> str:
        """Retrieve configured Mistral vision model (MISTRAL_MODEL_NAME, default mistral-large-4-0)."""
        return os.environ.get("MISTRAL_MODEL_NAME") or DEFAULT_MISTRAL_MODEL

    @staticmethod
    def ocr_first_enabled() -> bool:
        """True when SCAN_OCR_FIRST is set (default off)."""
        return os.environ.get("SCAN_OCR_FIRST", "false").strip().lower() in ("1", "true", "yes")

    @staticmethod
    def get_ocr_model() -> str:
        """Mistral OCR model (MISTRAL_OCR_MODEL, default mistral-ocr-2512)."""
        return os.environ.get("MISTRAL_OCR_MODEL") or DEFAULT_MISTRAL_OCR_MODEL

    @classmethod
    def ocr_pages(cls, images: List[Image.Image]) -> List[str]:
        """Markdown (tables as HTML) per page image via Mistral OCR; [] on any failure."""
        try:
            from mistralai.client import Mistral
            client = Mistral(api_key=cls.get_api_key())
            out: List[str] = []
            for img in images:
                resp = client.ocr.process(
                    model=cls.get_ocr_model(),
                    document={"type": "image_url", "image_url": cls._image_to_data_url(img)},
                    include_image_base64=False, table_format="html",
                )
                out.append("\n".join(p.markdown for p in resp.pages))
            return out
        except Exception as e:
            logger.warning("Mistral OCR-first step failed, continuing with images only: %s", e)
            return []

    @staticmethod
    def get_api_url() -> str:
        """Retrieve Mistral chat completions endpoint (override for proxies/self-hosted)."""
        return os.environ.get("MISTRAL_API_URL", DEFAULT_MISTRAL_API_URL)

    @staticmethod
    def get_max_tokens() -> int:
        """Max output tokens per call (override via MISTRAL_MAX_TOKENS)."""
        try:
            return int(os.environ.get("MISTRAL_MAX_TOKENS", str(DEFAULT_MISTRAL_MAX_TOKENS)))
        except ValueError:
            return DEFAULT_MISTRAL_MAX_TOKENS

    @staticmethod
    def _image_to_data_url(img: Image.Image) -> str:
        """Downscale and encode a page image as a JPEG data URL (Pixtral-friendly size)."""
        img = img.convert("RGB")
        img.thumbnail((MISTRAL_MAX_IMAGE_SIDE, MISTRAL_MAX_IMAGE_SIDE))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"

    @classmethod
    def is_available(cls) -> bool:
        """Check if Mistral API key is configured."""
        return bool(cls.get_api_key())

    @classmethod
    def parse_pdf_document(
        cls,
        file_bytes: bytes,
        test_code: Optional[str] = None,
        structure_hint: Optional[str] = None
    ) -> ParseResult:
        """
        Main entry point for parsing PDF exam document using Mistral Vision.
        """
        # render_pdf_to_images is provider-agnostic (pypdfium2), reused from the Gemini service
        images = GeminiVisionParserService.render_pdf_to_images(file_bytes)
        if not images:
            return ParseResult(errors=[ParseError(question_number=None, message="PDF contains no renderable pages.")])

        return cls.parse_images_with_mistral(images, test_code=test_code, structure_hint=structure_hint)

    @classmethod
    def parse_images_with_mistral(
        cls,
        images: List[Image.Image],
        test_code: Optional[str] = None,
        page_numbers: Optional[List[int]] = None,
        structure_hint: Optional[str] = None
    ) -> ParseResult:
        """
        Sends exam page images to Mistral Vision API (chat completions) and returns parsed structured questions.
        page_numbers carries the original 1-based PDF page number of each image (for image bboxes).
        """
        api_key = cls.get_api_key()
        if not api_key:
            return ParseResult(errors=[ParseError(question_number=None, message="MISTRAL_API_KEY is not configured.")])

        model_name = cls.get_model_name()

        try:
            user_content: List[Any] = []
            for idx, img in enumerate(images, 1):
                page_no = page_numbers[idx - 1] if page_numbers and idx - 1 < len(page_numbers) else idx
                user_content.append({"type": "text", "text": f"--- TRANG {page_no} CỦA ĐỀ THI ---"})
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": cls._image_to_data_url(img)},
                })
            if cls.ocr_first_enabled():
                texts = cls.ocr_pages(images)
                if texts:
                    joined = "\n\n".join(
                        f"[OCR page {page_numbers[i] if page_numbers and i < len(page_numbers) else i + 1}]\n{t}"
                        for i, t in enumerate(texts))
                    user_content.append({"type": "text", "text":
                        "Reference OCR text (exact source for 'Câu N' labels, formulas, HTML tables):\n" + joined})
            instruction = "Hãy bóc tách toàn bộ các câu hỏi từ tất cả các trang trên và trả về kết quả JSON."
            if structure_hint:
                instruction += "\n" + structure_hint
            user_content.append({"type": "text", "text": instruction})

            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": VISION_OCR_SYSTEM_PROMPT + MISTRAL_PROMPT_ADDENDUM},
                    {"role": "user", "content": user_content},
                ],
                # NDJSON stream (one question object per line) - response_format json_object
                # is intentionally omitted because it forces a single JSON document
                "stream": True,
                "temperature": MISTRAL_PARSE_TEMPERATURE,
                "max_tokens": cls.get_max_tokens(),
            }
            # Transcription needs no deep reasoning; without this the model spends the token
            # budget thinking (empty output after ~2 minutes). "none" is rejected by large-4-0.
            effort = os.environ.get("MISTRAL_PARSE_REASONING_EFFORT", "low").strip().lower()
            if effort in ("low", "medium", "high"):
                payload["reasoning_effort"] = effort
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            # Stream the SSE response and accumulate delta content line by line. A
            # token-truncated tail only cuts the last partial line, not the whole payload.
            raw_parts: List[str] = []
            started = time.monotonic()
            # read timeout applies between stream chunks, so a stalled model fails fast
            timeout = httpx.Timeout(connect=15.0, read=120.0, write=60.0, pool=15.0)
            with httpx.Client(timeout=timeout) as client:
                with client.stream("POST", cls.get_api_url(), json=payload, headers=headers) as response:
                    raise_for_status_logged(response)
                    for line in response.iter_lines():
                        if not line:
                            continue
                        if line.startswith("data:"):
                            data = line[len("data:"):].strip()
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                delta = chunk["choices"][0].get("delta", {})
                                content = flatten_content(delta.get("content"))
                                if content:
                                    raw_parts.append(content)
                            except Exception:
                                continue
                        else:
                            # non-SSE plain text fallback
                            raw_parts.append(line)

            raw_text = "".join(raw_parts)
            logger.info("Mistral chunk: pages=%s raw_chars=%d elapsed=%.1fs model=%s",
                        page_numbers or list(range(1, len(images) + 1)), len(raw_text),
                        time.monotonic() - started, model_name)
            # NDJSON / whole-JSON parsing is provider-agnostic, reused from the Gemini service
            return GeminiVisionParserService._process_streamed_response(raw_text or "{}", provider="Mistral")

        except Exception as e:
            logger.error(f"Mistral Vision API execution failed: {e}", exc_info=True)
            return ParseResult(errors=[ParseError(question_number=None, message=f"Mistral Vision OCR error: {str(e)}")])

    @classmethod
    def parse_images(cls, images: List[Image.Image], test_code: Optional[str] = None,
                     page_numbers: Optional[List[int]] = None,
                     structure_hint: Optional[str] = None) -> ParseResult:
        """Common provider-chain interface (used by ImportParserService)."""
        return cls.parse_images_with_mistral(images, test_code=test_code, page_numbers=page_numbers,
                                             structure_hint=structure_hint)

    @classmethod
    def complete_json(cls, system_prompt: str, user_text: str, images: Optional[List[Image.Image]] = None,
                      schema: Optional[dict] = None, max_tokens: int = 1024, timeout: float = 60.0) -> str:
        """Small non-streaming JSON chat call (text, or low-res page images) used for exam structure analysis."""
        api_key = cls.get_api_key()
        if not api_key:
            raise RuntimeError("MISTRAL_API_KEY is not configured.")
        content: List[Any] = [{"type": "text", "text": user_text}]
        for img in images or []:
            small = img.convert("RGB")
            small.thumbnail((1000, 1000))
            buf = io.BytesIO()
            small.save(buf, format="JPEG", quality=70)
            content.append({"type": "image_url", "image_url": {
                "url": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")}})
        payload = {
            "model": cls.get_model_name(),
            "messages": [{"role": "system", "content": system_prompt},
                         {"role": "user", "content": content if images else user_text}],
            # HTTP 400 "top_p must be 1 when using greedy sampling" for temperature 0 on this model
            "temperature": 0.1,
            "reasoning_effort": "low",  # "none" is rejected by mistral-large-4-0; low keeps thinking short
            "max_tokens": max_tokens,
            "response_format": ({"type": "json_schema",
                                 "json_schema": {"name": "exam_structure", "schema": schema, "strict": True}}
                                if schema else {"type": "json_object"}),
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        started = time.monotonic()
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(cls.get_api_url(), json=payload, headers=headers)
            raise_for_status_logged(resp)
            text = flatten_content(resp.json()["choices"][0]["message"]["content"])
        logger.info("Mistral complete_json: elapsed=%.1fs chars=%d", time.monotonic() - started, len(text))
        return text
