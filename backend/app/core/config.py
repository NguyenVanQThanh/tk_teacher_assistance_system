# File Name: config.py
# Description: Application-level configuration loaded from environment variables (.env).
# Created At: 2026-11-08
# Created By: Tam Khang
# Updated At: 2026-11-17
# Updated By: AI Agent

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

# ---------------------------------------------------------------------------
# File storage backend for uploaded files. The DB keeps storing URL strings, so
# switching between local disk and Cloudflare R2 does not change the schema.
# ---------------------------------------------------------------------------
# local (default) or r2/cloud/s3 (all three mean Cloudflare R2, case-insensitive).
STORAGE_BACKEND = (os.environ.get("STORAGE_BACKEND", "local") or "local").strip().lower()

# Root directory for local storage; storage keys are resolved relative to it.
UPLOAD_ROOT = Path(os.environ.get("UPLOAD_ROOT", "uploads"))

# Cloudflare R2 (S3-compatible) credentials; only used when STORAGE_BACKEND=r2.
R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET = os.environ.get("R2_BUCKET", "")
R2_PUBLIC_BASE_URL = os.environ.get("R2_PUBLIC_BASE_URL", "")

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
AI_PART_MAX_TOKENS = _env_int("AI_PART_MAX_TOKENS", 3500, minimum=500)
# Questions requested per model call; smaller batches avoid replies cut off at max_tokens.
AI_PART_BATCH_SIZE = _env_int("AI_PART_BATCH_SIZE", 5, minimum=1)
# Worker threads that process queued background jobs (0 disables the worker, e.g. in tests).
JOB_WORKERS = _env_int("JOB_WORKERS", 2, minimum=0)
# Mistral model for question generation (tried before Gemini)
AI_MISTRAL_MODEL = os.environ.get("AI_MISTRAL_MODEL", "mistral-large-latest")


def _env_bool(name: str, default: bool) -> bool:
    return os.environ.get(name, "true" if default else "false").strip().lower() in ("1", "true", "yes")

# Second-pass LLM review of generated questions (solves each question blind and compares keys).
AI_JUDGE_ENABLED = _env_bool("AI_JUDGE_ENABLED", True)
AI_JUDGE_MODEL = os.environ.get("AI_JUDGE_MODEL", "deepseek-v4-1-flash-1017")  # served through the Mistral API (MISTRAL_API_KEY)
AI_JUDGE_MAX_TOKENS = _env_int("AI_JUDGE_MAX_TOKENS", 600, minimum=200)

# ---------------------------------------------------------------------------
# Guest access (POST /api/v1/auth/guest) and academic year.
# ---------------------------------------------------------------------------
GUEST_ACCESS_ENABLED = _env_bool("GUEST_ACCESS_ENABLED", True)
# Maximum guest accounts created per client IP per rolling hour.
GUEST_CREATE_PER_IP_HOUR = _env_int("GUEST_CREATE_PER_IP_HOUR", 5)
# Global ceiling on guest accounts created per rolling hour, independent of IP (bounds paid LLM spend).
GUEST_CREATE_GLOBAL_HOUR = _env_int("GUEST_CREATE_GLOBAL_HOUR", 200)
# Maximum documents a guest account may upload.
GUEST_DOC_LIMIT = _env_int("GUEST_DOC_LIMIT", 3, minimum=0)
# Maximum AI generations (exercises created) per guest account; soft-deleted ones still count.
GUEST_AI_LIMIT = _env_int("GUEST_AI_LIMIT", 3, minimum=0)
# Fallback academic year ("YYYY-YYYY") used when no admin setting exists; empty -> derived from calendar.
CURRENT_ACADEMIC_YEAR = os.environ.get("CURRENT_ACADEMIC_YEAR", "").strip()
# Honor CF-Connecting-IP / X-Forwarded-For only behind a trusted reverse proxy.
TRUST_PROXY_HEADERS = _env_bool("TRUST_PROXY_HEADERS", False)
# Number of trusted proxy hops that append to X-Forwarded-For (the client IP is the Nth entry from the right).
TRUSTED_PROXY_HOPS = _env_int("TRUSTED_PROXY_HOPS", 1)


def client_ip(request) -> str:
    """Return the caller IP, honoring proxy headers only when TRUST_PROXY_HEADERS is enabled."""
    if TRUST_PROXY_HEADERS:
        cf = request.headers.get("cf-connecting-ip")
        if cf:
            return cf.strip()[:45]
        xff = request.headers.get("x-forwarded-for")
        if xff:
            # The LAST entry is appended by our own proxy; earlier entries are client-controlled and spoofable.
            parts = [p.strip() for p in xff.split(",") if p.strip()]
            if parts:
                return parts[max(-len(parts), -TRUSTED_PROXY_HOPS)][:45]
    return (request.client.host if request.client else "unknown")[:45]
