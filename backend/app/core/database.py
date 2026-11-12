# File Name: database.py
# Description: Database session setup and get_db dependency.
# Created At: 2026-07-17
# Created By: Tam Khang
# Updated At: 2026-11-13
# Updated By: AI Agent

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

# Load environment variables
load_dotenv()


def _env_int(name: str, default: int, minimum: int = 1) -> int:
    """Read an integer env var, falling back to the default on missing/bad input."""
    try:
        value = int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(minimum, value)


# Read database configuration from the environment
DB_USERNAME = os.environ.get("DB_USERNAME") or os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME")

if not all([DB_USERNAME, DB_PASSWORD, DB_NAME]):
    raise ValueError("Missing database configuration in environment variables")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ---------------------------------------------------------------------------
# Connection pool / timeouts
#
# 30 concurrent users are served by a small pool instead of an unbounded one:
#   pool_size=20 + max_overflow=30 -> at most 50 physical connections per
#   backend process (per uvicorn worker). A request waits at most pool_timeout
#   seconds for a free connection, then fails fast instead of queueing forever.
#   The extra headroom matters because the X-Data-Version middleware opens a
#   short-lived second session while the request's own session is still held.
#   pool_pre_ping drops stale connections after a DB restart/network blip;
#   pool_recycle=1800s avoids server-side idle timeouts.
#
# PostgreSQL also gets a server-side statement_timeout so a slow query cannot
# pin a pooled connection indefinitely. SQLite (unit tests / local tooling)
# keeps its own pool class, so pool sizing args are only applied to non-SQLite
# backends; tests still create their own engine and are unaffected.
# ---------------------------------------------------------------------------
_db_url = make_url(DATABASE_URL)
_db_backend = _db_url.get_backend_name()

_engine_kwargs = {
    "pool_pre_ping": True,
    "pool_recycle": _env_int("DB_POOL_RECYCLE", 1800),
}

if _db_backend != "sqlite":
    _engine_kwargs.update(
        pool_size=_env_int("DB_POOL_SIZE", 20),
        max_overflow=_env_int("DB_MAX_OVERFLOW", 30, minimum=0),
        pool_timeout=_env_int("DB_POOL_TIMEOUT", 10),
    )

if _db_backend == "postgresql":
    _statement_timeout_ms = _env_int("DB_STATEMENT_TIMEOUT_MS", 30000)
    _engine_kwargs["connect_args"] = {
        "options": f"-c statement_timeout={_statement_timeout_ms}"
    }

engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
