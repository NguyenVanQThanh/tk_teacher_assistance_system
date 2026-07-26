# File Name: scoping.py
# Description: Helper functions for RBAC Data Scoping — determining accessible class_ids and enforcing class access controls based on user roles (Admin, Teacher, Student).
# Created At: 2026-07-26
# Created By: Tam Khang
# Updated At: 2026-07-26
# Updated By: Tam Khang

import logging
from typing import Optional, List
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.models import User, Role, Class, StudentClass, TeacherSubject

logger = logging.getLogger("academic_scoping")


def get_user_role_name(db: Session, user: User) -> str:
    """Retrieve the role name of the user ('Admin', 'Teacher', 'Student')."""
    role = db.query(Role).filter(Role.role_id == user.role_id).first()
    return role.name if role else "Unknown"


def get_accessible_class_ids(db: Session, user: User, role_name: str) -> Optional[List[UUID]]:
    """
    Get the list of class_ids accessible to the user based on their role:
    - Admin: Returns None (unrestricted access to all classes).
    - Teacher: Returns class_ids where homeroom_teacher_id == user_id or TeacherSubject.teacher_id == user_id.
    - Student: Returns class_ids where StudentClass.student_id == user_id.
    """
    if role_name == "Admin":
        return None

    if role_name == "Teacher":
        # 1. Homeroom classes
        homeroom_class_ids = [
            c.class_id for c in db.query(Class.class_id).filter(
                Class.homeroom_teacher_id == user.user_id,
                Class.status != 'DELETED'
            ).all()
        ]
        # 2. Teaching assigned classes
        assigned_class_ids = [
            ts.class_id for ts in db.query(TeacherSubject.class_id).filter(
                TeacherSubject.teacher_id == user.user_id,
                TeacherSubject.status != 'DELETED'
            ).all()
        ]
        accessible = list(set(homeroom_class_ids + assigned_class_ids))
        return accessible

    if role_name == "Student":
        enrolled_class_ids = [
            sc.class_id for sc in db.query(StudentClass.class_id).filter(
                StudentClass.student_id == user.user_id,
                StudentClass.status != 'DELETED'
            ).all()
        ]
        return enrolled_class_ids

    return []


def check_class_access(db: Session, user: User, class_id: UUID, role_name: Optional[str] = None) -> None:
    """
    Verify if the user has access to a specific class_id.
    Raises 403 ERR-ACAD-CLASS_ACCESS_DENIED if forbidden.
    """
    if role_name is None:
        role_name = get_user_role_name(db, user)

    if role_name == "Admin":
        return

    accessible_ids = get_accessible_class_ids(db, user, role_name)
    if accessible_ids is None or class_id in accessible_ids:
        return

    logger.warning("Data Scoping Access Denied — user %s (role %s) attempted to access class %s", user.user_id, role_name, class_id)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "code": "ERR-ACAD-CLASS_ACCESS_DENIED",
            "message": "Bạn không có quyền truy cập thông tin lớp học này."
        }
    )
