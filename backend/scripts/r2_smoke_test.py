# File Name: r2_smoke_test.py
# Description: End-to-end smoke test against a REAL Cloudflare R2 bucket.
#              Exercises the same code path the app uses (app.core.storage), not a mock.
# Created At: 2026-11-14
# Created By: AI Agent
# Updated At: 2026-11-14
# Updated By: AI Agent

"""Verify the configured storage backend against the real bucket.

Why this exists: `backend/tests/test_storage.py` monkeypatches boto3, so the unit
suite proves the *logic* but never proves the credentials, the bucket name, the
endpoint, the permissions or the public domain actually work. This script does.

Run from the backend directory (reads backend/.env via load_dotenv):

    python scripts/r2_smoke_test.py

Optional flags:
    --keep   do not delete the test object (useful to inspect it in the dashboard)
    --key    custom object key (default: _smoke/<timestamp>-<random>.txt)

Exit code 0 = everything works. Non-zero = the first failing step is printed with
the reason, so a broken deploy is caught here instead of by a user hitting a 500.
"""

from __future__ import annotations

import argparse
import os
import secrets
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# .env must be loaded BEFORE app.core.config is imported: config.py reads
# os.environ at import time (the app does the same in app/main.py).
from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))
load_dotenv(BACKEND_ROOT / ".env")

from app.core import config  # noqa: E402
from app.core.storage import (  # noqa: E402
    REMOTE_BACKENDS,
    get_storage,
    read_bytes_from_url,
)

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"

# Cloudflare's Browser Integrity Check rejects the default Python-urllib signature
# with `403 error code: 1010`. Browsers (the real consumer of these URLs) are fine.
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

results: list[tuple[str, str, str]] = []


def record(step: str, status: str, detail: str = "") -> None:
    results.append((step, status, detail))
    mark = {PASS: "[ok]  ", FAIL: "[FAIL]", SKIP: "[skip]"}[status]
    print(f"{mark} {step}" + (f" -> {detail}" if detail else ""))


def mask(value: str, keep: int = 4) -> str:
    if not value:
        return "(empty)"
    if len(value) <= keep:
        return "*" * len(value)
    return value[:keep] + "*" * (len(value) - keep)


def show_config() -> None:
    backend = (config.STORAGE_BACKEND or "local").strip().lower()
    print("=== Cau hinh dang dung ===")
    print(f"  STORAGE_BACKEND      = {backend}")
    print(f"  R2_ACCOUNT_ID        = {mask(config.R2_ACCOUNT_ID, 6)}")
    print(f"  R2_ACCESS_KEY_ID     = {mask(config.R2_ACCESS_KEY_ID)}")
    print(f"  R2_SECRET_ACCESS_KEY = {mask(config.R2_SECRET_ACCESS_KEY, 2)}")
    print(f"  R2_BUCKET            = {config.R2_BUCKET or '(empty)'}")
    print(f"  R2_PUBLIC_BASE_URL   = {config.R2_PUBLIC_BASE_URL or '(empty)'}")
    print()


def http_get(url: str, timeout: float = 20.0) -> tuple[int, bytes, str]:
    """GET a public URL the way a browser would.

    The User-Agent matters: Cloudflare's Browser Integrity Check answers
    `403 error code: 1010` to the default `Python-urllib/x.y` signature, which
    looks like a broken bucket but is really bot protection. A real browser
    (and therefore the app's <img> tags) is unaffected, so send a browser UA.
    """
    request = urllib.request.Request(url, method="GET", headers={"User-Agent": BROWSER_UA})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read(), response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()[:400], exc.headers.get("Content-Type", "") if exc.headers else ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", action="store_true", help="keep the test object in the bucket")
    parser.add_argument("--key", default="", help="custom object key")
    args = parser.parse_args()

    show_config()

    backend = (config.STORAGE_BACKEND or "local").strip().lower()
    if backend not in REMOTE_BACKENDS:
        record(
            "backend la r2",
            FAIL,
            f"STORAGE_BACKEND={backend!r}; dat STORAGE_BACKEND=r2 trong backend/.env",
        )
        return finish()
    record("backend la r2", PASS, backend)

    # --- 1. Build the backend (validates every required env var) ---------------
    try:
        storage = get_storage()
    except Exception as exc:  # noqa: BLE001
        record("khoi tao R2Storage", FAIL, f"{type(exc).__name__}: {exc}")
        return finish()
    record("khoi tao R2Storage", PASS, type(storage).__name__)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    key = args.key or f"_smoke/{stamp}-{secrets.token_hex(4)}.txt"
    payload = (
        "SmartLMS R2 smoke test\n"
        f"key={key}\n"
        f"time={stamp}\n"
        "Tiếng Việt có dấu: đề thi, hình ảnh, câu hỏi.\n"
    ).encode("utf-8")

    # --- 2. put ---------------------------------------------------------------
    try:
        storage.put(key, payload, content_type="text/plain; charset=utf-8")
    except Exception as exc:  # noqa: BLE001
        record("put_object", FAIL, f"{type(exc).__name__}: {exc}")
        return finish()
    record("put_object", PASS, f"{len(payload)} bytes -> {key}")

    try:
        # --- 3. exists --------------------------------------------------------
        if storage.exists(key):
            record("head_object (exists)", PASS)
        else:
            record("head_object (exists)", FAIL, "vua put ma exists() = False")

        # --- 4. size ----------------------------------------------------------
        size = storage.size(key)
        record(
            "size",
            PASS if size == len(payload) else FAIL,
            f"{size} bytes" + ("" if size == len(payload) else f" (mong doi {len(payload)})"),
        )

        # --- 5. get -----------------------------------------------------------
        fetched = storage.get(key)
        record(
            "get_object round-trip",
            PASS if fetched == payload else FAIL,
            f"{len(fetched)} bytes" + ("" if fetched == payload else " (noi dung KHAC)"),
        )

        # --- 6. url() + key_from_url() ---------------------------------------
        url = storage.url(key)
        expected_prefix = (config.R2_PUBLIC_BASE_URL or "").rstrip("/") + "/"
        if url.startswith(expected_prefix):
            record("url() dung R2_PUBLIC_BASE_URL", PASS, url)
        else:
            record("url() dung R2_PUBLIC_BASE_URL", FAIL, f"{url} (mong doi {expected_prefix}...)")

        round_trip = storage.key_from_url(url)
        record(
            "key_from_url() round-trip",
            PASS if round_trip == key else FAIL,
            f"{round_trip!r}",
        )

        # --- 7. read_bytes_from_url (duong di cua pdf_export) ----------------
        try:
            via_helper = read_bytes_from_url(url)
            record(
                "read_bytes_from_url",
                PASS if via_helper == payload else FAIL,
                f"{len(via_helper)} bytes",
            )
        except Exception as exc:  # noqa: BLE001
            record("read_bytes_from_url", FAIL, f"{type(exc).__name__}: {exc}")

        # --- 8. public URL that the browser will actually load ---------------
        status, body, content_type = http_get(url)
        if status == 200 and body == payload:
            record("GET public URL", PASS, f"200, {content_type}")
        elif status == 200:
            record("GET public URL", FAIL, f"200 nhung noi dung khac ({len(body)} bytes)")
        elif b"1010" in body:
            record(
                "GET public URL",
                FAIL,
                "HTTP 403 error 1010 - Cloudflare chan User-Agent (bot protection), khong phai loi bucket",
            )
        elif status in (403, 404):
            record(
                "GET public URL",
                FAIL,
                f"HTTP {status} - custom domain chua Active, hoac bucket chua bat public access",
            )
        else:
            record("GET public URL", FAIL, f"HTTP {status}: {body[:200]!r}")

        # --- 9. missing key -> FileNotFoundError, not a 500 ------------------
        missing_key = f"_smoke/definitely-missing-{secrets.token_hex(6)}.txt"
        try:
            storage.get(missing_key)
            record("get key khong ton tai", FAIL, "khong nem FileNotFoundError")
        except FileNotFoundError:
            record("get key khong ton tai", PASS, "FileNotFoundError")
        except Exception as exc:  # noqa: BLE001
            record("get key khong ton tai", FAIL, f"{type(exc).__name__}: {exc}")
    finally:
        # --- 10. delete ------------------------------------------------------
        if args.keep:
            record("delete_object", SKIP, f"--keep, giu lai {key}")
        else:
            try:
                storage.delete(key)
                record(
                    "delete_object",
                    PASS if not storage.exists(key) else FAIL,
                    "da xoa" if not storage.exists(key) else "van con ton tai",
                )
            except Exception as exc:  # noqa: BLE001
                record("delete_object", FAIL, f"{type(exc).__name__}: {exc}")

    return finish()


def finish() -> int:
    failed = [r for r in results if r[1] == FAIL]
    skipped = [r for r in results if r[1] == SKIP]
    print()
    print(f"=== Ket qua: {len(results) - len(failed) - len(skipped)} pass, "
          f"{len(failed)} fail, {len(skipped)} skip ===")
    if failed:
        print("\nCac buoc that bai:")
        for step, _, detail in failed:
            print(f"  - {step}: {detail}")
        return 1
    print("R2 hoat dong day du: ghi, doc, xoa, URL public deu OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
