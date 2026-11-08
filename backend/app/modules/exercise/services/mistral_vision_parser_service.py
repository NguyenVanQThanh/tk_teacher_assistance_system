# File Name: mistral_vision_parser_service.py
# Description: Service for extracting and parsing exam questions from PDF/Images using Mistral AI Vision API (Pixtral), with config-driven provider selection.
# Created At: 2026-11-08
# Created By: Tam Khang

import os
import io
import base64
import json
import logging
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
DEFAULT_MISTRAL_MODEL = "pixtral-12b-2409"
# Pixtral accepts at most ~1568px per image side and 8192 output tokens
MISTRAL_MAX_IMAGE_SIDE = 1568
DEFAULT_MISTRAL_MAX_TOKENS = 8192


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
        """Retrieve configured Mistral vision model or default to pixtral-12b-2409."""
        return os.environ.get("MISTRAL_MODEL_NAME", DEFAULT_MISTRAL_MODEL)

    @staticmethod
    def get_api_url() -> str:
        """Retrieve Mistral chat completions endpoint (override for proxies/self-hosted)."""
        return os.environ.get("MISTRAL_API_URL", DEFAULT_MISTRAL_API_URL)

    @staticmethod
    def get_max_tokens() -> int:
        """Max output tokens (Pixtral models cap at 8192; override via MISTRAL_MAX_TOKENS)."""
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
        test_code: Optional[str] = None
    ) -> ParseResult:
        """
        Main entry point for parsing PDF exam document using Mistral Vision.
        """
        # render_pdf_to_images is provider-agnostic (pypdfium2), reused from the Gemini service
        images = GeminiVisionParserService.render_pdf_to_images(file_bytes)
        if not images:
            return ParseResult(errors=[ParseError(question_number=None, message="PDF contains no renderable pages.")])

        return cls.parse_images_with_mistral(images, test_code=test_code)

    @classmethod
    def parse_images_with_mistral(
        cls,
        images: List[Image.Image],
        test_code: Optional[str] = None,
        page_numbers: Optional[List[int]] = None
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
            user_content.append({
                "type": "text",
                "text": "Hãy bóc tách toàn bộ các câu hỏi từ tất cả các trang trên và trả về kết quả JSON.",
            })

            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": VISION_OCR_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                # NDJSON stream (one question object per line) - response_format json_object
                # is intentionally omitted because it forces a single JSON document
                "stream": True,
                "temperature": 0.1,
                "max_tokens": cls.get_max_tokens(),
            }
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            # Stream the SSE response and accumulate delta content line by line. A
            # token-truncated tail only cuts the last partial line, not the whole payload.
            raw_parts: List[str] = []
            with httpx.Client(timeout=300.0) as client:
                with client.stream("POST", cls.get_api_url(), json=payload, headers=headers) as response:
                    response.raise_for_status()
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
                                content = delta.get("content")
                                if content:
                                    raw_parts.append(content)
                            except Exception:
                                continue
                        else:
                            # non-SSE plain text fallback
                            raw_parts.append(line)

            raw_text = "".join(raw_parts)
            # NDJSON / whole-JSON parsing is provider-agnostic, reused from the Gemini service
            return GeminiVisionParserService._process_streamed_response(raw_text or "{}", provider="Mistral")

        except Exception as e:
            logger.error(f"Mistral Vision API execution failed: {e}", exc_info=True)
            return ParseResult(errors=[ParseError(question_number=None, message=f"Mistral Vision OCR error: {str(e)}")])

    @classmethod
    def parse_images(cls, images: List[Image.Image], test_code: Optional[str] = None,
                     page_numbers: Optional[List[int]] = None) -> ParseResult:
        """Common provider-chain interface (used by ImportParserService)."""
        return cls.parse_images_with_mistral(images, test_code=test_code, page_numbers=page_numbers)
