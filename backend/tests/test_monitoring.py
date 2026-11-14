# File Name: test_monitoring.py
# Description: Tests for the realtime API monitoring module: X-Request-ID correlation header,
#              admin-only access, recent-request filtering, collector percentiles/alerts,
#              the SSE stream's first event and the ApiRequestMetric table.
# Created At: 2026-11-13
# Created By: AI Agent
# Updated At: 2026-11-13
# Updated By: AI Agent

import asyncio
import json
import time
import uuid

import pytest
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient
from sqlalchemy import text
from starlette.requests import Request

import models.models  # noqa: F401  (registers every table on Base.metadata)
from app.modules.monitoring.collector import collector
from app.modules.monitoring.middleware import _normalize_path
from models.base import Base


def get_admin_token(client: TestClient) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"phone": "0987654321", "password": "password123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def get_student_token(client: TestClient) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"phone": "0934567890", "password": "password123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def admin_headers(client: TestClient) -> dict:
    return {"Authorization": f"Bearer {get_admin_token(client)}"}


@pytest.fixture(autouse=True)
def clean_collector():
    """Keep the process-wide collector isolated between tests."""
    collector.reset()
    yield
    collector.reset()


def _record(duration_ms: float, status_code: int, user_ref: str = "user-a", now: float | None = None):
    timestamp = time.time() if now is None else now
    collector.record(
        {
            "request_id": uuid.uuid4().hex,
            "method": "GET",
            "route": "/api/v1/test",
            "path": "/api/v1/test",
            "status_code": status_code,
            "duration_ms": duration_ms,
            "request_bytes": 0,
            "response_bytes": 128,
            "user_ref": user_ref,
            "ip_ref": "ip-ref-123",
            "is_error": status_code >= 500,
            "timestamp": timestamp,
            "started_at": "2026-11-13T00:00:00+00:00",
            "finished_at": "2026-11-13T00:00:00.010+00:00",
        }
    )


def test_request_id_header_and_metrics(client: TestClient):
    headers = admin_headers(client)

    health = client.get("/health", headers=headers)
    assert health.status_code == 200
    assert health.headers.get("X-Request-ID"), "monitoring middleware must stamp X-Request-ID"

    # A client-supplied correlation id is preserved.
    correlated = client.get(
        "/health",
        headers={**headers, "X-Request-ID": "client-correlation-1"},
    )
    assert correlated.headers.get("X-Request-ID") == "client-correlation-1"

    exercises = client.get("/api/v1/exercises", headers=headers)
    assert exercises.status_code == 200, exercises.text
    assert exercises.headers.get("X-Request-ID")
    assert exercises.headers["X-Request-ID"] != health.headers["X-Request-ID"]

    summary = client.get("/api/v1/admin/monitoring/summary", headers=headers)
    assert summary.status_code == 200, summary.text
    body = summary.json()

    assert body["totals"]["requests"] >= 2
    assert isinstance(body["latency_ms"]["p95"], (int, float))
    assert "2xx" in body["status_counts"]
    assert isinstance(body["series"], list) and body["series"]
    assert isinstance(body["alerts"], list)


def test_monitoring_admin_only(client: TestClient):
    student = get_student_token(client)
    resp = client.get(
        "/api/v1/admin/monitoring/summary",
        headers={"Authorization": f"Bearer {student}"},
    )
    assert resp.status_code == 403

    assert client.get("/api/v1/admin/monitoring/summary").status_code == 401


def test_recent_requests_filter(client: TestClient):
    headers = admin_headers(client)

    client.get("/health", headers=headers)
    client.get("/api/v1/exercises", headers=headers)
    client.get(f"/api/v1/exercises/{uuid.uuid4()}", headers=headers)  # 404, route template kept
    client.get("/api/v1/definitely-not-a-route", headers=headers)  # 404, normalized fallback

    recent = client.get("/api/v1/admin/monitoring/requests?limit=50", headers=headers)
    assert recent.status_code == 200, recent.text
    payload = recent.json()
    assert isinstance(payload["requests"], list) and payload["requests"]
    assert payload["count"] == len(payload["requests"])

    # Authenticated requests carry an anonymized (sha256[:12]) user ref; IPs are hashed too.
    authenticated = [item for item in payload["requests"] if item["user_ref"] != "anonymous"]
    assert authenticated
    assert all(len(item["user_ref"]) == 12 for item in authenticated)
    assert all(len(item["ip_ref"]) == 12 for item in payload["requests"])

    by_route = client.get(
        "/api/v1/admin/monitoring/requests?route=/api/v1/exercises&limit=50",
        headers=headers,
    ).json()
    assert by_route["requests"]
    assert all(
        "/api/v1/exercises" in f"{item['route']} {item['path']}"
        for item in by_route["requests"]
    )

    by_status = client.get(
        "/api/v1/admin/monitoring/requests?status=404&limit=50",
        headers=headers,
    ).json()
    assert by_status["requests"]
    assert all(item["status_code"] == 404 for item in by_status["requests"])

    # The 404 for a UUID path must be recorded under the route template, not the raw UUID.
    assert any(
        item["route"] == "/api/v1/exercises/{exercise_id}"
        for item in by_status["requests"]
    )


def test_snapshot_percentiles_and_alerts():
    now = time.time()
    _record(10, 200, now=now)
    _record(20, 200, now=now)
    _record(30, 200, now=now)
    _record(1000, 500, user_ref="anonymous", now=now)
    _record(9999, 200, now=now - 3600)  # outside the 300s window

    snapshot = collector.snapshot(window_seconds=300)

    assert snapshot["totals"]["requests"] == 4
    assert snapshot["latency_ms"]["p50"] == 20
    assert snapshot["latency_ms"]["p95"] == 1000
    assert snapshot["latency_ms"]["p99"] == 1000
    assert snapshot["error_rate"] == pytest.approx(0.25)
    assert snapshot["totals"]["errors"] == 1
    assert snapshot["status_counts"]["2xx"] == 3
    assert snapshot["status_counts"]["5xx"] == 1
    assert snapshot["active_users"] == 1  # "anonymous" does not count

    alert_types = {alert["type"] for alert in snapshot["alerts"]}
    assert "error_rate" in alert_types


def test_error_rate_counts_only_server_errors():
    """401/404 are normal client traffic: they appear in status_counts but not in the error rate."""
    now = time.time()
    _record(10, 200, now=now)
    _record(10, 401, now=now)
    _record(10, 404, now=now)
    _record(10, 500, now=now)

    snapshot = collector.snapshot(window_seconds=300)

    assert snapshot["totals"]["requests"] == 4
    assert snapshot["totals"]["errors"] == 1
    assert snapshot["error_rate"] == pytest.approx(0.25)
    assert snapshot["status_counts"]["4xx"] == 2
    assert snapshot["status_counts"]["5xx"] == 1

    top_route = snapshot["top_routes"][0]
    assert top_route["count"] == 4  # 4xx still counts as route traffic
    assert top_route["errors"] == 1
    assert top_route["error_rate"] == pytest.approx(0.25)


def test_sse_first_event():
    from app.modules.monitoring.router import monitoring_stream

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/admin/monitoring/stream",
        "headers": [],
        "query_string": b"",
    }

    async def _receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    request = Request(scope, _receive)

    async def run():
        response = await monitoring_stream(request=request)
        assert isinstance(response, StreamingResponse)
        assert response.media_type == "text/event-stream"
        assert response.headers.get("cache-control") == "no-cache, no-store"
        assert response.headers.get("x-accel-buffering") == "no"
        iterator = response.body_iterator
        chunk = await iterator.__anext__()
        await iterator.aclose()
        return chunk

    chunk = asyncio.run(run())
    assert isinstance(chunk, str)
    assert chunk.startswith("data: ") and chunk.endswith("\n\n")

    payload = json.loads(chunk[len("data: "):].strip())
    assert "totals" in payload
    assert "latency_ms" in payload
    assert "series" in payload


def test_metrics_model_created(db_session):
    assert "api_request_metrics" in Base.metadata.tables
    table = Base.metadata.tables["api_request_metrics"]
    expected_columns = {
        "metric_id",
        "request_id",
        "method",
        "route",
        "path",
        "status_code",
        "duration_ms",
        "request_bytes",
        "response_bytes",
        "user_ref",
        "ip_ref",
        "is_error",
        "created_at",
    }
    assert expected_columns.issubset(set(table.columns.keys()))

    count = db_session.execute(text("SELECT COUNT(*) FROM api_request_metrics")).scalar()
    assert count == 0


def test_collector_flush_and_requeue(monkeypatch):
    monkeypatch.setenv("MONITORING_PERSIST_ENABLED", "1")
    for _ in range(3):
        _record(5, 200)

    assert collector.pending_size() == 3
    batch = collector.flush_batch()
    assert len(batch) == 3
    assert collector.pending_size() == 0
    assert collector.buffer_size() == 3

    collector.requeue(batch)
    assert collector.pending_size() == 3


def test_normalize_path_collapses_high_cardinality_values():
    assert _normalize_path("/api/v1/exercises/123") == "/api/v1/exercises/{id}"
    assert (
        _normalize_path("/api/v1/exercises/9f8c7b6a-5d4e-3f2a-1b0c-9d8e7f6a5b4c")
        == "/api/v1/exercises/{id}"
    )
    # The API version segment must never be collapsed.
    assert _normalize_path("/api/v1/definitely-not-a-route") == "/api/v1/definitely-not-a-route"
