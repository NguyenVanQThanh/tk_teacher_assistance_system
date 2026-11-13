# File Name: bootstrap_admin.py
# Description: Idempotently create the primary Admin account (and the RBAC rows it needs)
#              on a freshly migrated production database.
# Created At: 2026-11-14
# Created By: AI Agent
# Updated At: 2026-11-14
# Updated By: AI Agent

"""Bootstrap the primary Admin account on a database built only from migrations.

Why this exists: `alembic upgrade head` creates tables but never inserts data, and
`app/scripts/seed.py` is a developer CLI that is not run in production. A production
database therefore starts with zero roles, zero permissions and zero users — and
because login is by PHONE NUMBER only, there is no way to get in.

Run from backend/docker/entrypoint.sh right after `alembic upgrade head`:

    ADMIN_PHONE        required — login identifier (phone, e.g. 0999000001)
    ADMIN_PASSWORD     required — plain password, hashed with bcrypt before storage
    ADMIN_EMAIL        optional — stored as-is, email login is NOT supported
    ADMIN_FULL_NAME    optional — defaults to "System Administrator"
    ADMIN_RESET_PASSWORD  optional — "1"/"true" forces the password back to ADMIN_PASSWORD

Behaviour:
  * Missing ADMIN_PHONE and ADMIN_PASSWORD -> prints a skip notice, exits 0, so dev
    and CI containers keep starting exactly as before.
  * Only one of the two set -> error (almost always a half-filled secret).
  * Existing account -> reused; password untouched unless ADMIN_RESET_PASSWORD is on,
    so redeploying never locks the administrator out.
  * Account whose phone belongs to a non-Admin user -> error instead of silently
    promoting a teacher/student to administrator.
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure backend root is in sys.path (mirrors app/scripts/seed.py so this file can be
# executed directly as `python /app/app/scripts/bootstrap_admin.py`).
backend_root = str(Path(__file__).resolve().parent.parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from sqlalchemy.orm import Session

from models.models import User
from app.core.security import get_password_hash
from app.scripts.rbac_seed import seed_rbac

DEFAULT_FULL_NAME = "System Administrator"
MIN_PASSWORD_LENGTH = 8
PHONE_MIN_LENGTH = 6
PHONE_MAX_LENGTH = 20

# Values shipped in deploy/.env.prod.example. Creating an account with one of these
# would hand out a publicly documented administrator password.
PLACEHOLDER_MARKERS = (
    "doi-mat-khau",
    "change-me",
    "changeme",
    "your-password",
    "mat-khau",
)

TRUTHY = {"1", "true", "yes", "y", "on"}


class AdminBootstrapError(RuntimeError):
    """Raised when the requested admin account cannot be created safely."""


def mask_phone(phone: str) -> str:
    """Show enough of the phone to recognise the account without logging it in full."""
    if not phone:
        return ""
    if len(phone) <= 4:
        return phone[0] + "*" * (len(phone) - 1)
    if len(phone) <= 6:
        return phone[:1] + "*" * (len(phone) - 2) + phone[-1:]
    return f"{phone[:3]}{'*' * (len(phone) - 6)}{phone[-3:]}"


def _validate(phone: str, password: str) -> None:
    if not phone:
        raise AdminBootstrapError("ADMIN_PHONE is empty")
    if not PHONE_MIN_LENGTH <= len(phone) <= PHONE_MAX_LENGTH:
        raise AdminBootstrapError(
            f"ADMIN_PHONE must be {PHONE_MIN_LENGTH}-{PHONE_MAX_LENGTH} characters, got {len(phone)}"
        )
    if not password:
        raise AdminBootstrapError("ADMIN_PASSWORD is empty")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise AdminBootstrapError(
            f"ADMIN_PASSWORD must be at least {MIN_PASSWORD_LENGTH} characters, got {len(password)}"
        )
    lowered = password.lower()
    for marker in PLACEHOLDER_MARKERS:
        if marker in lowered:
            raise AdminBootstrapError(
                f"ADMIN_PASSWORD still looks like a template placeholder (contains {marker!r}). "
                "Set a real password in deploy/.env.prod or the ADMIN_PASSWORD secret."
            )


def bootstrap_admin(
    session: Session,
    *,
    phone: str,
    password: str,
    email: Optional[str] = None,
    full_name: str = DEFAULT_FULL_NAME,
    reset_password: bool = False,
) -> Dict[str, Any]:
    """Create the Admin account if missing and return a summary of what happened.

    The caller owns the transaction: this function only flushes, never commits.
    Raises AdminBootstrapError when the request is unsafe or inconsistent.
    """
    phone = (phone or "").strip()
    email = (email or "").strip() or None
    full_name = (full_name or "").strip() or DEFAULT_FULL_NAME
    _validate(phone, password or "")

    roles = seed_rbac(session)
    admin_role = roles.get("Admin")
    if admin_role is None:
        raise AdminBootstrapError("role 'Admin' is still missing after seeding RBAC")

    existing = session.query(User).filter(User.phone == phone).first()

    if existing is None:
        user = User(
            user_id=uuid.uuid4(),
            phone=phone,
            email=email,
            password_hash=get_password_hash(password),
            full_name=full_name,
            role_id=admin_role.role_id,
            status="ACTIVE",
        )
        session.add(user)
        session.flush()
        return {
            "action": "created",
            "user_id": str(user.user_id),
            "phone": user.phone,
            "email": user.email,
            "role": "Admin",
        }

    # The phone already exists: never hijack a different role.
    if existing.role_id != admin_role.role_id:
        raise AdminBootstrapError(
            f"phone {mask_phone(phone)} already belongs to a non-Admin account. "
            "Pick another ADMIN_PHONE instead of promoting an existing user."
        )

    changes = []
    if reset_password:
        existing.password_hash = get_password_hash(password)
        changes.append("password")
    # Only fill blanks — an administrator may have edited these in the UI.
    if email and not existing.email:
        existing.email = email
        changes.append("email")
    if full_name and not existing.full_name:
        existing.full_name = full_name
        changes.append("full_name")
    if existing.status != "ACTIVE":
        existing.status = "ACTIVE"
        changes.append("status")

    if changes:
        session.flush()

    return {
        "action": "updated" if changes else "unchanged",
        "user_id": str(existing.user_id),
        "phone": existing.phone,
        "email": existing.email,
        "role": "Admin",
        "changes": changes,
    }


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def main() -> int:
    phone = _env("ADMIN_PHONE")
    password = _env("ADMIN_PASSWORD")

    if not phone and not password:
        print(
            "bootstrap_admin: ADMIN_PHONE/ADMIN_PASSWORD not set - skipping. "
            "No account is created (fine for dev/CI)."
        )
        return 0

    if not phone or not password:
        missing = "ADMIN_PHONE" if not phone else "ADMIN_PASSWORD"
        print(f"bootstrap_admin: ERROR - {missing} is empty but the other one is set.")
        return 1

    reset_password = _env("ADMIN_RESET_PASSWORD").lower() in TRUTHY

    # Imported lazily so unit tests can exercise bootstrap_admin() with their own
    # session without requiring DB_* environment variables at import time.
    from app.core.database import SessionLocal

    session = SessionLocal()
    try:
        result = bootstrap_admin(
            session,
            phone=phone,
            password=password,
            email=_env("ADMIN_EMAIL"),
            full_name=_env("ADMIN_FULL_NAME") or DEFAULT_FULL_NAME,
            reset_password=reset_password,
        )
        session.commit()
    except AdminBootstrapError as exc:
        session.rollback()
        print(f"bootstrap_admin: ERROR - {exc}")
        return 1
    except Exception as exc:  # noqa: BLE001 - surface any DB problem as a clear failure
        session.rollback()
        print(f"bootstrap_admin: ERROR - unexpected failure: {exc}")
        return 1
    finally:
        session.close()

    detail = result["action"]
    if result.get("changes"):
        detail += f" ({', '.join(result['changes'])})"
    print(
        f"bootstrap_admin: admin {mask_phone(result['phone'])} -> {detail}, role={result['role']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
