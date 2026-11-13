# File Name: rbac_seed.py
# Description: Single source of truth for RBAC seed data (roles, permissions, role-permission
#              mappings) plus an idempotent seeder shared by seed.py and bootstrap_admin.py.
# Created At: 2026-11-14
# Created By: AI Agent
# Updated At: 2026-11-14
# Updated By: AI Agent

"""RBAC seed data + idempotent seeder.

Alembic only creates tables; it never inserts roles or permissions. Development
environments ran `app/scripts/seed.py` by hand, but a production database built
purely from migrations starts with an empty `roles` table — and `users.role_id`
is NOT NULL, so no account can exist at all.

Keeping the data here (instead of inside seed.py) lets both entry points use the
same list:
  * seed.py            — CLI for dev, seeds RBAC and nothing else
  * bootstrap_admin.py — runs from the container entrypoint in production
"""

from __future__ import annotations

from typing import Dict, List

from sqlalchemy.orm import Session

from models.models import Permission, Role, RolePermission

# Roles created on every environment. Order is irrelevant; lookups are by name.
ROLES: List[Dict[str, str]] = [
    {"name": "Admin", "description": "System Administrator"},
    {"name": "Teacher", "description": "Teacher"},
    {"name": "Student", "description": "Student"},
]

PERMISSIONS: List[Dict[str, str]] = [
    {"permission_code": "AUTH_ME_VIEW", "name": "View Personal Information", "description": "Allows users to view their own personal profile information"},
    {"permission_code": "AUTH_PASSWORD_CHANGE", "name": "Change Password", "description": "Allows users to change their own password"},
    {"permission_code": "AUTH_PERM_MANAGE", "name": "Manage System Permissions", "description": "Allows administrators to manage user roles and permissions"},
    {"permission_code": "ACAD_SUBJECT_MANAGE", "name": "Manage Subjects", "description": "Allows Admin to create, edit, and delete subjects"},
    {"permission_code": "ACAD_SUBJECT_HEAD_ASSIGN", "name": "Assign Subject Head", "description": "Allows Admin to assign the head of a subject department"},
    {"permission_code": "ACAD_SUBJECT_VIEW", "name": "View Subjects", "description": "Allows viewing subject list and details"},
    {"permission_code": "ACAD_CLASS_MANAGE", "name": "Manage Classes", "description": "Allows Admin to create, edit, and delete classes"},
    {"permission_code": "ACAD_CLASS_VIEW", "name": "View Classes", "description": "Allows viewing class list and details"},
    {"permission_code": "ACAD_ENROLLMENT_MANAGE", "name": "Manage Student Enrollments", "description": "Allows Admin to enroll and unenroll students in classes"},
    {"permission_code": "ACAD_ENROLLMENT_VIEW", "name": "View Student Enrollments", "description": "Allows viewing list of enrolled students in a class"},
    {"permission_code": "ACAD_TEACHER_ASSIGN_MANAGE", "name": "Manage Teacher Assignments", "description": "Allows Admin to assign and unassign subject teachers"},
    {"permission_code": "ACAD_TEACHER_ASSIGN_VIEW", "name": "View Teacher Assignments", "description": "Allows viewing list of teacher assignments by class"},
    {"permission_code": "EXE_EXERCISE_MANAGE", "name": "Manage Exercise Bank", "description": "Allows creating, editing, soft deleting, and restoring exercises and questions"},
    {"permission_code": "EXE_EXERCISE_VIEW", "name": "View Exercise Bank", "description": "Allows viewing list and details of exercises"},
    {"permission_code": "EXE_ASSIGNMENT_MANAGE", "name": "Manage Class Assignments", "description": "Allows assigning exercises, cancelling assignments (soft delete), and restoring"},
    {"permission_code": "EXE_ASSIGNMENT_VIEW", "name": "View Assigned Exercises", "description": "Allows viewing list of assigned exercises by class"},
    {"permission_code": "EXE_ATTEMPT_SUBMIT", "name": "Start and Submit Exercise Attempts", "description": "Allows students to start attempts and submit answers for evaluation"},
    {"permission_code": "EXE_ATTEMPT_VIEW", "name": "View Exercise Attempt Results", "description": "Allows viewing detailed results of exercise attempts"},
    {"permission_code": "EXE_QUESTION_IMPORT", "name": "Bulk Question Import", "description": "Allows teachers and admins to bulk import questions from docx/pdf files"},
]

# role name -> permission codes granted to that role.
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "Admin": [
        "AUTH_ME_VIEW", "AUTH_PASSWORD_CHANGE", "AUTH_PERM_MANAGE",
        "ACAD_SUBJECT_MANAGE", "ACAD_SUBJECT_VIEW", "ACAD_SUBJECT_HEAD_ASSIGN",
        "ACAD_CLASS_MANAGE", "ACAD_CLASS_VIEW",
        "ACAD_ENROLLMENT_MANAGE", "ACAD_ENROLLMENT_VIEW",
        "ACAD_TEACHER_ASSIGN_MANAGE", "ACAD_TEACHER_ASSIGN_VIEW",
        "EXE_EXERCISE_MANAGE", "EXE_EXERCISE_VIEW",
        "EXE_ASSIGNMENT_MANAGE", "EXE_ASSIGNMENT_VIEW",
        "EXE_ATTEMPT_VIEW", "EXE_QUESTION_IMPORT",
    ],
    "Teacher": [
        "AUTH_ME_VIEW", "AUTH_PASSWORD_CHANGE",
        "ACAD_CLASS_VIEW", "ACAD_SUBJECT_VIEW",
        "ACAD_ENROLLMENT_VIEW", "ACAD_TEACHER_ASSIGN_VIEW",
        "EXE_EXERCISE_MANAGE", "EXE_EXERCISE_VIEW",
        "EXE_ASSIGNMENT_MANAGE", "EXE_ASSIGNMENT_VIEW",
        "EXE_ATTEMPT_VIEW", "EXE_QUESTION_IMPORT",
    ],
    "Student": [
        "AUTH_ME_VIEW", "AUTH_PASSWORD_CHANGE",
        "ACAD_CLASS_VIEW", "ACAD_SUBJECT_VIEW", "ACAD_ENROLLMENT_VIEW",
        "EXE_EXERCISE_VIEW", "EXE_ASSIGNMENT_VIEW", "EXE_ATTEMPT_SUBMIT", "EXE_ATTEMPT_VIEW",
    ],
}


def seed_rbac(session: Session) -> Dict[str, Role]:
    """Insert missing roles/permissions and role-permission mappings.

    Idempotent: existing rows are reused, and permission name/description drift
    (e.g. text edited in this file) is reconciled. Nothing is deleted, so custom
    grants added by an administrator survive a redeploy.

    The caller owns the transaction — this function only flushes, never commits.

    Returns:
        Mapping of role name -> Role instance, for the roles that now exist.
    """
    roles_db: Dict[str, Role] = {}

    for role_data in ROLES:
        role = session.query(Role).filter(Role.name == role_data["name"]).first()
        if not role:
            role = Role(name=role_data["name"], description=role_data["description"])
            session.add(role)
            session.flush()  # populate role_id for the FK mapping below
            print(f"rbac: created role {role.name}")
        elif role.description != role_data["description"]:
            role.description = role_data["description"]
            print(f"rbac: updated description for role {role.name}")
        roles_db[role_data["name"]] = role

    perms_db: Dict[str, Permission] = {}
    for perm_data in PERMISSIONS:
        perm = (
            session.query(Permission)
            .filter(Permission.permission_code == perm_data["permission_code"])
            .first()
        )
        if not perm:
            perm = Permission(
                permission_code=perm_data["permission_code"],
                name=perm_data["name"],
                description=perm_data["description"],
            )
            session.add(perm)
            session.flush()
            print(f"rbac: created permission {perm.permission_code}")
        else:
            changed = False
            if perm.name != perm_data["name"]:
                perm.name = perm_data["name"]
                changed = True
            if perm.description != perm_data["description"]:
                perm.description = perm_data["description"]
                changed = True
            if changed:
                print(f"rbac: updated permission {perm.permission_code}")
        perms_db[perm_data["permission_code"]] = perm

    session.flush()

    mapped = 0
    for role_name, perm_codes in ROLE_PERMISSIONS.items():
        role = roles_db.get(role_name)
        if not role:
            continue
        for code in perm_codes:
            perm = perms_db.get(code)
            if not perm:
                continue
            exists = (
                session.query(RolePermission)
                .filter(
                    RolePermission.role_id == role.role_id,
                    RolePermission.permission_id == perm.permission_id,
                )
                .first()
            )
            if not exists:
                session.add(
                    RolePermission(role_id=role.role_id, permission_id=perm.permission_id)
                )
                mapped += 1

    if mapped:
        session.flush()
        print(f"rbac: mapped {mapped} role-permission relationships")

    return roles_db
