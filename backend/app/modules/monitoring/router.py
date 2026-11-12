# File Name: router.py
# Description: Admin-only realtime monitoring API: summary snapshot, recent requests, SSE stream,
#              collector health and a dev/test reset. All routes require the Admin role; the SSE
#              endpoint authenticates with the regular Bearer header (fetch-based stream), never
#              with a query-string token.
# Created At: 2026-11-13
# Created By: AI Agent
# Updated At: 2026-11-13
# Updated By: AI Agent

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncGenerator, Dict, Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse

from app.modules.auth.dependencies import require_roles
from app.modules.monitoring.collector import collector

router = APIRouter(
    prefix="/api/v1/admin/monitoring",
    tags=["admin-monitoring"],
    dependencies=[Depends(require_roles("Admin"))],
)

# How often the SSE stream pushes a fresh snapshot.
SSE_INTERVAL_SECONDS = 2.0


@router.get("/summary")
def get_monitoring_summary(
    window_seconds: int = Query(300, ge=10, le=86400, description="Aggregation window in seconds"),
) -> Dict[str, Any]:
    """Realtime totals, latency percentiles, status counts, top routes, series and alerts."""
    return collector.snapshot(window_seconds=window_seconds)


@router.get("/requests")
def get_recent_requests(
    limit: int = Query(100, ge=1, le=500),
    route: Optional[str] = Query(None, description="Case-insensitive substring of route/path"),
    status: Optional[int] = Query(None, ge=100, le=599, description="Exact HTTP status code"),
) -> Dict[str, Any]:
    """Newest-first list of recent requests, optionally filtered by route and status code."""
    items = collector.recent(limit=limit, route=route, status=status)
    return {"requests": items, "count": len(items), "limit": limit}


@router.get("/health")
def get_monitoring_health() -> Dict[str, Any]:
    """Collector health: buffer occupancy and whether DB persistence is enabled."""
    return {
        "status": "ok",
        "buffer_size": collector.buffer_size(),
        "pending": collector.pending_size(),
        "persist_enabled": collector.persist_enabled(),
    }


@router.post("/reset")
def reset_monitoring() -> Dict[str, Any]:
    """Clear the in-memory buffer/pending queue (dev + tests; admin-only)."""
    collector.reset()
    return {"status": "ok", "reset": True}


@router.get("/stream")
async def monitoring_stream(
    request: Request,
    window_seconds: int = Query(300, ge=10, le=86400, description="Aggregation window in seconds"),
) -> StreamingResponse:
    """Server-Sent Events stream: one `data: <summary json>` event every 2 seconds.

    Auth is enforced by the router-level Admin dependency (Bearer header). EventSource cannot set
    headers, so the dashboard must consume this with `fetch()` + a ReadableStream reader.
    """
    try:
        window = int(window_seconds)
    except (TypeError, ValueError):
        # Direct invocation in tests may pass the Query default object.
        window = 300

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            while not await request.is_disconnected():
                # Snapshot is CPU-bound: keep it off the event loop.
                snapshot = await asyncio.to_thread(collector.snapshot, window)
                yield f"data: {json.dumps(snapshot, ensure_ascii=False)}\n\n"
                await asyncio.sleep(SSE_INTERVAL_SECONDS)
        except (asyncio.CancelledError, GeneratorExit):
            # Client disconnected or server shutting down: close the stream quietly.
            return

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
