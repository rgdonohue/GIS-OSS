"""
Minimal RBAC scaffolding to support future governance rules.

This module provides deterministic role resolution from API key prefixes and
an explicit permission matrix. Unknown non-empty API keys default to MEMBER.
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
    Resolve role from API key conventions.

    Supported prefixes:
    - admin:
    - elder:
    - member:
    - public:

    If no key is provided, callers are treated as PUBLIC.
    Unknown non-empty keys default to MEMBER.
    """

    normalized = api_key.strip().lower()
    if not normalized:
        return Role.PUBLIC

    if normalized.startswith("admin:") or normalized == "admin":
        return Role.ADMIN
    if normalized.startswith("elder:") or normalized == "elder":
        return Role.ELDER
    if normalized.startswith("member:") or normalized == "member":
        return Role.MEMBER
    if normalized.startswith("public:") or normalized == "public":
        return Role.PUBLIC

    return Role.MEMBER


def check_permission(
    user_role: Role,
    required_permission: Permission,
) -> bool:
    """
    Evaluate whether the role has the required permission.
    """
    role_permissions: dict[Role, set[Permission]] = {
        Role.PUBLIC: {Permission.QUERY_PUBLIC},
        Role.MEMBER: {Permission.QUERY_PUBLIC, Permission.QUERY_SENSITIVE},
        Role.ELDER: {
            Permission.QUERY_PUBLIC,
            Permission.QUERY_SENSITIVE,
            Permission.QUERY_SACRED,
        },
        Role.ADMIN: {
            Permission.QUERY_PUBLIC,
            Permission.QUERY_SENSITIVE,
            Permission.QUERY_SACRED,
            Permission.EXPORT_DATA,
        },
    }
    return required_permission in role_permissions.get(user_role, set())


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
