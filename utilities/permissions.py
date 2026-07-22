"""Centralized Role-Based Access Control (RBAC) permission definitions.

This module is the single source of truth for all role and permission
mappings. Both backend controllers/services AND the frontend GUI
import from here (or mirror these definitions) to stay synchronized.

Roles:
    admin   — Full system access.
    editor  — Document management without system administration.
    viewer  — Read-only access.

Usage::

    from utilities.permissions import has_permission, get_role_permissions
    if has_permission("admin", "manage_users"):
        ...
"""

from __future__ import annotations

from enum import Enum
from typing import FrozenSet


# ------------------------------------------------------------------
# Permission constants
# ------------------------------------------------------------------

class Permission(str, Enum):
    """All granular permissions in the system."""

    # Document permissions
    UPLOAD_DOCUMENT = "upload_document"
    DOWNLOAD_DOCUMENT = "download_document"
    DELETE_DOCUMENT = "delete_document"
    EDIT_DOCUMENT = "edit_document"
    SHARE_DOCUMENT = "share_document"
    VIEW_DOCUMENT = "view_document"
    VIEW_ALL_DOCUMENTS = "view_all_documents"

    # Encryption
    USE_ENCRYPTION_TOOLS = "use_encryption_tools"

    # User management
    MANAGE_USERS = "manage_users"
    ASSIGN_ROLES = "assign_roles"

    # Audit
    VIEW_AUDIT_LOGS = "view_audit_logs"

    # System
    MANAGE_SYSTEM_SETTINGS = "manage_system_settings"
    BACKUP_RESTORE = "backup_restore"

    # Profile
    VIEW_PROFILE = "view_profile"
    EDIT_PROFILE = "edit_profile"


# ------------------------------------------------------------------
# Role → Permission mapping
# ------------------------------------------------------------------

_ROLE_PERMISSIONS: dict[str, FrozenSet[Permission]] = {
    "admin": frozenset({
        # Documents
        Permission.UPLOAD_DOCUMENT,
        Permission.DOWNLOAD_DOCUMENT,
        Permission.DELETE_DOCUMENT,
        Permission.EDIT_DOCUMENT,
        Permission.SHARE_DOCUMENT,
        Permission.VIEW_DOCUMENT,
        Permission.VIEW_ALL_DOCUMENTS,
        # Encryption
        Permission.USE_ENCRYPTION_TOOLS,
        # User management
        Permission.MANAGE_USERS,
        Permission.ASSIGN_ROLES,
        # Audit
        Permission.VIEW_AUDIT_LOGS,
        # System
        Permission.MANAGE_SYSTEM_SETTINGS,
        Permission.BACKUP_RESTORE,
        # Profile
        Permission.VIEW_PROFILE,
        Permission.EDIT_PROFILE,
    }),
    "editor": frozenset({
        # Documents
        Permission.UPLOAD_DOCUMENT,
        Permission.DOWNLOAD_DOCUMENT,
        Permission.DELETE_DOCUMENT,  # own only — enforced in service layer
        Permission.EDIT_DOCUMENT,    # own only — enforced in service layer
        Permission.SHARE_DOCUMENT,
        Permission.VIEW_DOCUMENT,
        # Encryption
        Permission.USE_ENCRYPTION_TOOLS,
        # Profile
        Permission.VIEW_PROFILE,
        Permission.EDIT_PROFILE,
    }),
    "viewer": frozenset({
        # Documents (read-only)
        Permission.DOWNLOAD_DOCUMENT,  # permitted docs only
        Permission.VIEW_DOCUMENT,
        # Profile
        Permission.VIEW_PROFILE,
        Permission.EDIT_PROFILE,
    }),
}

# Valid roles kept in sync with models.user.VALID_ROLES
VALID_ROLES: frozenset[str] = frozenset({"admin", "editor", "viewer"})


# ------------------------------------------------------------------
# Public helpers
# ------------------------------------------------------------------

def get_role_permissions(role: str) -> FrozenSet[Permission]:
    """Return the set of permissions for *role*.

    Unknown roles receive no permissions (fail-closed).
    """
    return _ROLE_PERMISSIONS.get(role, frozenset())


def has_permission(role: str, permission: Permission) -> bool:
    """Check whether *role* holds *permission*.

    >>> has_permission("admin", Permission.MANAGE_USERS)
    True
    >>> has_permission("viewer", Permission.UPLOAD_DOCUMENT)
    False
    """
    return permission in get_role_permissions(role)


def has_any_permission(role: str, *permissions: Permission) -> bool:
    """Return True if *role* has at least one of the given permissions."""
    role_perms = get_role_permissions(role)
    return bool(role_perms & frozenset(permissions))


def require_permission(role: str, permission: Permission) -> None:
    """Raise :class:`~exceptions.custom_exceptions.AuthorizationError`
    if *role* does not hold *permission*.
    """
    from exceptions.custom_exceptions import AuthorizationError

    if not has_permission(role, permission):
        raise AuthorizationError(
            f"Role '{role}' does not have the required permission "
            f"'{permission.value}'."
        )


def require_any_permission(role: str, *permissions: Permission) -> None:
    """Raise if *role* has none of the given permissions."""
    from exceptions.custom_exceptions import AuthorizationError

    if not has_any_permission(role, *permissions):
        perm_names = ", ".join(p.value for p in permissions)
        raise AuthorizationError(
            f"Role '{role}' does not have any of the required "
            f"permissions: [{perm_names}]."
        )
