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
import re
import uuid
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.admin.routers.users import require_admin_privilege
from app.modules.admin.state_store import get_latest_state, record_audit_event, upsert_state
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.services.permission_service import PermissionService
from models.models import Permission, Role, RolePermission, Subject, User

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


class RoleCreateRequest(BaseModel):
    """Schema for creating a custom RBAC role."""

    name: str = Field(..., min_length=1, max_length=100)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    template_role_code: Optional[str] = None
    cloneFrom: Optional[str] = None


class RolePermissionsUpdateRequest(BaseModel):
    """Schema for updating the permission matrix for a role."""

    permissions: Dict[str, bool]


class RoleMemberAssignRequest(BaseModel):
    """Schema for assigning an existing user to a role."""

    user_id: UUID


def _slugify_role_code(raw: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", raw.strip().lower()).strip("_")
    return slug[:50]


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
    """
    Return deduplicated non-deleted users belonging to a role.
    For head_teacher, unions explicit User.role_id members with active
    teachers assigned as Subject.head_teacher_id on active subjects.
    """
    direct_users = (
        db.query(User)
        .filter(
            User.role_id == role.role_id,
            func.upper(User.status) != "DELETED",
        )
        .order_by(User.full_name.asc())
        .all()
    )
    if (role.name or "").strip().lower() != "head_teacher":
        return direct_users

    subject_heads = (
        db.query(User)
        .join(Subject, Subject.head_teacher_id == User.user_id)
        .filter(
            func.upper(Subject.status) != "DELETED",
            Subject.head_teacher_id.isnot(None),
            func.upper(User.status) != "DELETED",
        )
        .all()
    )
    by_id = {u.user_id: u for u in direct_users}
    for teacher in subject_heads:
        by_id.setdefault(teacher.user_id, teacher)

    return sorted(by_id.values(), key=lambda u: (u.full_name or "").lower())


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


@router.post("", status_code=status.HTTP_201_CREATED)
def create_role(
    payload: RoleCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new role in DB, optionally cloning permissions from an existing template role.
    """
    _ensure_seeded(db)

    raw_code = (payload.code or _slugify_role_code(payload.name)).strip().lower()
    if not raw_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ERR-ADMIN-INVALID_ROLE_CODE", "message": "Role code cannot be empty."},
        )

    # Reject duplicates across DB role names and built-in aliases
    existing_alias = _CODE_TO_BUILTIN.get(raw_code)
    existing_db = db.query(Role).filter(func.lower(Role.name) == raw_code).first()
    if existing_alias or existing_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "ERR-ADMIN-ROLE_EXISTS", "message": f"Role '{raw_code}' already exists."},
        )

    template_code = payload.template_role_code or payload.cloneFrom
    source_role = _resolve_role(db, template_code) if template_code else None

    new_role = Role(
        role_id=uuid.uuid4(),
        name=raw_code,
        description=(payload.description or payload.name).strip(),
    )
    db.add(new_role)
    db.flush()

    if source_role:
        source_rps = (
            db.query(RolePermission)
            .filter(RolePermission.role_id == source_role.role_id)
            .all()
        )
        for rp in source_rps:
            db.add(
                RolePermission(
                    role_id=new_role.role_id,
                    permission_id=rp.permission_id,
                )
            )

    db.commit()
    db.refresh(new_role)
    upsert_state(
        db,
        f"__ROLE_META__:{new_role.role_id}",
        {"display_name": payload.name.strip()},
        actor_name=current_user.full_name,
    )
    PermissionService.invalidate_role_cache()

    record_audit_event(
        db=db,
        title="Created RBAC Role",
        description=f"Created role '{payload.name.strip()}' ({raw_code})"
        + (f" cloned from '{template_code}'." if template_code else "."),
        actor_name=current_user.full_name,
        severity="info",
    )

    state = _build_roles_and_matrix(db)
    role_dto = next(r for r in state["roles"] if r["code"] == raw_code)
    return {
        **role_dto,
        "role": role_dto,
        "permissions": state["permissions_matrix"].get(raw_code, {}),
    }


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


@router.put("/{role_code}/permissions")
def update_role_permissions(
    role_code: str,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update UI permissions in RolePermission for the specified role and invalidate RBAC cache.
    """
    perm_map = _ensure_seeded(db)
    role = _resolve_role(db, role_code)
    canonical = _canonical_role_code(role)

    # Self-lockout protection: the Admin permission matrix is read-only.
    if canonical == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ERR-ADMIN-ADMIN_PERMS_LOCKED", "message": "Admin role permissions cannot be modified."},
        )

    raw_perms = payload.get("permissions") if isinstance(payload.get("permissions"), dict) else payload
    if not isinstance(raw_perms, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ERR-ADMIN-INVALID_PERMISSIONS", "message": "Invalid permissions payload."},
        )

    ui_perm_ids = [perm_map[code].permission_id for code in UI_PERMISSION_CODES]
    existing_rps = (
        db.query(RolePermission)
        .filter(
            RolePermission.role_id == role.role_id,
            RolePermission.permission_id.in_(ui_perm_ids),
        )
        .all()
    )
    existing_perm_ids = {rp.permission_id for rp in existing_rps}

    to_add = []
    to_remove = []
    for code in UI_PERMISSION_CODES:
        if code not in raw_perms:
            continue
        pid = perm_map[code].permission_id
        desired = bool(raw_perms[code])
        if desired and pid not in existing_perm_ids:
            to_add.append(RolePermission(role_id=role.role_id, permission_id=pid))
        elif not desired and pid in existing_perm_ids:
            to_remove.append(pid)

    for rp in to_add:
        db.add(rp)

    if to_remove:
        db.query(RolePermission).filter(
            RolePermission.role_id == role.role_id,
            RolePermission.permission_id.in_(to_remove),
        ).delete(synchronize_session=False)

    db.commit()
    PermissionService.invalidate_role_cache(role.role_id)

    record_audit_event(
        db=db,
        title="Updated Role Permissions",
        description=f"Updated permission matrix for role '{canonical}'.",
        actor_name=current_user.full_name,
        severity="warning" if canonical == "admin" else "info",
    )

    state = _build_roles_and_matrix(db)
    return {
        "role_code": canonical,
        "permissions": state["permissions_matrix"].get(canonical, {}),
        "message": "Permissions updated successfully.",
    }


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


@router.post("/{role_code}/members")
def assign_user_to_role(
    role_code: str,
    payload: RoleMemberAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Assign a non-deleted user to the specified role and record an audit log entry.
    """
    _ensure_seeded(db)
    role = _resolve_role(db, role_code)
    canonical = _canonical_role_code(role)

    target_user = (
        db.query(User)
        .filter(
            User.user_id == payload.user_id,
            func.upper(User.status) != "DELETED",
        )
        .first()
    )
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ERR-ADMIN-USER_NOT_FOUND", "message": "User not found or deleted."},
        )

    # Policy: no new admins. Assigning the Admin role is forbidden.
    if canonical == "admin" and target_user.role_id != role.role_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ERR-ADMIN-ADMIN_ROLE_LOCKED", "message": "Admin accounts cannot be created or assigned."},
        )

    if target_user.user_id == current_user.user_id and target_user.role_id != role.role_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ERR-ADMIN-SELF_ROLE_CHANGE", "message": "You cannot change your own role."},
        )

    # Last-admin protection: never demote the only remaining active Admin.
    admin_role = db.query(Role).filter(func.lower(Role.name) == "admin").first()
    if (
        admin_role
        and target_user.role_id == admin_role.role_id
        and role.role_id != admin_role.role_id
    ):
        other_admins = (
            db.query(User)
            .filter(
                User.role_id == admin_role.role_id,
                User.user_id != target_user.user_id,
                func.upper(User.status) == "ACTIVE",
            )
            .count()
        )
        if other_admins == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "ERR-ADMIN-LAST_ADMIN", "message": "Cannot demote the last active Admin."},
            )

    target_user.role_id = role.role_id
    db.commit()
    db.refresh(target_user)

    record_audit_event(
        db=db,
        title="Assigned User to Role",
        description=f"Assigned user '{target_user.full_name}' to role '{canonical}'.",
        actor_name=current_user.full_name,
        severity="warning" if canonical == "admin" else "info",
    )

    return {
        "message": "User assigned to role successfully.",
        "user_id": str(target_user.user_id),
        "full_name": target_user.full_name,
        "role_code": canonical,
        "role_id": str(role.role_id),
    }
