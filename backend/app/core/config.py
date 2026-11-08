# File Name: config.py
# Description: Application-level configuration loaded from environment variables (.env).
# Created At: 2026-11-08
# Created By: Tam Khang

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Question image storage (BE storage for images attached to questions).
# Override these in .env to change where uploaded images are stored/served.
# ---------------------------------------------------------------------------
# Directory on disk where question images are written.
QUESTION_IMAGE_DIR = Path(os.environ.get("QUESTION_IMAGE_DIR", "uploads/questions"))

# URL prefix under which the FastAPI app serves the stored images.
QUESTION_IMAGE_URL_PREFIX = (
    os.environ.get("QUESTION_IMAGE_URL_PREFIX", "/uploads/questions") or "/uploads/questions"
).rstrip("/") or "/uploads/questions"

# Maximum accepted image size (default 10 MB).
QUESTION_IMAGE_MAX_BYTES = int(os.environ.get("QUESTION_IMAGE_MAX_BYTES", str(10 * 1024 * 1024)))

# Allowed image file extensions.
QUESTION_IMAGE_ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "svg"}
