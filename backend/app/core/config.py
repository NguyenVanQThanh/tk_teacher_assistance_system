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


# ---------------------------------------------------------------------------
# Concurrency / resource limits (30 concurrent users, 5 GB total RAM budget).
# These are process-local limits; when running N uvicorn workers multiply the
# effective capacity by N (and size the DB pool accordingly).
# ---------------------------------------------------------------------------
def _env_int(name: str, default: int, minimum: int = 1) -> int:
    """Read a positive integer env var, falling back to the default on bad input."""
    try:
        value = int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(minimum, value)


# Maximum number of simultaneous PDF exports per backend process.
PDF_EXPORT_CONCURRENCY = _env_int("PDF_EXPORT_CONCURRENCY", 2)

# Maximum number of simultaneous bulk imports (questions / users) per process.
# Import parsing is CPU-bound (docx/PDF OCR + AI answer solving) and commits
# per row, so keep it small; extra requests wait in the threadpool.
IMPORT_CONCURRENCY = _env_int("IMPORT_CONCURRENCY", 2)

# Maximum number of documents ingested at the same time per backend process.
# Ingestion is CPU/IO/memory heavy (PDF render + VLM + embeddings), so default 1.
ETL_CONCURRENCY = _env_int("ETL_CONCURRENCY", 1)

# Hard cap for an uploaded document before it is read into memory (default 50 MB).
MAX_INGEST_BYTES = _env_int("MAX_INGEST_BYTES", 50 * 1024 * 1024)

# Default worker count for backend/scripts/load_test.py (not used by the app).
LOAD_TEST_DEFAULT_USERS = _env_int("LOAD_TEST_DEFAULT_USERS", 30)

# AI exercise generation: process-wide concurrent generations, parallel LLM calls per generation and
# retry rounds for missing questions.
AI_GENERATE_CONCURRENCY = _env_int("AI_GENERATE_CONCURRENCY", 4)
AI_PART_WORKERS = _env_int("AI_PART_WORKERS", 3)
AI_PART_MAX_RETRIES = _env_int("AI_PART_MAX_RETRIES", 2, minimum=0)
# Mistral model for question generation (tried before Gemini)
AI_MISTRAL_MODEL = os.environ.get("AI_MISTRAL_MODEL", "mistral-large-latest")
