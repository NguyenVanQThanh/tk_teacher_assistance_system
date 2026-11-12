# File Name: sync.py
# Description: API Router for data sync endpoints — GET /api/v1/sync/version (version snapshot) and
#              GET /api/v1/sync/stream (SSE stream that pushes a `data:` event whenever the version changes).
#              The SSE handler authenticates with a short-lived session and polls the DB with a fresh
#              short-lived session per tick inside asyncio.to_thread, so no connection is held for the
#              stream lifetime and the event loop is never blocked by SQLAlchemy.
# Created At: 2026-11-12
# Updated At: 2026-11-13
# Updated By: AI Agent

import asyncio
import json
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core import database
from app.core.database import get_db
from models.models import User
from app.modules.auth.dependencies import get_current_user, resolve_user_from_token
from app.modules.exercise.schemas import SyncVersionOut
from app.modules.exercise.services.sync_service import SyncService, get_cached_version_snapshot

router = APIRouter(tags=["sync"])

# How often each SSE connection polls the DB for changes.
SSE_POLL_INTERVAL_SECONDS = 2.0


@router.get("/api/v1/sync/version", response_model=SyncVersionOut)
def get_sync_version(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Return the current data-version snapshot: {"version": <ISO8601 UTC>, "tables": {...}}.
    Any authenticated user may call this (no special permission required).
    Auth is header-only here (Authorization: Bearer ...) — the ?token= query variant is
    reserved for the SSE stream, because EventSource cannot set request headers and JWTs
    in URLs would leak into access logs.
    """
    # Uses the process-wide 2s cache to stay light on the DB.
    return get_cached_version_snapshot(db=db)


def _authenticate_stream(request: Request, token_query: Optional[str]) -> User:
    """
    Authenticate an SSE connection. Accepts the JWT from the Authorization header OR the
    ?token= query param (EventSource cannot set headers). Uses a short-lived session that
    is closed immediately — the stream itself never holds a request-scoped DB session.
    """
    header = request.headers.get("authorization", "")
    bearer = header[7:].strip() if header.lower().startswith("bearer ") else None
    db = database.SessionLocal()
    try:
        return resolve_user_from_token(bearer or token_query, db)
    finally:
        db.close()


def _poll_version_snapshot(raw_token: Optional[str]) -> dict:
    """One DB poll with a fresh short-lived session (closed right after the query).
    Re-validates the token each tick so expired/blocked/revoked users are cut off
    (raises HTTPException, which ends the stream)."""
    db = database.SessionLocal()
    try:
        resolve_user_from_token(raw_token, db)
        return SyncService(db).get_version_snapshot()
    finally:
        db.close()


@router.get("/api/v1/sync/stream")
async def sync_stream(
    request: Request,
    token: Optional[str] = Query(None, description="JWT for EventSource clients that cannot set headers"),
):
    """
    Server-Sent Events stream. Each connection polls the DB every 2 seconds (in a worker
    thread, with a short-lived session per poll) and emits
    `data: {"version": ..., "tables": {...}}\n\n` whenever the version changes for that connection.
    Any authenticated user may subscribe.
    """
    _authenticate_stream(request, token)  # raises 401/403 on bad credentials
    header = request.headers.get("authorization", "")
    raw_token = (header[7:].strip() if header.lower().startswith("bearer ") else None) or token

    async def event_generator() -> AsyncGenerator[str, None]:
        last_version = None
        try:
            while not await request.is_disconnected():
                # No cache here: every connection tracks its own last emitted version.
                # Run the blocking aggregate queries in a worker thread, never on the event loop.
                snapshot = await asyncio.to_thread(_poll_version_snapshot, raw_token)
                version = snapshot.get("version")
                if version != last_version:
                    last_version = version
                    yield f"data: {json.dumps(snapshot, ensure_ascii=False)}\n\n"
                await asyncio.sleep(SSE_POLL_INTERVAL_SECONDS)
        except HTTPException:
            # Token expired or user blocked/deactivated mid-stream: close the stream.
            return
        except (asyncio.CancelledError, GeneratorExit):
            # Client disconnected (or server shutdown): stop the generator quietly.
            return

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
