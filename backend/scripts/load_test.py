#!/usr/bin/env python3
"""Async load test for SmartLMS (30 concurrent users by default).

Usage (from the backend/ directory, venv active):

    python scripts/load_test.py \
        --base-url http://localhost:8000 \
        --users 30 --requests-per-user 20 \
        --phone 0999000002 --password 'Teacher@1234'

The script logs in once, then runs N workers concurrently. Each worker
alternates between the two read endpoints that dominate the teacher/student
UI:

    GET /api/v1/exercises?page_size=6
    GET /api/v1/assignments

It reports p50/p95/p99 latency, RPS, total requests, error rate and status
code counts as both human-readable text and JSON. Only httpx is required
(no locust/k6 dependency).

Note: run it against the backend directly (port 8000) when measuring the app.
If you run it through Nginx, temporarily raise/disable the edge rate limit,
otherwise 429/503 responses measure the proxy, not the application.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import sys
import time
from collections import Counter
from typing import Any, Dict, List, Optional

import httpx

DEFAULT_PHONE = os.environ.get("LOAD_TEST_PHONE", "0999000002")
DEFAULT_PASSWORD = os.environ.get("LOAD_TEST_PASSWORD", "Teacher@1234")

ENDPOINTS = (
    "/api/v1/exercises?page_size=6",
    "/api/v1/assignments",
)


def _percentile(values: List[float], pct: float) -> Optional[float]:
    """Nearest-rank percentile (pct in 0..100)."""
    if not values:
        return None
    ordered = sorted(values)
    rank = max(0, min(len(ordered) - 1, math.ceil(pct / 100.0 * len(ordered)) - 1))
    return round(ordered[rank], 2)


def _latency_summary(values: List[float]) -> Dict[str, Optional[float]]:
    if not values:
        return {"p50": None, "p95": None, "p99": None, "max": None, "avg": None}
    return {
        "p50": _percentile(values, 50),
        "p95": _percentile(values, 95),
        "p99": _percentile(values, 99),
        "max": round(max(values), 2),
        "avg": round(sum(values) / len(values), 2),
    }


async def _login(client: httpx.AsyncClient, phone: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"phone": phone, "password": password},
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"Login failed (HTTP {resp.status_code}): {resp.text[:500]}"
        )
    token = resp.json().get("access_token")
    if not token:
        raise RuntimeError("Login response did not contain access_token")
    return token


async def _worker(
    worker_id: int,
    client: httpx.AsyncClient,
    headers: Dict[str, str],
    requests_per_user: int,
) -> List[Dict[str, Any]]:
    """Run one user's request loop; return one record per request."""
    results: List[Dict[str, Any]] = []
    for i in range(requests_per_user):
        endpoint = ENDPOINTS[i % len(ENDPOINTS)]
        started = time.perf_counter()
        status: Optional[int] = None
        error: Optional[str] = None
        try:
            resp = await client.get(endpoint, headers=headers)
            status = resp.status_code
            if status >= 400:
                error = f"HTTP {status}: {resp.text[:200]}"
        except Exception as exc:  # noqa: BLE001 - load test must record every failure
            error = f"{type(exc).__name__}: {exc}"
        latency_ms = (time.perf_counter() - started) * 1000.0
        results.append(
            {
                "worker": worker_id,
                "endpoint": endpoint,
                "status": status,
                "latency_ms": latency_ms,
                "error": error,
            }
        )
    return results


def _build_report(
    *,
    base_url: str,
    users: int,
    requests_per_user: int,
    wall_time_s: float,
    results: List[Dict[str, Any]],
    errors: List[Dict[str, Any]],
) -> Dict[str, Any]:
    total = len(results)
    latencies = [r["latency_ms"] for r in results]
    status_counts = Counter(
        str(r["status"]) if r["status"] is not None else "EXCEPTION"
        for r in results
    )
    error_count = sum(1 for r in results if r["error"])
    error_rate = (error_count / total * 100.0) if total else 0.0

    per_endpoint: Dict[str, Any] = {}
    for endpoint in ENDPOINTS:
        subset = [r for r in results if r["endpoint"] == endpoint]
        subset_latencies = [r["latency_ms"] for r in subset]
        per_endpoint[endpoint] = {
            "requests": len(subset),
            "errors": sum(1 for r in subset if r["error"]),
            "latency_ms": _latency_summary(subset_latencies),
        }

    return {
        "config": {
            "base_url": base_url,
            "users": users,
            "requests_per_user": requests_per_user,
            "total_requests": total,
        },
        "summary": {
            "wall_time_s": round(wall_time_s, 3),
            "rps": round(total / wall_time_s, 2) if wall_time_s > 0 else None,
            "total_requests": total,
            "error_count": error_count,
            "error_rate_pct": round(error_rate, 2),
            "status_counts": dict(sorted(status_counts.items())),
            "latency_ms": _latency_summary(latencies),
        },
        "per_endpoint": per_endpoint,
        "errors_sample": errors[:20],
    }


def _print_text(report: Dict[str, Any]) -> None:
    cfg = report["config"]
    summary = report["summary"]
    lat = summary["latency_ms"]
    print("=== SmartLMS load test ===")
    print(f"Base URL        : {cfg['base_url']}")
    print(
        f"Workload        : {cfg['users']} users x {cfg['requests_per_user']} "
        f"requests = {cfg['total_requests']} requests"
    )
    print(f"Wall time       : {summary['wall_time_s']} s")
    print(f"RPS             : {summary['rps']}")
    print(
        "Latency (ms)    : "
        f"p50={lat['p50']} p95={lat['p95']} p99={lat['p99']} "
        f"avg={lat['avg']} max={lat['max']}"
    )
    print(
        f"Errors          : {summary['error_count']}/{summary['total_requests']} "
        f"({summary['error_rate_pct']}%)"
    )
    print(f"Status counts   : {summary['status_counts']}")
    print("Per endpoint:")
    for endpoint, stats in report["per_endpoint"].items():
        e_lat = stats["latency_ms"]
        print(
            f"  {endpoint}: n={stats['requests']} errors={stats['errors']} "
            f"p50={e_lat['p50']} p95={e_lat['p95']} p99={e_lat['p99']}"
        )
    if report["errors_sample"]:
        print("First errors:")
        for err in report["errors_sample"][:5]:
            print(f"  worker={err['worker']} {err['endpoint']} -> {err['error']}")


async def _run(args: argparse.Namespace) -> int:
    base_url = args.base_url.rstrip("/")
    timeout = httpx.Timeout(
        connect=min(10.0, args.timeout),
        read=args.timeout,
        write=args.timeout,
        pool=args.timeout,
    )
    limits = httpx.Limits(
        max_connections=max(10, args.users * 2),
        max_keepalive_connections=max(10, args.users),
    )

    async with httpx.AsyncClient(
        base_url=base_url,
        timeout=timeout,
        limits=limits,
        headers={"User-Agent": "smartlms-load-test/1.0"},
    ) as client:
        try:
            token = await _login(client, args.phone, args.password)
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2

        headers = {"Authorization": f"Bearer {token}"}
        started = time.perf_counter()
        batches = await asyncio.gather(
            *(
                _worker(i, client, headers, args.requests_per_user)
                for i in range(args.users)
            )
        )
        wall_time_s = time.perf_counter() - started

    results = [item for batch in batches for item in batch]
    errors = [r for r in results if r["error"]]
    report = _build_report(
        base_url=base_url,
        users=args.users,
        requests_per_user=args.requests_per_user,
        wall_time_s=wall_time_s,
        results=results,
        errors=errors,
    )

    _print_text(report)
    print("\nJSON report:")
    print(json.dumps(report, indent=2, ensure_ascii=False))

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)
        print(f"\nJSON report written to {args.json_out}", file=sys.stderr)

    return 0


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Async SmartLMS load test (exercises + assignments endpoints)."
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("LOAD_TEST_BASE_URL", "http://localhost:8000"),
        help="Backend base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--users",
        type=int,
        default=int(os.environ.get("LOAD_TEST_DEFAULT_USERS", "30")),
        help="Concurrent users/workers (default: 30)",
    )
    parser.add_argument(
        "--requests-per-user",
        type=int,
        default=20,
        help="Requests per worker (default: 20)",
    )
    parser.add_argument(
        "--phone",
        default=DEFAULT_PHONE,
        help=f"Login phone (default: LOAD_TEST_PHONE or {DEFAULT_PHONE})",
    )
    parser.add_argument(
        "--password",
        default=DEFAULT_PASSWORD,
        help="Login password (default: LOAD_TEST_PASSWORD or the seed teacher password)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Per-request timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--json-out",
        default=None,
        help="Optional path to write the JSON report",
    )
    args = parser.parse_args(argv)
    if args.users < 1:
        parser.error("--users must be >= 1")
    if args.requests_per_user < 1:
        parser.error("--requests-per-user must be >= 1")
    return args


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)
    try:
        return asyncio.run(_run(args))
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
