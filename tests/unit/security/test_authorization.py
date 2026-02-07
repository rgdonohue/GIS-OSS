from __future__ import annotations

import pytest
from fastapi import HTTPException

from src.security.authorization import (
    Permission,
    Role,
    check_permission,
    enforce_permission,
    resolve_role_from_api_key,
)


def test_resolve_role_from_api_key_defaults_to_public_when_empty():
    assert resolve_role_from_api_key("") == Role.PUBLIC


def test_resolve_role_from_api_key_honors_prefixes():
    assert resolve_role_from_api_key("admin:abc123") == Role.ADMIN
    assert resolve_role_from_api_key("elder:abc123") == Role.ELDER
    assert resolve_role_from_api_key("member:abc123") == Role.MEMBER
    assert resolve_role_from_api_key("public:abc123") == Role.PUBLIC


def test_resolve_role_from_api_key_unknown_nonempty_defaults_to_member():
    assert resolve_role_from_api_key("opaque_key_value") == Role.MEMBER


def test_check_permission_enforces_matrix():
    assert check_permission(Role.PUBLIC, Permission.QUERY_PUBLIC) is True
    assert check_permission(Role.PUBLIC, Permission.QUERY_SENSITIVE) is False
    assert check_permission(Role.MEMBER, Permission.QUERY_SENSITIVE) is True
    assert check_permission(Role.ELDER, Permission.QUERY_SACRED) is True
    assert check_permission(Role.ELDER, Permission.EXPORT_DATA) is False
    assert check_permission(Role.ADMIN, Permission.EXPORT_DATA) is True


def test_enforce_permission_raises_for_denied_role():
    checker = enforce_permission(Permission.QUERY_SENSITIVE)
    with pytest.raises(HTTPException) as exc_info:
        checker(x_api_key="")

    assert exc_info.value.status_code == 403
    assert "Insufficient permissions" in exc_info.value.detail


def test_enforce_permission_allows_authorized_role():
    checker = enforce_permission(Permission.QUERY_SENSITIVE)
    checker(x_api_key="member:abc123")
