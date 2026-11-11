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

# AI answer solver (fills the correct option for unkeyed MC / True-False questions).
ANSWER_SOLVER_ENABLED = os.environ.get("ANSWER_SOLVER_ENABLED", "true").strip().lower() in ("1", "true", "yes")
ANSWER_SOLVER_MODEL = os.environ.get("ANSWER_SOLVER_MODEL", "mistral-large-4-0")
ANSWER_SOLVER_BATCH_SIZE = int(os.environ.get("ANSWER_SOLVER_BATCH_SIZE", "5"))

# VLM figure detection (reconciled with PDF layout blocks) and its crop verification pass.
FIGURE_VLM_ENABLED = os.environ.get("FIGURE_VLM_ENABLED", "true").strip().lower() in ("1", "true", "yes")
FIGURE_VLM_VERIFY = os.environ.get("FIGURE_VLM_VERIFY", "true").strip().lower() in ("1", "true", "yes")
FIGURE_VLM_MODEL = os.environ.get("FIGURE_VLM_MODEL", "")  # empty -> MISTRAL_MODEL_NAME
