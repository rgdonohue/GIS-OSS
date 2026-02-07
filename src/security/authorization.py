"""
Minimal RBAC scaffolding to support future governance rules.

This module provides deterministic role resolution from API key prefixes and
an explicit permission matrix. Unknown non-empty API keys default to MEMBER.
"""

from __future__ import annotations

import hashlib
from enum import Enum

from fastapi import Header, HTTPException, status
from psycopg2.extensions import connection as PGConnection


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


def api_key_fingerprint(api_key: str) -> str:
    normalized = api_key.strip()
    return hashlib.sha256(normalized.encode("utf-8", errors="ignore")).hexdigest()


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


def _normalize_role(raw_role: str | None) -> Role | None:
    if raw_role is None:
        return None
    normalized = raw_role.strip().lower()
    for role in Role:
        if role.value == normalized:
            return role
    return None


def resolve_role_from_database(conn: PGConnection, api_key: str) -> Role | None:
    """
    Resolve role from governance.api_keys using a SHA-256 API key fingerprint.
    """

    normalized = api_key.strip()
    if not normalized:
        return Role.PUBLIC

    key_hash = api_key_fingerprint(normalized)
    query = """
        SELECT role
        FROM governance.api_keys
        WHERE key_hash = %s
          AND active = TRUE
        LIMIT 1
    """
    with conn.cursor() as cur:
        cur.execute(query, (key_hash,))
        row = cur.fetchone()
    if not row:
        return None
    return _normalize_role(row[0])


def resolve_role(
    *,
    api_key: str,
    authz_backend: str,
    conn: PGConnection | None = None,
) -> Role:
    backend = authz_backend.strip().lower()
    if backend == "database" and conn is not None:
        try:
            role = resolve_role_from_database(conn, api_key)
        except Exception:
            role = None
        if role is not None:
            return role
    return resolve_role_from_api_key(api_key)


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
