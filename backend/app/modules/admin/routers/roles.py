# File Name: roles.py
# Description: Admin RBAC role and permission matrix management API endpoints.
# Created At: 2026-11-14
# Created By: Tam Khang
# Updated At: 2026-11-14
# Updated By: Tam Khang

import csv
import io
import json
import logging
import uuid
from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.admin.routers.users import require_admin_privilege
from app.modules.admin.state_store import get_latest_state, upsert_state
from app.modules.auth.services.permission_service import PermissionService
from models.models import Permission, Role, RolePermission, User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin/roles",
    tags=["admin-roles"],
    dependencies=[Depends(require_admin_privilege)],
)

UI_PERMISSION_DEFS: List[Dict[str, str]] = [
    {
        "code": "view_schedule",
        "name": "View Schedules & Teaching Plans",
        "module": "academic",
        "description": "Access timetable, teaching schedules, and class rosters.",
    },
    {
        "code": "create_class",
        "name": "Create & Edit Classes",
        "module": "academic",
        "description": "Create new classes and update class information.",
    },
    {
        "code": "assign_teaching",
        "name": "Assign Subject Teachers",
        "module": "academic",
        "description": "Assign homeroom and subject teachers to classes.",
    },
    {
        "code": "ai_exercise",
        "name": "Generate AI Exercises",
        "module": "exercises",
        "description": "Use AI assistants to generate practice exercises and quizzes.",
    },
    {
        "code": "auto_grade",
        "name": "Run AI Auto-Grading",
        "module": "exercises",
        "description": "Run automated grading workflows on student submissions.",
    },
    {
        "code": "publish_exam",
        "name": "Publish Assignments & Exams",
        "module": "exercises",
        "description": "Publish assignments and exams to student cohorts.",
    },
    {
        "code": "edit_score_closed",
        "name": "Edit Scores After Term Lock",
        "module": "exercises",
        "description": "Override or adjust finalized grades after grading deadlines.",
    },
    {
        "code": "view_students",
        "name": "View Student Profiles & Rosters",
        "module": "students",
        "description": "Inspect student records and enrollment details.",
    },
    {
        "code": "edit_transcript",
        "name": "Edit Official Academic Transcripts",
        "module": "students",
        "description": "Update official academic performance transcripts.",
    },
]

UI_PERMISSION_CODES = [item["code"] for item in UI_PERMISSION_DEFS]

BUILTIN_ROLES: List[Dict[str, Any]] = [
    {
        "code": "admin",
        "aliases": ["admin"],
        "db_name": "Admin",
        "display_name": "Administrator (Admin)",
        "description": "Full system access across configuration, security, and academic administration.",
        "default_perms": {k: True for k in UI_PERMISSION_CODES},
    },
    {
        "code": "head_teacher",
        "aliases": ["head_teacher"],
        "db_name": "head_teacher",
        "display_name": "Head Teacher",
        "description": "Department head and homeroom oversight, class assignments, and grading controls.",
        "default_perms": {
            "view_schedule": True,
            "create_class": True,
            "assign_teaching": True,
            "ai_exercise": True,
            "auto_grade": True,
            "publish_exam": True,
            "edit_score_closed": False,
            "view_students": True,
            "edit_transcript": True,
        },
    },
    {
        "code": "subject_teacher",
        "aliases": ["subject_teacher", "teacher"],
        "db_name": "Teacher",
        "display_name": "Subject Teacher",
        "description": "Create exercises, manage assigned classes, and grade student submissions.",
        "default_perms": {
            "view_schedule": True,
            "create_class": False,
            "assign_teaching": False,
            "ai_exercise": True,
            "auto_grade": True,
            "publish_exam": True,
            "edit_score_closed": False,
            "view_students": True,
            "edit_transcript": False,
        },
    },
    {
        "code": "academic_staff",
        "aliases": ["academic_staff"],
        "db_name": "academic_staff",
        "display_name": "Academic Staff",
        "description": "Manage timetables, class rosters, and official academic transcripts.",
        "default_perms": {
            "view_schedule": True,
            "create_class": True,
            "assign_teaching": True,
            "ai_exercise": False,
            "auto_grade": False,
            "publish_exam": False,
            "edit_score_closed": False,
            "view_students": True,
            "edit_transcript": True,
        },
    },
    {
        "code": "student_parent",
        "aliases": ["student_parent", "student"],
        "db_name": "Student",
        "display_name": "Student / Parent",
        "description": "View class schedules, submit assignments, and track learning progress.",
        "default_perms": {
            "view_schedule": True,
            **{k: False for k in UI_PERMISSION_CODES if k != "view_schedule"},
        },
    },
]

_DB_NAME_TO_BUILTIN = {item["db_name"].lower(): item for item in BUILTIN_ROLES}
_CODE_TO_BUILTIN = {
    alias.lower(): item for item in BUILTIN_ROLES for alias in item["aliases"]
}


def _ensure_seeded(db: Session) -> Dict[str, Permission]:
    """
    Idempotently seed default roles, UI matrix permission definitions, and initial defaults.
    """
    created_any_role_perm = False

    # 1. Seed built-in Role rows without altering existing Admin/Teacher/Student names
    role_by_db_lower: Dict[str, Role] = {
        r.name.lower(): r for r in db.query(Role).all()
    }
    for spec in BUILTIN_ROLES:
        db_lower = spec["db_name"].lower()
        if db_lower not in role_by_db_lower:
            new_role = Role(
                role_id=uuid.uuid4(),
                name=spec["db_name"],
                description=spec["description"],
            )
            db.add(new_role)
            db.flush()
            role_by_db_lower[db_lower] = new_role

    # 2. Seed UI matrix Permission rows
    perm_map: Dict[str, Permission] = {
        p.permission_code: p
        for p in db.query(Permission)
        .filter(Permission.permission_code.in_(UI_PERMISSION_CODES))
        .all()
    }
    for p_def in UI_PERMISSION_DEFS:
        if p_def["code"] not in perm_map:
            perm = Permission(
                permission_id=uuid.uuid4(),
                permission_code=p_def["code"],
                name=p_def["name"],
                description=p_def["description"],
                module="admin_ui_matrix",
                http_method="UI",
                url_pattern="/api/v1/admin/roles",
            )
            db.add(perm)
            db.flush()
            perm_map[p_def["code"]] = perm

    db.commit()

    # 3. Seed default RolePermission toggles only once
    seed_flag = get_latest_state(db, "__UI_ROLES_SEEDED__")
    if not seed_flag:
        for spec in BUILTIN_ROLES:
            role_obj = role_by_db_lower[spec["db_name"].lower()]
            existing_perm_ids = {
                rp.permission_id
                for rp in db.query(RolePermission)
                .filter(RolePermission.role_id == role_obj.role_id)
                .all()
            }
            for perm_code, enabled in spec["default_perms"].items():
                if enabled:
                    perm_obj = perm_map[perm_code]
                    if perm_obj.permission_id not in existing_perm_ids:
                        db.add(
                            RolePermission(
                                role_id=role_obj.role_id,
                                permission_id=perm_obj.permission_id,
                            )
                        )
                        created_any_role_perm = True
        db.commit()
        upsert_state(db, "__UI_ROLES_SEEDED__", {"seeded": True}, actor_name="System")
        if created_any_role_perm:
            PermissionService.invalidate_role_cache()

    return perm_map


def _resolve_role(db: Session, role_code: str) -> Role:
    """
    Resolve a UI role code, alias, DB role name, or UUID to a Role ORM record.
    """
    key = role_code.strip().lower()
    builtin = _CODE_TO_BUILTIN.get(key)
    if builtin:
        role = db.query(Role).filter(func.lower(Role.name) == builtin["db_name"].lower()).first()
        if role:
            return role

    role = db.query(Role).filter(func.lower(Role.name) == key).first()
    if role:
        return role

    try:
        uid = UUID(role_code)
        role = db.query(Role).filter(Role.role_id == uid).first()
        if role:
            return role
    except ValueError:
        pass

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "ERR-ADMIN-ROLE_NOT_FOUND", "message": f"Role '{role_code}' not found."},
    )


def _canonical_role_code(role: Role) -> str:
    spec = _DB_NAME_TO_BUILTIN.get(role.name.lower())
    return spec["code"] if spec else role.name


def _role_display_meta(db: Session, role: Role, member_count: int) -> Dict[str, Any]:
    spec = _DB_NAME_TO_BUILTIN.get(role.name.lower())
    code = spec["code"] if spec else role.name
    meta = None if spec else get_latest_state(db, f"__ROLE_META__:{role.role_id}")
    display_name = spec["display_name"] if spec else (meta.get("display_name") if meta else role.name)
    description = role.description or (spec["description"] if spec else "")
    return {
        "id": code,
        "code": code,
        "role_id": str(role.role_id),
        "name": display_name,
        "db_name": role.name,
        "description": description,
        "memberCount": member_count,
        "isSystem": bool(spec),
    }


def _get_role_member_users(db: Session, role: Role) -> list:
    """Return non-deleted users whose role_id is this role (the only users the role permissions apply to)."""
    return (
        db.query(User)
        .filter(
            User.role_id == role.role_id,
            func.upper(User.status) != "DELETED",
        )
        .order_by(User.full_name.asc())
        .all()
    )

def _build_roles_and_matrix(db: Session) -> Dict[str, Any]:
    perm_map = _ensure_seeded(db)
    perm_id_to_code = {p.permission_id: code for code, p in perm_map.items()}

    roles = db.query(Role).order_by(Role.created_at.asc()).all()
    builtin_order = {spec["db_name"].lower(): idx for idx, spec in enumerate(BUILTIN_ROLES)}
    roles.sort(key=lambda r: (builtin_order.get(r.name.lower(), 100), r.name.lower()))

    # Count non-deleted users per role
    count_rows = (
        db.query(User.role_id, func.count(User.user_id))
        .filter(func.upper(User.status) != "DELETED")
        .group_by(User.role_id)
        .all()
    )
    counts_map = {rid: int(cnt) for rid, cnt in count_rows}
    for r in roles:
        if (r.name or "").strip().lower() == "head_teacher":
            counts_map[r.role_id] = len(_get_role_member_users(db, r))

    # Load all RolePermission mappings for UI permissions
    rp_rows = (
        db.query(RolePermission)
        .filter(RolePermission.permission_id.in_(list(perm_id_to_code.keys())))
        .all()
    )
    role_enabled_codes: Dict[UUID, set] = {}
    for rp in rp_rows:
        code = perm_id_to_code.get(rp.permission_id)
        if code:
            role_enabled_codes.setdefault(rp.role_id, set()).add(code)

    roles_out: List[Dict[str, Any]] = []
    matrix: Dict[str, Dict[str, bool]] = {}
    for role in roles:
        meta = _role_display_meta(db, role, counts_map.get(role.role_id, 0))
        roles_out.append(meta)
        enabled = role_enabled_codes.get(role.role_id, set())
        matrix[meta["code"]] = {code: (code in enabled) for code in UI_PERMISSION_CODES}

    return {
        "roles": roles_out,
        "permissions_matrix": matrix,
        "permission_definitions": UI_PERMISSION_DEFS,
    }


@router.get("")
def list_roles_and_matrix(db: Session = Depends(get_db)):
    """
    List all roles with active member counts and the full UI permissions matrix.
    """
    return _build_roles_and_matrix(db)


@router.get("/export")
def export_roles_matrix(
    format: str = Query("csv", description="Export format: csv or json"),
    db: Session = Depends(get_db),
):
    """
    Export the RBAC roles and permission matrix as a downloadable CSV or JSON stream.
    """
    data = _build_roles_and_matrix(db)
    fmt = format.strip().lower()

    if fmt == "json":
        raw_json = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        return StreamingResponse(
            io.BytesIO(raw_json),
            media_type="application/json; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="roles_permissions_export.json"'},
        )

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Role Code", "Role Name", "Description", "Member Count", *UI_PERMISSION_CODES])
    for r in data["roles"]:
        perms = data["permissions_matrix"].get(r["code"], {})
        writer.writerow([
            r["code"],
            r["name"],
            r["description"],
            r["memberCount"],
            *[str(bool(perms.get(k, False))).lower() for k in UI_PERMISSION_CODES],
        ])

    csv_bytes = b"\xef\xbb\xbf" + buf.getvalue().encode("utf-8")
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="roles_permissions_export.csv"'},
    )


@router.get("/{role_code}/members")
def list_role_members(
    role_code: str,
    db: Session = Depends(get_db),
):
    """
    List active non-deleted users assigned to the specified role.
    """
    _ensure_seeded(db)
    role = _resolve_role(db, role_code)
    canonical = _canonical_role_code(role)

    users = _get_role_member_users(db, role)

    return {
        "items": [
            {
                "user_id": str(u.user_id),
                "full_name": u.full_name,
                "email": u.email,
                "phone": u.phone,
                "status": u.status,
                "role_id": str(role.role_id),
                "role_code": canonical,
                "role_name": role.name,
            }
            for u in users
        ]
    }
