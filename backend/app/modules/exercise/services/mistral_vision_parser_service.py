# File Name: mistral_vision_parser_service.py
# Description: Service for extracting and parsing exam questions from PDF/Images using Mistral AI Vision API (Pixtral), with config-driven provider selection.
# Created At: 2026-11-08
# Created By: Tam Khang

import os
import io
import base64
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

    @classmethod
    def is_available(cls) -> bool:
        """Check if Mistral API key is configured."""
        return bool(cls.get_api_key())

    @staticmethod
    def _image_to_data_url(img: Image.Image) -> str:
        """Encode a PIL image as a base64 PNG data URL for the Mistral API."""
        buffer = io.BytesIO()
        img.convert("RGB").save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}"

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
        test_code: Optional[str] = None
    ) -> ParseResult:
        """
        Sends exam page images to Mistral Vision API (chat completions) and returns parsed structured questions.
        """
        api_key = cls.get_api_key()
        if not api_key:
            return ParseResult(errors=[ParseError(question_number=None, message="MISTRAL_API_KEY is not configured.")])

        model_name = cls.get_model_name()

        try:
            user_content: List[Any] = []
            for idx, img in enumerate(images, 1):
                user_content.append({"type": "text", "text": f"--- TRANG {idx} CỦA ĐỀ THI ---"})
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
                "response_format": {"type": "json_object"},
                "temperature": 0.1,
                "max_tokens": 16384,
            }
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            with httpx.Client(timeout=300.0) as client:
                response = client.post(cls.get_api_url(), json=payload, headers=headers)
                response.raise_for_status()

            data = response.json()
            raw_json = data["choices"][0]["message"]["content"] or "{}"
            # JSON repair/parsing is provider-agnostic, reused from the Gemini service
            return GeminiVisionParserService._process_gemini_json_response(raw_json)

        except Exception as e:
            logger.error(f"Mistral Vision API execution failed: {e}", exc_info=True)
            return ParseResult(errors=[ParseError(question_number=None, message=f"Mistral Vision OCR error: {str(e)}")])
