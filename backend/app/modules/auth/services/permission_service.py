# File Name: permission_service.py
# Description: Service for calculating effective permissions and caching role mappings.
# Created At: 2026-07-17
# Created By: Tam Khang
# Updated At: 2026-07-17
# Updated By: Tam Khang

from typing import Dict, Set
from uuid import UUID
from sqlalchemy.orm import Session
from app.modules.auth.permission_repository import PermissionRepository

# In-memory dictionary for role permission cache
# Keys: role_id (UUID), Values: Set[str] of permission_codes
_role_permission_cache: Dict[UUID, Set[str]] = {}

class PermissionService:
    @staticmethod
    def get_role_permissions(db: Session, role_id: UUID) -> Set[str]:
        """
        Get permissions for a given role_id, using the in-memory cache if available.
        """
        if role_id in _role_permission_cache:
            return _role_permission_cache[role_id]
        
        # Cache miss: query DB
        permissions = PermissionRepository.get_permissions_by_role(db, role_id)
        perm_set = set(permissions)
        _role_permission_cache[role_id] = perm_set
        return perm_set

    @staticmethod
    def invalidate_role_cache(role_id: UUID = None) -> None:
        """
        Invalidate cache for a specific role_id or clear the entire cache.
        """
        global _role_permission_cache
        if role_id:
            _role_permission_cache.pop(role_id, None)
        else:
            _role_permission_cache.clear()

    @staticmethod
    def get_effective_permissions(db: Session, user_id: UUID, role_id: UUID) -> Set[str]:
        """
        Calculate effective permissions for a user:
        Effective = (Role permissions) + (User overrides 'allow') - (User overrides 'deny')
        Deny overrides always take priority over Allow.
        """
        # 1. Get role permissions (cached)
        role_perms = PermissionService.get_role_permissions(db, role_id)
        
        # 2. Get user permission overrides (never cached)
        overrides = PermissionRepository.get_user_permission_overrides(db, user_id)
        
        # 3. Apply overrides
        allow_overrides = {code for code, effect in overrides if effect == "allow"}
        deny_overrides = {code for code, effect in overrides if effect == "deny"}
        
        # Effective = (Role permissions + Allow overrides) - Deny overrides
        effective_perms = (role_perms | allow_overrides) - deny_overrides
        return effective_perms
