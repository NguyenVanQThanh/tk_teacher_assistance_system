# File Name: permission_repository.py
# Description: Repository for querying Role Permissions and User Permission Overrides.
# Created At: 2026-07-17
# Created By: Tam Khang
# Updated At: 2026-07-17
# Updated By: Tam Khang

from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Tuple
from models.models import Permission, RolePermission, UserPermission

class PermissionRepository:
    @staticmethod
    def get_permissions_by_role(db: Session, role_id: UUID) -> List[str]:
        """
        Retrieve a list of permission_codes associated with a given role_id.
        Returns an empty list if no permissions are mapped.
        """
        results = (
            db.query(Permission.permission_code)
            .join(RolePermission, Permission.permission_id == RolePermission.permission_id)
            .filter(RolePermission.role_id == role_id)
            .all()
        )
        return [r[0] for r in results]

    @staticmethod
    def get_user_permission_overrides(db: Session, user_id: UUID) -> List[Tuple[str, str]]:
        """
        Retrieve a list of user-specific permission overrides (permission_code, effect) for a given user_id.
        Returns an empty list if no overrides are defined.
        """
        results = (
            db.query(Permission.permission_code, UserPermission.effect)
            .join(UserPermission, Permission.permission_id == UserPermission.permission_id)
            .filter(UserPermission.user_id == user_id)
            .all()
        )
        return [(r[0], r[1]) for r in results]
