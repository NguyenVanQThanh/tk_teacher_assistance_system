# File Name: middleware.py
# Description: HTTP middleware that records one ApiRequestMetric per API request and adds the
#              correlation id / static cache headers. Monitoring must never break a request:
#              metric building and recording are wrapped in try/except and failures are logged
#              at debug level only.
# Created At: 2026-11-13
# Created By: AI Agent
# Updated At: 2026-11-13
# Updated By: AI Agent

from __future__ import annotations

import hashlib
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Request
from jose import jwt as jose_jwt

from app.modules.monitoring.collector import ANONYMOUS, collector

logger = logging.getLogger("smartlms.monitoring")

# Static files / docs are not API traffic. The monitoring SSE stream is skipped as well:
# measuring a long-lived stream would record its whole lifetime as latency. The existing
# sync SSE stream is skipped for the same reason.
_SKIP_PREFIXES = ("/uploads", "/sgk-images", "/docs", "/redoc")
_SKIP_EXACT = {
    "/openapi.json",
    "/favicon.ico",
    "/api/v1/admin/monitoring/stream",
    "/api/v1/sync/stream",
}

_UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
# Only whole numeric path segments are collapsed: /api/v1/... must keep its version.
_NUMERIC_SEGMENT_RE = re.compile(r"(?<=/)\d+(?=/|$)")


def _utc_iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


def _hash_ref(value: str) -> str:
    """Anonymize an identifier: sha256 hex digest truncated to 12 characters."""
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:12]


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _should_skip(request: Request) -> bool:
    if request.method.upper() == "OPTIONS":
        # CORS preflight noise: not application traffic.
        return True
    path = request.url.path or ""
    if path in _SKIP_EXACT:
        return True
    return any(path == prefix or path.startswith(prefix + "/") for prefix in _SKIP_PREFIXES)


def _request_id(request: Request) -> str:
    raw = request.headers.get("x-request-id")
    if raw:
        cleaned = raw.strip()[:64]
        if cleaned:
            return cleaned
    return uuid.uuid4().hex


def _normalize_path(path: str) -> str:
    """Collapse high-cardinality path values so the route dimension stays bounded."""
    normalized = _UUID_RE.sub("{id}", path or "")
    normalized = _NUMERIC_SEGMENT_RE.sub("{id}", normalized)
    return normalized[:512]


def _route_template(request: Request) -> str:
    """Prefer the FastAPI route template (e.g. /api/v1/exercises/{exercise_id})."""
    route = request.scope.get("route")
    route_path = getattr(route, "path", None)
    if isinstance(route_path, str) and route_path:
        return route_path[:255]
    return _normalize_path(request.url.path or "")[:255]


def _user_ref(request: Request) -> str:
    """Derive a stable, anonymized user reference from the JWT `sub` claim.

    Uses get_unverified_claims only: the middleware must not query the DB or re-validate the
    token (the endpoint's own auth dependency is authoritative). Any problem -> anonymous.
    """
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        return ANONYMOUS
    token = header[7:].strip()
    if not token:
        return ANONYMOUS
    try:
        claims = jose_jwt.get_unverified_claims(token)
        subject = claims.get("sub") if isinstance(claims, dict) else None
        if subject:
            return _hash_ref(str(subject))
    except Exception:
        # Expired/malformed/stream-ticket tokens are all simply anonymous here.
        return ANONYMOUS
    return ANONYMOUS


def _ip_ref(request: Request) -> str:
    client = request.client
    host = getattr(client, "host", None) if client is not None else None
    if not host:
        return ANONYMOUS
    return _hash_ref(str(host))


def _record_metric(
    request: Request,
    request_id: str,
    status_code: int,
    started_perf: float,
    started_epoch: float,
    response: Optional[Any] = None,
) -> None:
    """Build and record one metric. Never raises."""
    try:
        finished_epoch = time.time()
        duration_ms = max(0.0, (time.perf_counter() - started_perf) * 1000.0)

        request_bytes = _safe_int(request.headers.get("content-length"))
        response_bytes = 0
        if response is not None:
            response_bytes = _safe_int(response.headers.get("content-length"))
            if not response_bytes:
                body = getattr(response, "body", None)
                if isinstance(body, (bytes, bytearray)):
                    response_bytes = len(body)

        metric = {
            "request_id": request_id,
            "method": request.method.upper()[:10],
            "route": _route_template(request),
            "path": (request.url.path or "")[:512],
            "status_code": int(status_code),
            "duration_ms": round(duration_ms, 3),
            "request_bytes": max(0, request_bytes),
            "response_bytes": max(0, response_bytes),
            "user_ref": _user_ref(request),
            "ip_ref": _ip_ref(request),
            # Only 5xx is a server error. 4xx (401/404/...) is normal client traffic and must
            # not trigger the error-rate alert; it is still counted in status_counts.
            "is_error": int(status_code) >= 500,
            "timestamp": finished_epoch,
            "started_at": _utc_iso(started_epoch),
            "finished_at": _utc_iso(finished_epoch),
        }
        collector.record(metric)
    except Exception:
        # Monitoring is best-effort: a broken metric must never fail the request.
        logger.debug("Failed to record API request metric", exc_info=True)


async def monitoring_middleware(request: Request, call_next):
    """Record latency/status/size/identity for every API request and stamp X-Request-ID."""
    if _should_skip(request):
        return await call_next(request)

    request_id = _request_id(request)
    try:
        request.state.request_id = request_id
    except Exception:
        logger.debug("Failed to set request.state.request_id", exc_info=True)

    started_perf = time.perf_counter()
    started_epoch = time.time()

    try:
        response = await call_next(request)
    except Exception:
        # Unhandled exception -> ServerErrorMiddleware will produce the 500 response.
        _record_metric(request, request_id, 500, started_perf, started_epoch)
        raise

    _record_metric(
        request,
        request_id,
        response.status_code,
        started_perf,
        started_epoch,
        response=response,
    )

    try:
        response.headers["X-Request-ID"] = request_id
    except Exception:
        logger.debug("Failed to set X-Request-ID header", exc_info=True)
    return response


async def static_cache_middleware(request: Request, call_next):
    """Add a long-lived Cache-Control header to read-only static mounts."""
    response = await call_next(request)
    path = request.url.path or ""
    if path.startswith(("/uploads", "/sgk-images")) and response.status_code in (200, 206, 304):
        response.headers.setdefault("Cache-Control", "public, max-age=86400")
    return response
