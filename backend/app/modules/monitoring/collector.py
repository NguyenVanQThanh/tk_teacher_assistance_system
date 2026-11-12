# File Name: collector.py
# Description: Thread-safe, in-process collector for API request metrics.
#              Sync FastAPI endpoints run in a threadpool, so every mutation of the ring
#              buffer / pending-flush queue is guarded by a single threading.Lock.
#              The collector is intentionally dependency-free (no SQLAlchemy, no config.py):
#              it only keeps bounded in-memory data and computes realtime aggregates.
# Created At: 2026-11-13
# Created By: AI Agent
# Updated At: 2026-11-13
# Updated By: AI Agent

from __future__ import annotations

import math
import os
import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional

# Anonymous sentinel written by the middleware when a request has no usable identity.
ANONYMOUS = "anonymous"


def _env_int(name: str, default: int) -> int:
    """Read an int from the environment, falling back to ``default`` on bad input."""
    try:
        return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default


# Bounds are read once at import: they define the allocation of the ring buffer.
BUFFER_SIZE = max(1, _env_int("MONITORING_BUFFER_SIZE", 5000))
PENDING_LIMIT = max(1, _env_int("MONITORING_PENDING_LIMIT", 1000))
SERIES_BUCKET_SECONDS = max(1, _env_int("MONITORING_SERIES_BUCKET_SECONDS", 10))

TOP_ROUTES_LIMIT = 10
SLOWEST_LIMIT = 10

# Alert thresholds are read at snapshot time so operators can tune them without a restart.
DEFAULT_ALERT_P95_MS = 1000.0
DEFAULT_ALERT_ERROR_RATE = 0.05


def _env_float(name: str, default: float) -> float:
    """Read a float from the environment, falling back to ``default`` on bad input."""
    raw = os.environ.get(name)
    if raw is None or str(raw).strip() == "":
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _utc_iso(epoch: Optional[float] = None) -> str:
    """Convert an epoch timestamp (seconds) to an ISO-8601 UTC string."""
    ts = time.time() if epoch is None else epoch
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _round(value: float, digits: int = 3) -> float:
    return round(float(value), digits)


def _percentile(sorted_values: List[float], pct: float) -> float:
    """Nearest-rank percentile (p50 of [10, 20, 30, 1000] -> 20)."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    rank = math.ceil((pct / 100.0) * len(sorted_values)) - 1
    rank = max(0, min(rank, len(sorted_values) - 1))
    return float(sorted_values[rank])


def _status_class(status_code: int) -> str:
    if 100 <= status_code < 200:
        return "1xx"
    if 200 <= status_code < 300:
        return "2xx"
    if 300 <= status_code < 400:
        return "3xx"
    if 400 <= status_code < 500:
        return "4xx"
    if 500 <= status_code < 600:
        return "5xx"
    return "other"


def _metric_timestamp(metric: Dict[str, Any]) -> float:
    return _as_float(metric.get("timestamp"), 0.0)


def _metric_is_error(metric: Dict[str, Any]) -> bool:
    """Server errors only (5xx). 4xx is client traffic and stays out of the error rate/alerts."""
    if "is_error" in metric:
        return bool(metric["is_error"])
    return _as_int(metric.get("status_code")) >= 500


def _serialize_metric(metric: Dict[str, Any]) -> Dict[str, Any]:
    """Public representation of a buffered metric (used by GET /requests)."""
    ts = _metric_timestamp(metric)
    return {
        "request_id": metric.get("request_id"),
        "method": metric.get("method"),
        "route": metric.get("route"),
        "path": metric.get("path"),
        "status_code": _as_int(metric.get("status_code")),
        "duration_ms": _round(_as_float(metric.get("duration_ms"))),
        "request_bytes": _as_int(metric.get("request_bytes")),
        "response_bytes": _as_int(metric.get("response_bytes")),
        "user_ref": metric.get("user_ref") or ANONYMOUS,
        "ip_ref": metric.get("ip_ref") or ANONYMOUS,
        "is_error": _metric_is_error(metric),
        "started_at": metric.get("started_at") or _utc_iso(ts),
        "finished_at": metric.get("finished_at") or _utc_iso(ts),
        "created_at": _utc_iso(ts),
    }


class MetricsCollector:
    """Bounded, thread-safe buffer of API request metrics plus realtime aggregates."""

    def __init__(self, buffer_size: int = BUFFER_SIZE, pending_limit: int = PENDING_LIMIT) -> None:
        self._lock = threading.Lock()
        self._buffer: Deque[Dict[str, Any]] = deque(maxlen=max(1, int(buffer_size)))
        self._pending: Deque[Dict[str, Any]] = deque()
        self._pending_limit = max(1, int(pending_limit))

    # ------------------------------------------------------------------
    # Persistence switch
    # ------------------------------------------------------------------
    @staticmethod
    def persist_enabled() -> bool:
        """True unless MONITORING_PERSIST_ENABLED is explicitly disabled."""
        raw = os.environ.get("MONITORING_PERSIST_ENABLED", "1")
        return str(raw).strip().lower() not in ("0", "false", "no", "off", "disabled")

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------
    def record(self, metric: Dict[str, Any]) -> None:
        """Append one metric to the ring buffer and (when persistence is on) to the flush queue.

        Both structures are bounded: the ring buffer drops the oldest metric when full, and the
        pending queue drops its oldest entry once PENDING_LIMIT is reached. Memory therefore
        stays flat regardless of traffic or DB availability.
        """
        if not isinstance(metric, dict):
            return
        with self._lock:
            self._buffer.append(metric)
            if self.persist_enabled():
                if len(self._pending) >= self._pending_limit:
                    self._pending.popleft()
                self._pending.append(metric)

    # ------------------------------------------------------------------
    # Queue helpers
    # ------------------------------------------------------------------
    def buffer_size(self) -> int:
        with self._lock:
            return len(self._buffer)

    def pending_size(self) -> int:
        with self._lock:
            return len(self._pending)

    def flush_batch(self) -> List[Dict[str, Any]]:
        """Atomically take every pending metric out of the queue for a bulk insert."""
        with self._lock:
            batch = list(self._pending)
            self._pending.clear()
        return batch

    def requeue(self, metrics: List[Dict[str, Any]]) -> None:
        """Put a failed batch back at the front of the pending queue (bounded, oldest dropped)."""
        if not metrics:
            return
        with self._lock:
            self._pending.extendleft(reversed(metrics))
            overflow = len(self._pending) - self._pending_limit
            for _ in range(max(0, overflow)):
                self._pending.popleft()

    def reset(self) -> None:
        """Clear all in-memory state (tests / admin dev reset)."""
        with self._lock:
            self._buffer.clear()
            self._pending.clear()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def recent(
        self,
        limit: int = 100,
        route: Optional[str] = None,
        status: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Return the newest metrics first, optionally filtered by route substring / status code."""
        limit = max(1, min(_as_int(limit, 100), 500))
        route_filter = str(route).strip().lower() if route else None
        status_filter = _as_int(status, -1) if status is not None and str(status).strip() != "" else None

        with self._lock:
            items = list(self._buffer)

        results: List[Dict[str, Any]] = []
        for metric in reversed(items):
            if route_filter:
                haystack = f"{metric.get('route') or ''} {metric.get('path') or ''}".lower()
                if route_filter not in haystack:
                    continue
            if status_filter is not None and _as_int(metric.get("status_code")) != status_filter:
                continue
            results.append(_serialize_metric(metric))
            if len(results) >= limit:
                break
        return results

    def snapshot(self, window_seconds: int = 300) -> Dict[str, Any]:
        """Compute realtime aggregates over the last ``window_seconds`` seconds."""
        window = max(1, _as_int(window_seconds, 300))
        now = time.time()
        cutoff = now - window

        with self._lock:
            buffer_size = len(self._buffer)
            pending_size = len(self._pending)
            items = [m for m in self._buffer if _metric_timestamp(m) >= cutoff]

        total = len(items)
        errors = sum(1 for m in items if _metric_is_error(m))
        error_rate = (errors / total) if total else 0.0
        rps = (total / window) if window else 0.0
        rpm = rps * 60.0

        durations = sorted(_as_float(m.get("duration_ms")) for m in items)
        latency = {
            "p50": _round(_percentile(durations, 50)),
            "p95": _round(_percentile(durations, 95)),
            "p99": _round(_percentile(durations, 99)),
            "avg": _round(sum(durations) / len(durations)) if durations else 0.0,
            "min": _round(durations[0]) if durations else 0.0,
            "max": _round(durations[-1]) if durations else 0.0,
        }

        status_counts = {"1xx": 0, "2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0, "other": 0}
        for metric in items:
            status_counts[_status_class(_as_int(metric.get("status_code")))] += 1

        active_users = {
            str(m.get("user_ref"))
            for m in items
            if m.get("user_ref") and str(m.get("user_ref")) != ANONYMOUS
        }

        request_bytes = sum(max(0, _as_int(m.get("request_bytes"))) for m in items)
        response_bytes = sum(max(0, _as_int(m.get("response_bytes"))) for m in items)
        bytes_per_sec = (response_bytes / window) if window else 0.0

        return {
            "window_seconds": window,
            "generated_at": _utc_iso(now),
            "totals": {
                "requests": total,
                "errors": errors,
                "error_rate": _round(error_rate, 4),
                "requests_per_sec": _round(rps, 4),
                "requests_per_minute": _round(rpm, 3),
                "request_bytes": request_bytes,
                "response_bytes": response_bytes,
                "avg_latency_ms": latency["avg"],
            },
            "error_rate": _round(error_rate, 4),
            "rps": _round(rps, 4),
            "req_per_minute": _round(rpm, 3),
            "active_users": len(active_users),
            "throughput": {
                "requests_per_sec": _round(rps, 4),
                "requests_per_minute": _round(rpm, 3),
                "bytes_per_sec": _round(bytes_per_sec, 3),
            },
            "latency_ms": latency,
            "status_counts": status_counts,
            "top_routes": self._top_routes(items),
            "slowest": self._slowest(items),
            "series": self._series(items, cutoff, now, window),
            "alerts": self._alerts(latency, error_rate, total),
            "buffer_size": buffer_size,
            "pending": pending_size,
            "persist_enabled": self.persist_enabled(),
        }

    # ------------------------------------------------------------------
    # Snapshot helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _top_routes(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        buckets: Dict[str, Dict[str, Any]] = {}
        for metric in items:
            route = str(metric.get("route") or metric.get("path") or "unknown")
            bucket = buckets.setdefault(route, {"count": 0, "errors": 0, "durations": []})
            bucket["count"] += 1
            bucket["errors"] += 1 if _metric_is_error(metric) else 0
            bucket["durations"].append(_as_float(metric.get("duration_ms")))

        rows: List[Dict[str, Any]] = []
        for route, bucket in buckets.items():
            durations = sorted(bucket["durations"])
            count = bucket["count"]
            rows.append(
                {
                    "route": route,
                    "count": count,
                    "errors": bucket["errors"],
                    "error_rate": _round(bucket["errors"] / count, 4) if count else 0.0,
                    "avg_ms": _round(sum(durations) / len(durations)) if durations else 0.0,
                    "p95_ms": _round(_percentile(durations, 95)),
                }
            )
        rows.sort(key=lambda row: (-row["count"], -row["p95_ms"]))
        return rows[:TOP_ROUTES_LIMIT]

    @staticmethod
    def _slowest(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        ordered = sorted(items, key=lambda m: _as_float(m.get("duration_ms")), reverse=True)
        rows: List[Dict[str, Any]] = []
        for metric in ordered[:SLOWEST_LIMIT]:
            ts = _metric_timestamp(metric)
            rows.append(
                {
                    "request_id": metric.get("request_id"),
                    "method": metric.get("method"),
                    "route": metric.get("route"),
                    "path": metric.get("path"),
                    "status_code": _as_int(metric.get("status_code")),
                    "duration_ms": _round(_as_float(metric.get("duration_ms"))),
                    "started_at": metric.get("started_at") or _utc_iso(ts),
                    "finished_at": metric.get("finished_at") or _utc_iso(ts),
                }
            )
        return rows

    @staticmethod
    def _series(
        items: List[Dict[str, Any]],
        cutoff: float,
        now: float,
        window: int,
    ) -> List[Dict[str, Any]]:
        # 10s buckets for short windows, 1m buckets for longer ones (bounded point count).
        bucket_seconds = SERIES_BUCKET_SECONDS if window <= 600 else 60
        start = math.floor(cutoff / bucket_seconds) * bucket_seconds
        end = math.floor(now / bucket_seconds) * bucket_seconds

        buckets: Dict[int, Dict[str, Any]] = {}
        cursor = start
        while cursor <= end:
            buckets[cursor] = {"requests": 0, "errors": 0, "durations": []}
            cursor += bucket_seconds

        for metric in items:
            key = math.floor(_metric_timestamp(metric) / bucket_seconds) * bucket_seconds
            bucket = buckets.get(key)
            if bucket is None:
                continue
            bucket["requests"] += 1
            bucket["errors"] += 1 if _metric_is_error(metric) else 0
            bucket["durations"].append(_as_float(metric.get("duration_ms")))

        series: List[Dict[str, Any]] = []
        for key in sorted(buckets):
            bucket = buckets[key]
            durations = sorted(bucket["durations"])
            series.append(
                {
                    "timestamp": _utc_iso(key),
                    "bucket_seconds": bucket_seconds,
                    "requests": bucket["requests"],
                    "errors": bucket["errors"],
                    "p95_ms": _round(_percentile(durations, 95)),
                    "avg_ms": _round(sum(durations) / len(durations)) if durations else 0.0,
                }
            )
        return series

    @staticmethod
    def _alerts(latency: Dict[str, float], error_rate: float, total: int) -> List[Dict[str, Any]]:
        if not total:
            return []

        p95_threshold = _env_float("MONITOR_ALERT_P95_MS", DEFAULT_ALERT_P95_MS)
        error_threshold = _env_float("MONITOR_ALERT_ERROR_RATE", DEFAULT_ALERT_ERROR_RATE)

        alerts: List[Dict[str, Any]] = []
        if latency["p95"] > p95_threshold:
            alerts.append(
                {
                    "type": "latency_p95",
                    "severity": "warning",
                    "message": (
                        f"p95 latency {latency['p95']:.0f}ms exceeds "
                        f"the {p95_threshold:.0f}ms threshold"
                    ),
                    "value": latency["p95"],
                    "threshold": p95_threshold,
                }
            )
        if error_rate > error_threshold:
            alerts.append(
                {
                    "type": "error_rate",
                    "severity": "critical" if error_rate >= max(error_threshold * 2, 0.1) else "warning",
                    "message": (
                        f"error rate {error_rate * 100:.1f}% exceeds "
                        f"the {error_threshold * 100:.1f}% threshold"
                    ),
                    "value": _round(error_rate, 4),
                    "threshold": error_threshold,
                }
            )
        return alerts


# Process-wide singleton shared by the middleware, the router and the flush loop.
collector = MetricsCollector()
