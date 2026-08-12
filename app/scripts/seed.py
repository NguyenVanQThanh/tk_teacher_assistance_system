# File Name: seed.py
# Description: Script to seed the initial database with roles, permissions, and role-permission mappings.
# Created At: 2026-07-17
# Created By: Tam Khang
# Updated At: 2026-07-31
# Updated By: Tam Khang

import os
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

from models.base import Base
from models.models import Role, Permission, RolePermission

# Load environment variables
load_dotenv()

# Read database configuration from the environment
DB_USERNAME = os.environ.get("DB_USERNAME")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME")

if not all([DB_USERNAME, DB_PASSWORD, DB_NAME]):
    raise ValueError("Missing database configuration in environment variables")

DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_data():
    session = SessionLocal()
    try:
        print("Initializing database seed data...")

        # 1. Seed Roles (Idempotent: check if they exist first, update if descriptions change)
        roles_to_seed = [
            {"name": "Admin", "description": "System Administrator"},
            {"name": "Teacher", "description": "Teacher"},
            {"name": "Student", "description": "Student"}
        ]

        roles_db = {}
        for role_data in roles_to_seed:
            role = session.query(Role).filter(Role.name == role_data["name"]).first()
            if not role:
                role = Role(name=role_data["name"], description=role_data["description"])
                session.add(role)
                session.flush()  # to populate role_id
                print(f"Created role: {role.name}")
            else:
                if role.description != role_data["description"]:
                    role.description = role_data["description"]
                    print(f"Updated description for role: {role.name}")
            roles_db[role_data["name"]] = role

        # 2. Seed Permissions (Idempotent: check if they exist first, update if name/description change)
        permissions_to_seed = [
            {"permission_code": "AUTH_ME_VIEW", "name": "View Personal Information", "description": "Allows users to view their own personal profile information"},
            {"permission_code": "AUTH_PASSWORD_CHANGE", "name": "Change Password", "description": "Allows users to change their own password"},
            {"permission_code": "AUTH_PERM_MANAGE", "name": "Manage System Permissions", "description": "Allows administrators to manage user roles and permissions"},
            {"permission_code": "ACAD_SUBJECT_MANAGE", "name": "Manage Subjects", "description": "Allows Admin to create, edit, and delete subjects"},
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

        perms_db = {}
        for perm_data in permissions_to_seed:
            perm = session.query(Permission).filter(Permission.permission_code == perm_data["permission_code"]).first()
            if not perm:
                perm = Permission(
                    permission_code=perm_data["permission_code"],
                    name=perm_data["name"],
                    description=perm_data["description"]
                )
                session.add(perm)
                session.flush()  # to populate permission_id
                print(f"Created permission: {perm.permission_code}")
            else:
                updated = False
                if perm.name != perm_data["name"]:
                    perm.name = perm_data["name"]
                    updated = True
                if perm.description != perm_data["description"]:
                    perm.description = perm_data["description"]
                    updated = True
                if updated:
                    print(f"Updated permission: {perm.permission_code}")
            perms_db[perm_data["permission_code"]] = perm

        session.commit()

        # 3. Seed RolePermission mapping (Idempotent: check if exists first)
        mappings = {
            "Admin": ["AUTH_ME_VIEW", "AUTH_PASSWORD_CHANGE", "AUTH_PERM_MANAGE", "ACAD_SUBJECT_MANAGE", "ACAD_SUBJECT_VIEW", "ACAD_CLASS_MANAGE", "ACAD_CLASS_VIEW", "ACAD_ENROLLMENT_MANAGE", "ACAD_ENROLLMENT_VIEW", "ACAD_TEACHER_ASSIGN_MANAGE", "ACAD_TEACHER_ASSIGN_VIEW", "EXE_EXERCISE_MANAGE", "EXE_EXERCISE_VIEW", "EXE_ASSIGNMENT_MANAGE", "EXE_ASSIGNMENT_VIEW", "EXE_ATTEMPT_VIEW", "EXE_QUESTION_IMPORT"],
            "Teacher": ["AUTH_ME_VIEW", "AUTH_PASSWORD_CHANGE", "EXE_EXERCISE_MANAGE", "EXE_EXERCISE_VIEW", "EXE_ASSIGNMENT_MANAGE", "EXE_ASSIGNMENT_VIEW", "EXE_ATTEMPT_VIEW", "EXE_QUESTION_IMPORT"],
            "Student": ["AUTH_ME_VIEW", "AUTH_PASSWORD_CHANGE", "EXE_ASSIGNMENT_VIEW", "EXE_ATTEMPT_SUBMIT", "EXE_ATTEMPT_VIEW"]
        }




        role_perm_count = 0
        for role_name, perm_codes in mappings.items():
            role = roles_db.get(role_name)
            if not role:
                continue
            for code in perm_codes:
                perm = perms_db.get(code)
                if not perm:
                    continue
                # Check if mapping already exists
                exists = session.query(RolePermission).filter(
                    RolePermission.role_id == role.role_id,
                    RolePermission.permission_id == perm.permission_id
                ).first()
                if not exists:
                    role_perm = RolePermission(role_id=role.role_id, permission_id=perm.permission_id)
                    session.add(role_perm)
                    role_perm_count += 1

        if role_perm_count > 0:
            session.commit()
            print(f"Successfully mapped {role_perm_count} role-permission relationships!")
        else:
            print("All role-permission relationships are already mapped.")

        print("Database seed process completed successfully!")

    except Exception as e:
        session.rollback()
        print(f"An error occurred while seeding data: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_data()
