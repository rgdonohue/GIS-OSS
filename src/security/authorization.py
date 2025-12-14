"""
Minimal RBAC scaffolding to support future governance rules.

Current implementation is permissive (returns True) but preserves
structure for role/permission checks keyed by API key or other claims.
"""

from __future__ import annotations

from enum import Enum

from fastapi import Header, HTTPException, status


class Role(str, Enum):
    PUBLIC = "public"
    MEMBER = "member"
    ELDER = "elder"
    ADMIN = "admin"


class Permission(str, Enum):
    QUERY_PUBLIC = "query:public"
    QUERY_SENSITIVE = "query:sensitive"
    QUERY_SACRED = "query:sacred"
    EXPORT_DATA = "export:data"


def resolve_role_from_api_key(api_key: str) -> Role:
    """
    Placeholder role resolver. Swap with a lookup (DB/cache) when roles are defined.
    """

    if not api_key:
        return Role.PUBLIC
    return Role.ADMIN


def check_permission(
    user_role: Role,
    required_permission: Permission,
) -> bool:
    """
    Evaluate whether the role has the required permission.
    Currently permissive to avoid breaking flows; tighten as rules are defined.
    """

    return True


def enforce_permission(required: Permission):
    """
    FastAPI dependency factory that validates the caller has the given permission.
    """

    def _checker(x_api_key: str | None = Header(default="", alias="X-API-Key")) -> None:
        role = resolve_role_from_api_key(x_api_key or "")
        if not check_permission(role, required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this operation.",
            )

    return _checker
