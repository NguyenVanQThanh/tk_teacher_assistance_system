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

# Read-only SGK (textbook) figure images served for RAG source previews.
SGK_IMAGE_DIR = Path(os.environ.get("SGK_IMAGE_DIR", "uploads/sgk_images"))
SGK_IMAGE_URL_PREFIX = (
    os.environ.get("SGK_IMAGE_URL_PREFIX", "/sgk-images") or "/sgk-images"
).rstrip("/") or "/sgk-images"

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

# Document ingestion (VLM extraction + embeddings into document_chunks).
MISTRAL_EMBED_MODEL = os.environ.get("MISTRAL_EMBED_MODEL", "mistral-embed")
MISTRAL_EMBED_URL = os.environ.get("MISTRAL_EMBED_URL", "https://api.mistral.ai/v1/embeddings")
EMBED_BATCH_SIZE = int(os.environ.get("EMBED_BATCH_SIZE", "16"))
DOCUMENT_FIGURE_DIR = Path(os.environ.get("DOCUMENT_FIGURE_DIR", "uploads/documents_figures"))
DOCUMENT_RENDER_DPI = int(os.environ.get("DOCUMENT_RENDER_DPI", "200"))

# RAG query expansion (sub-queries for retrieval). API keys are read from the process environment at call time.
RAG_QUERY_EXPANSION_ENABLED = os.environ.get("RAG_QUERY_EXPANSION_ENABLED", "true").strip().lower() in ("1", "true", "yes")
RAG_QUERY_EXPANSION_GEMINI_MODEL = os.environ.get("RAG_QUERY_EXPANSION_GEMINI_MODEL", "gemini-2.5-flash")
RAG_QUERY_EXPANSION_MISTRAL_MODEL = os.environ.get("RAG_QUERY_EXPANSION_MISTRAL_MODEL", "mistral-small-latest")
