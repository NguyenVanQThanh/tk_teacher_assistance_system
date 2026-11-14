# File Name: test_bootstrap_admin.py
# Description: Tests for the production admin bootstrap (RBAC seeding + primary Admin account).
# Created At: 2026-11-14
# Created By: AI Agent
# Updated At: 2026-11-14
# Updated By: AI Agent

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.base import Base
from models.models import Permission, Role, RolePermission, User
from app.core.security import get_password_hash, verify_password
from app.scripts.bootstrap_admin import (
    AdminBootstrapError,
    bootstrap_admin,
    main,
    mask_phone,
)
from app.scripts.rbac_seed import PERMISSIONS, ROLE_PERMISSIONS, seed_rbac

ADMIN_PHONE = "0999000001"
ADMIN_PASSWORD = "Admin@12345"


@pytest.fixture()
def session():
    """Fresh in-memory database per test, so counts never leak between cases."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


# ---------------------------------------------------------------------------
# Seed data integrity
# ---------------------------------------------------------------------------

def test_every_mapped_permission_code_exists():
    declared = {p["permission_code"] for p in PERMISSIONS}
    mapped = {code for codes in ROLE_PERMISSIONS.values() for code in codes}
    assert mapped <= declared, f"unknown permission codes: {sorted(mapped - declared)}"


def test_seed_rbac_is_idempotent(session):
    seed_rbac(session)
    session.commit()
    seed_rbac(session)
    session.commit()

    assert session.query(Role).count() == 3
    assert session.query(Permission).count() == len(PERMISSIONS)
    assert session.query(RolePermission).count() == sum(
        len(codes) for codes in ROLE_PERMISSIONS.values()
    )


# ---------------------------------------------------------------------------
# Account creation
# ---------------------------------------------------------------------------

def test_creates_admin_on_empty_database(session):
    result = bootstrap_admin(
        session, phone=ADMIN_PHONE, password=ADMIN_PASSWORD, email="admin@school.com"
    )
    session.commit()

    assert result["action"] == "created"
    assert result["role"] == "Admin"

    user = session.query(User).filter(User.phone == ADMIN_PHONE).one()
    assert user.status == "ACTIVE"
    assert user.full_name == "System Administrator"
    assert user.email == "admin@school.com"
    assert verify_password(ADMIN_PASSWORD, user.password_hash)

    admin_role = session.query(Role).filter(Role.name == "Admin").one()
    assert user.role_id == admin_role.role_id


def test_creates_the_rbac_rows_the_account_needs(session):
    """A production DB built from migrations only has tables, no roles/permissions."""
    bootstrap_admin(session, phone=ADMIN_PHONE, password=ADMIN_PASSWORD)
    session.commit()

    # Without these the admin would log in with zero effective permissions.
    assert session.query(Role).count() == 3
    assert session.query(Permission).count() == len(PERMISSIONS)
    assert session.query(RolePermission).count() == sum(
        len(codes) for codes in ROLE_PERMISSIONS.values()
    )


def test_email_is_optional(session):
    result = bootstrap_admin(session, phone=ADMIN_PHONE, password=ADMIN_PASSWORD)
    session.commit()

    user = session.query(User).filter(User.phone == ADMIN_PHONE).one()
    assert user.email is None
    assert result["action"] == "created"


def test_second_run_is_a_noop(session):
    bootstrap_admin(session, phone=ADMIN_PHONE, password=ADMIN_PASSWORD)
    session.commit()
    first_hash = session.query(User).filter(User.phone == ADMIN_PHONE).one().password_hash

    result = bootstrap_admin(session, phone=ADMIN_PHONE, password="Other@12345")
    session.commit()

    assert result["action"] == "unchanged"
    user = session.query(User).filter(User.phone == ADMIN_PHONE).one()
    assert user.password_hash == first_hash
    assert verify_password(ADMIN_PASSWORD, user.password_hash)
    assert session.query(User).count() == 1


# ---------------------------------------------------------------------------
# Password handling
# ---------------------------------------------------------------------------

def test_reset_password_flag_rewrites_the_hash(session):
    bootstrap_admin(session, phone=ADMIN_PHONE, password=ADMIN_PASSWORD)
    session.commit()

    result = bootstrap_admin(
        session, phone=ADMIN_PHONE, password="Recovered@123", reset_password=True
    )
    session.commit()

    assert result["action"] == "updated"
    assert "password" in result["changes"]
    user = session.query(User).filter(User.phone == ADMIN_PHONE).one()
    assert verify_password("Recovered@123", user.password_hash)
    assert not verify_password(ADMIN_PASSWORD, user.password_hash)


def test_blank_fields_are_filled_but_edits_are_preserved(session):
    bootstrap_admin(session, phone=ADMIN_PHONE, password=ADMIN_PASSWORD)
    session.commit()

    user = session.query(User).filter(User.phone == ADMIN_PHONE).one()
    user.full_name = "Renamed In UI"
    session.commit()

    result = bootstrap_admin(
        session,
        phone=ADMIN_PHONE,
        password=ADMIN_PASSWORD,
        email="ops@school.com",
        full_name="System Administrator",
    )
    session.commit()

    assert "email" in result["changes"]
    assert "full_name" not in result["changes"]
    user = session.query(User).filter(User.phone == ADMIN_PHONE).one()
    assert user.email == "ops@school.com"
    assert user.full_name == "Renamed In UI"


@pytest.mark.parametrize(
    "password",
    [
        "short",                 # too short
        "",                      # empty
        "<doi-mat-khau-manh-it-nhat-8-ky-tu>",  # copied straight from .env.prod.example
        "changeme-please-123",   # generic placeholder
    ],
)
def test_rejects_unsafe_passwords(session, password):
    with pytest.raises(AdminBootstrapError):
        bootstrap_admin(session, phone=ADMIN_PHONE, password=password)
    assert session.query(User).count() == 0


def test_rejects_empty_phone(session):
    with pytest.raises(AdminBootstrapError):
        bootstrap_admin(session, phone="   ", password=ADMIN_PASSWORD)


# ---------------------------------------------------------------------------
# Role safety
# ---------------------------------------------------------------------------

def test_refuses_to_promote_an_existing_non_admin(session):
    seed_rbac(session)
    teacher_role = session.query(Role).filter(Role.name == "Teacher").one()
    session.add(
        User(
            user_id=uuid.uuid4(),
            phone=ADMIN_PHONE,
            email=None,
            password_hash=get_password_hash("Teacher@1234"),
            full_name="Sample Teacher",
            role_id=teacher_role.role_id,
            status="ACTIVE",
        )
    )
    session.commit()

    with pytest.raises(AdminBootstrapError, match="non-Admin"):
        bootstrap_admin(session, phone=ADMIN_PHONE, password=ADMIN_PASSWORD)

    user = session.query(User).filter(User.phone == ADMIN_PHONE).one()
    assert user.role_id == teacher_role.role_id
    assert verify_password("Teacher@1234", user.password_hash)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def test_main_skips_when_env_is_unset(monkeypatch):
    monkeypatch.delenv("ADMIN_PHONE", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    assert main() == 0


def test_main_fails_when_only_one_env_is_set(monkeypatch):
    monkeypatch.setenv("ADMIN_PHONE", ADMIN_PHONE)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    assert main() == 1


@pytest.mark.parametrize(
    "phone,expected",
    [
        ("", ""),
        ("1234", "1***"),
        ("123456", "1****6"),
        ("0999000001", "099****001"),
    ],
)
def test_mask_phone(phone, expected):
    assert mask_phone(phone) == expected
