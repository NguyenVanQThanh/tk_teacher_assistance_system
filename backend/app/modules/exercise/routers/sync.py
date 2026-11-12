# File Name: sync.py
# Description: API Router for data sync endpoints — GET /api/v1/sync/version (version snapshot) and
#              GET /api/v1/sync/stream (SSE stream that pushes a `data:` event whenever the version changes).
# Created At: 2026-11-12
# Created By: AI Agent
# Updated At: 2026-11-12
# Updated By: AI Agent

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from models.models import User
from app.modules.auth.dependencies import get_current_user_query_ok
from app.modules.exercise.schemas import SyncVersionOut
from app.modules.exercise.services.sync_service import SyncService, get_cached_version_snapshot

router = APIRouter(tags=["sync"])

# How often each SSE connection polls the DB for changes.
SSE_POLL_INTERVAL_SECONDS = 2.0


@router.get("/api/v1/sync/version", response_model=SyncVersionOut)
def get_sync_version(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_query_ok)
):
    """
    Return the current data-version snapshot: {"version": <ISO8601 UTC>, "tables": {...}}.
    Any authenticated user may call this (no special permission required).
    """
    # Uses the process-wide 2s cache to stay light on the DB.
    return get_cached_version_snapshot(db=db)


@router.get("/api/v1/sync/stream")
async def sync_stream(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_query_ok)
):
    """
    Server-Sent Events stream. Each connection polls the DB every 2 seconds and emits
    `data: {"version": ..., "tables": {...}}\\n\\n` whenever the version changes for that connection.
    Any authenticated user may subscribe. Auth accepts the usual Authorization header OR
    ?token=... because browser EventSource cannot set request headers.
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        last_version = None
        try:
            while True:
                # No cache here: every connection tracks its own last emitted version.
                snapshot = SyncService(db).get_version_snapshot()
                version = snapshot.get("version")
                if version != last_version:
                    last_version = version
                    yield f"data: {json.dumps(snapshot, ensure_ascii=False)}\n\n"
                await asyncio.sleep(SSE_POLL_INTERVAL_SECONDS)
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
