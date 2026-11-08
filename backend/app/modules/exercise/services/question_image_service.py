# File Name: question_image_service.py
# Description: Storage service for images attached to questions. Files are written to the
# BE storage directory configured via QUESTION_IMAGE_DIR (see app/core/config.py) and served
# under QUESTION_IMAGE_URL_PREFIX. Returns metadata that callers persist on the Question row.
# Created At: 2026-11-08
# Created By: Tam Khang

import io
import uuid
from typing import Optional, Tuple

from fastapi import HTTPException, UploadFile, status

from app.core.config import (
    QUESTION_IMAGE_ALLOWED_EXTENSIONS,
    QUESTION_IMAGE_DIR,
    QUESTION_IMAGE_MAX_BYTES,
    QUESTION_IMAGE_URL_PREFIX,
)


class QuestionImageService:
    """Save uploaded question images to BE storage and return their metadata."""

    @staticmethod
    def _detect_dimensions(data: bytes, ext: str) -> Tuple[Optional[int], Optional[int]]:
        """Best-effort width/height detection using Pillow (SVG is skipped)."""
        if ext == "svg":
            return None, None
        try:
            from PIL import Image

            with Image.open(io.BytesIO(data)) as img:
                return img.width, img.height
        except Exception:
            return None, None

    @staticmethod
    def save_image(file: UploadFile) -> dict:
        original_name = file.filename or "image"
        ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
        if ext not in QUESTION_IMAGE_ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "ERR-EXE-IMAGE_TYPE_NOT_ALLOWED",
                    "message": f"Image type '.{ext}' is not allowed. Allowed: {sorted(QUESTION_IMAGE_ALLOWED_EXTENSIONS)}",
                },
            )

        data = file.file.read()
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "ERR-EXE-IMAGE_EMPTY", "message": "Uploaded image is empty."},
            )
        if len(data) > QUESTION_IMAGE_MAX_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "code": "ERR-EXE-IMAGE_TOO_LARGE",
                    "message": f"Image exceeds maximum size of {QUESTION_IMAGE_MAX_BYTES} bytes.",
                },
            )

        filename = f"q_img_{uuid.uuid4().hex[:12]}.{ext}"
        QUESTION_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        target_path = QUESTION_IMAGE_DIR / filename
        with open(target_path, "wb") as f:
            f.write(data)

        width, height = QuestionImageService._detect_dimensions(data, ext)

        return {
            "url": f"{QUESTION_IMAGE_URL_PREFIX}/{filename}",
            "filename": filename,
            "original_name": original_name,
            "size_bytes": len(data),
            "content_type": file.content_type,
            "width": width,
            "height": height,
        }
