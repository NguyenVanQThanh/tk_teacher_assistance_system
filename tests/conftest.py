# File Name: conftest.py
# Description: Testing configuration, database setup using SQLite in-memory, and fixtures.
# Created At: 2026-07-17
# Created By: Tam Khang
# Updated At: 2026-07-22
# Updated By: Tam Khang


import os
import uuid
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Mock environment variables before importing anything else
os.environ["SECRET_KEY"] = "test-secret-key-for-jwt-generation-and-validation-must-be-long"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "10"
os.environ["DB_USERNAME"] = "dummy"
os.environ["DB_PASSWORD"] = "dummy"
os.environ["DB_NAME"] = "dummy"

# Monkeypatch bcrypt.hashpw to avoid passlib bug check ValueError on Python 3.13 / bcrypt >= 4.0
import bcrypt
_original_hashpw = bcrypt.hashpw
def _patched_hashpw(password, salt):
    if isinstance(password, bytes) and len(password) > 72:
        password = password[:72]
    return _original_hashpw(password, salt)
bcrypt.hashpw = _patched_hashpw

from models.base import Base
from models.models import User, Role, Permission, RolePermission, UserPermission
from app.core.database import get_db
from app.core.security import get_password_hash
from app.modules.auth.services.permission_service import PermissionService
from app.main import app


# Create SQLite in-memory engine for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_db() -> Generator[None, None, None]:
    """
    Creates database schema and seeds initial roles, permissions, and users.
    """
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        # 1. Seed Roles
        admin_role = Role(role_id=uuid.uuid4(), name="Admin", description="System Administrator")
        teacher_role = Role(role_id=uuid.uuid4(), name="Teacher", description="Teacher")
        student_role = Role(role_id=uuid.uuid4(), name="Student", description="Student")
        
        db.add_all([admin_role, teacher_role, student_role])
        db.flush()

        # 2. Seed Permissions
        me_view_perm = Permission(
            permission_id=uuid.uuid4(),
            permission_code="AUTH_ME_VIEW",
            name="View personal info",
            description="Allows user to view their own profile"
        )
        pwd_change_perm = Permission(
            permission_id=uuid.uuid4(),
            permission_code="AUTH_PASSWORD_CHANGE",
            name="Change password",
            description="Allows user to change their password"
        )
        perm_manage_perm = Permission(
            permission_id=uuid.uuid4(),
            permission_code="AUTH_PERM_MANAGE",
            name="Manage system permissions",
            description="Allows admin to manage permissions"
        )
        acad_subject_manage_perm = Permission(
            permission_id=uuid.uuid4(),
            permission_code="ACAD_SUBJECT_MANAGE",
            name="Manage subjects",
            description="Allows admin to create, update, delete subjects"
        )
        acad_subject_view_perm = Permission(
            permission_id=uuid.uuid4(),
            permission_code="ACAD_SUBJECT_VIEW",
            name="View subjects",
            description="Allows viewing subjects"
        )
        acad_class_manage_perm = Permission(
            permission_id=uuid.uuid4(),
            permission_code="ACAD_CLASS_MANAGE",
            name="Manage classes",
            description="Allows admin to create, update, delete classes"
        )
        acad_class_view_perm = Permission(
            permission_id=uuid.uuid4(),
            permission_code="ACAD_CLASS_VIEW",
            name="View classes",
            description="Allows viewing classes"
        )
        acad_enrollment_manage_perm = Permission(
            permission_id=uuid.uuid4(),
            permission_code="ACAD_ENROLLMENT_MANAGE",
            name="Manage enrollments",
            description="Allows admin to enroll and unenroll students"
        )
        acad_enrollment_view_perm = Permission(
            permission_id=uuid.uuid4(),
            permission_code="ACAD_ENROLLMENT_VIEW",
            name="View enrollments",
            description="Allows viewing enrollments"
        )
        acad_teacher_assign_manage_perm = Permission(
            permission_id=uuid.uuid4(),
            permission_code="ACAD_TEACHER_ASSIGN_MANAGE",
            name="Manage teacher assignments",
            description="Allows admin to assign and unassign teachers"
        )
        acad_teacher_assign_view_perm = Permission(
            permission_id=uuid.uuid4(),
            permission_code="ACAD_TEACHER_ASSIGN_VIEW",
            name="View teacher assignments",
            description="Allows viewing teacher assignments"
        )
        exe_exercise_manage_perm = Permission(
            permission_id=uuid.uuid4(),
            permission_code="EXE_EXERCISE_MANAGE",
            name="Manage exercises",
            description="Allows creating and managing exercise bank"
        )
        exe_exercise_view_perm = Permission(
            permission_id=uuid.uuid4(),
            permission_code="EXE_EXERCISE_VIEW",
            name="View exercises",
            description="Allows viewing exercise bank"
        )
        exe_assignment_manage_perm = Permission(
            permission_id=uuid.uuid4(),
            permission_code="EXE_ASSIGNMENT_MANAGE",
            name="Manage class assignments",
            description="Allows creating, soft deleting, and restoring assignments"
        )
        exe_assignment_view_perm = Permission(
            permission_id=uuid.uuid4(),
            permission_code="EXE_ASSIGNMENT_VIEW",
            name="View class assignments",
            description="Allows viewing class assignments"
        )
        exe_attempt_submit_perm = Permission(
            permission_id=uuid.uuid4(),
            permission_code="EXE_ATTEMPT_SUBMIT",
            name="Start and submit attempts",
            description="Allows students to start and submit attempts"
        )
        exe_attempt_view_perm = Permission(
            permission_id=uuid.uuid4(),
            permission_code="EXE_ATTEMPT_VIEW",
            name="View attempt results",
            description="Allows viewing attempt results"
        )
        
        db.add_all([
            me_view_perm,
            pwd_change_perm,
            perm_manage_perm,
            acad_subject_manage_perm,
            acad_subject_view_perm,
            acad_class_manage_perm,
            acad_class_view_perm,
            acad_enrollment_manage_perm,
            acad_enrollment_view_perm,
            acad_teacher_assign_manage_perm,
            acad_teacher_assign_view_perm,
            exe_exercise_manage_perm,
            exe_exercise_view_perm,
            exe_assignment_manage_perm,
            exe_assignment_view_perm,
            exe_attempt_submit_perm,
            exe_attempt_view_perm
        ])
        db.flush()

        # 3. Seed RolePermission mappings
        # Admin gets all
        db.add_all([
            RolePermission(role_id=admin_role.role_id, permission_id=me_view_perm.permission_id),
            RolePermission(role_id=admin_role.role_id, permission_id=pwd_change_perm.permission_id),
            RolePermission(role_id=admin_role.role_id, permission_id=perm_manage_perm.permission_id),
            RolePermission(role_id=admin_role.role_id, permission_id=acad_subject_manage_perm.permission_id),
            RolePermission(role_id=admin_role.role_id, permission_id=acad_subject_view_perm.permission_id),
            RolePermission(role_id=admin_role.role_id, permission_id=acad_class_manage_perm.permission_id),
            RolePermission(role_id=admin_role.role_id, permission_id=acad_class_view_perm.permission_id),
            RolePermission(role_id=admin_role.role_id, permission_id=acad_enrollment_manage_perm.permission_id),
            RolePermission(role_id=admin_role.role_id, permission_id=acad_enrollment_view_perm.permission_id),
            RolePermission(role_id=admin_role.role_id, permission_id=acad_teacher_assign_manage_perm.permission_id),
            RolePermission(role_id=admin_role.role_id, permission_id=acad_teacher_assign_view_perm.permission_id),
            RolePermission(role_id=admin_role.role_id, permission_id=exe_exercise_manage_perm.permission_id),
            RolePermission(role_id=admin_role.role_id, permission_id=exe_exercise_view_perm.permission_id),
            RolePermission(role_id=admin_role.role_id, permission_id=exe_assignment_manage_perm.permission_id),
            RolePermission(role_id=admin_role.role_id, permission_id=exe_assignment_view_perm.permission_id),
            RolePermission(role_id=admin_role.role_id, permission_id=exe_attempt_view_perm.permission_id),
        ])
        # Teacher & Student get view & change password
        db.add_all([
            RolePermission(role_id=teacher_role.role_id, permission_id=me_view_perm.permission_id),
            RolePermission(role_id=teacher_role.role_id, permission_id=pwd_change_perm.permission_id),
            RolePermission(role_id=teacher_role.role_id, permission_id=exe_exercise_manage_perm.permission_id),
            RolePermission(role_id=teacher_role.role_id, permission_id=exe_exercise_view_perm.permission_id),
            RolePermission(role_id=teacher_role.role_id, permission_id=exe_assignment_manage_perm.permission_id),
            RolePermission(role_id=teacher_role.role_id, permission_id=exe_assignment_view_perm.permission_id),
            RolePermission(role_id=teacher_role.role_id, permission_id=exe_attempt_view_perm.permission_id),
            RolePermission(role_id=student_role.role_id, permission_id=me_view_perm.permission_id),
            RolePermission(role_id=student_role.role_id, permission_id=pwd_change_perm.permission_id),
            RolePermission(role_id=student_role.role_id, permission_id=exe_assignment_view_perm.permission_id),
            RolePermission(role_id=student_role.role_id, permission_id=exe_attempt_submit_perm.permission_id),
            RolePermission(role_id=student_role.role_id, permission_id=exe_attempt_view_perm.permission_id),
        ])


        
        # 4. Seed Users
        hashed_password = get_password_hash("password123")
        
        # Standard Active Admin
        admin_user = User(
            user_id=uuid.uuid4(),
            phone="0987654321",
            email="admin@test.com",
            password_hash=hashed_password,
            full_name="Admin User",
            role_id=admin_role.role_id,
            status="Active"
        )
        
        # Blocked Admin
        blocked_user = User(
            user_id=uuid.uuid4(),
            phone="0987654322",
            email="blocked@test.com",
            password_hash=hashed_password,
            full_name="Blocked User",
            role_id=admin_role.role_id,
            status="Blocked"
        )
        
        # Inactive Admin
        inactive_user = User(
            user_id=uuid.uuid4(),
            phone="0987654323",
            email="inactive@test.com",
            password_hash=hashed_password,
            full_name="Inactive User",
            role_id=admin_role.role_id,
            status="Inactive"
        )

        # Standard Active Teacher
        teacher_user = User(
            user_id=uuid.uuid4(),
            phone="0912345678",
            email="teacher@test.com",
            password_hash=hashed_password,
            full_name="Teacher User",
            role_id=teacher_role.role_id,
            status="Active"
        )

        # Standard Active Student
        student_user = User(
            user_id=uuid.uuid4(),
            phone="0934567890",
            email="student@test.com",
            password_hash=hashed_password,
            full_name="Student User",
            role_id=student_role.role_id,
            status="Active"
        )

        # Student User to test override ALLOW (will start with Student role but we override allowance for AUTH_PERM_MANAGE)
        student_allow_user = User(
            user_id=uuid.uuid4(),
            phone="0934567891",
            email="student_allow@test.com",
            password_hash=hashed_password,
            full_name="Student Allow Override User",
            role_id=student_role.role_id,
            status="Active"
        )

        # Student User to test override DENY (has Student role but we deny AUTH_ME_VIEW)
        student_deny_user = User(
            user_id=uuid.uuid4(),
            phone="0934567892",
            email="student_deny@test.com",
            password_hash=hashed_password,
            full_name="Student Deny Override User",
            role_id=student_role.role_id,
            status="Active"
        )

        db.add_all([
            admin_user, blocked_user, inactive_user, 
            teacher_user, student_user, student_allow_user, student_deny_user
        ])
        db.flush()

        # 5. Seed UserPermission overrides
        db.add_all([
            UserPermission(user_id=student_allow_user.user_id, permission_id=perm_manage_perm.permission_id, effect="allow"),
            UserPermission(user_id=student_deny_user.user_id, permission_id=me_view_perm.permission_id, effect="deny")
        ])

        db.commit()
        PermissionService.invalidate_role_cache()
    except Exception as e:

        db.rollback()
        raise e
    finally:
        db.close()

    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """
    Provides a transactional database session for each test, rolling back changes after test completion.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    FastAPI TestClient with overridden get_db dependency.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
