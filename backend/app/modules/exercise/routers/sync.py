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
import time
from typing import AsyncGenerator, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core import database
from app.core.database import get_db
from models.models import User
from app.core.security import create_stream_ticket
from app.modules.auth.dependencies import ensure_active_user, get_current_user, resolve_user_from_token
from app.modules.exercise.schemas import SyncVersionOut
from app.modules.exercise.services.sync_service import SyncService, get_cached_version_snapshot

router = APIRouter(tags=["sync"])

# How often each SSE connection polls the DB for changes.
SSE_POLL_INTERVAL_SECONDS = 2.0

# Idle connections are closed by proxies: Cloudflare drops a stream that stays silent for
# ~100s (524), and nginx has its own read timeout. A comment line keeps the connection warm
# without waking the client (SSE comments are ignored by EventSource).
SSE_HEARTBEAT_SECONDS = 15.0


@router.get("/api/v1/sync/version", response_model=SyncVersionOut)
def get_sync_version(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Return the current data-version snapshot: {"version": <ISO8601 UTC>, "tables": {...}}.
    Any authenticated user may call this (no special permission required).
    Auth is header-only (Authorization: Bearer ...); access tokens never travel in URLs.
    """
    # Uses the process-wide 2s cache to stay light on the DB.
    return get_cached_version_snapshot(db=db)


@router.post("/api/v1/sync/stream-ticket")
def create_sync_stream_ticket(current_user: User = Depends(get_current_user)):
    """
    Issue a 30-second, single-purpose ticket for GET /api/v1/sync/stream?ticket=...
    EventSource cannot set headers and the access token must not sit in a URL (logs,
    history, proxies). The ticket is rejected by every other endpoint.
    """
    return {"ticket": create_stream_ticket(current_user.user_id), "expires_in": 30}


def _authenticate_stream(request: Request, ticket: Optional[str]) -> UUID:
    """Authenticate an SSE connection once at connect: Bearer header or ?ticket=.
    Returns the user id. Uses a short-lived session closed immediately."""
    header = request.headers.get("authorization", "")
    bearer = header[7:].strip() if header.lower().startswith("bearer ") else None
    db = database.SessionLocal()
    try:
        if bearer:
            return resolve_user_from_token(bearer, db).user_id
        return resolve_user_from_token(ticket, db, expect_ticket=True).user_id
    finally:
        db.close()


def _poll_version_snapshot(user_id: UUID) -> dict:
    """One DB poll with a fresh short-lived session. Re-checks the account each tick so
    blocked/inactive/deleted users are cut off (raises HTTPException, ending the stream).
    The ticket itself is only valid for connecting; the open stream is bound to the user."""
    db = database.SessionLocal()
    try:
        ensure_active_user(db, user_id)
        return SyncService(db).get_version_snapshot()
    finally:
        db.close()


@router.get("/api/v1/sync/stream")
async def sync_stream(
    request: Request,
    ticket: Optional[str] = Query(None, description="Short-lived ticket from POST /sync/stream-ticket"),
):
    """
    Server-Sent Events stream. Each connection polls the DB every 2 seconds (in a worker
    thread, with a short-lived session per poll) and emits
    `data: {"version": ..., "tables": {...}}\n\n` whenever the version changes for that connection.
    Any authenticated user may subscribe.
    """
    user_id = _authenticate_stream(request, ticket)  # raises 401/403 on bad credentials

    async def event_generator() -> AsyncGenerator[str, None]:
        last_version = None
        last_emit = time.monotonic()
        try:
            while not await request.is_disconnected():
                # No cache here: every connection tracks its own last emitted version.
                # Run the blocking aggregate queries in a worker thread, never on the event loop.
                snapshot = await asyncio.to_thread(_poll_version_snapshot, user_id)
                version = snapshot.get("version")
                if version != last_version:
                    last_version = version
                    last_emit = time.monotonic()
                    yield f"data: {json.dumps(snapshot, ensure_ascii=False)}\n\n"
                elif time.monotonic() - last_emit >= SSE_HEARTBEAT_SECONDS:
                    # Keep the connection alive through Cloudflare/nginx while nothing changes.
                    last_emit = time.monotonic()
                    yield ": keep-alive\n\n"
                await asyncio.sleep(SSE_POLL_INTERVAL_SECONDS)
        except HTTPException:
            # User blocked/deactivated mid-stream: close the stream.
            return
        except (asyncio.CancelledError, GeneratorExit):
            # Client disconnected (or server shutdown): stop the generator quietly.
            return

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store",
            # The ticket sits in the URL: never forward it via Referer.
            "Referrer-Policy": "no-referrer",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
