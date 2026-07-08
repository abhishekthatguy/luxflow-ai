"""Enterprise permission matrix — maps roles to portal capabilities."""

from __future__ import annotations

from lexflow_api.auth.rbac import (
    ENTERPRISE_ROLES,
    LOGIN_ROLES,
    PORTAL_ROLES,
    ROLE_ATTORNEY,
    ROLE_LEGAL_ASSISTANT,
    ROLE_MANAGING_PARTNER,
    ROLE_PARALEGAL,
    ROLE_PARTNER,
    ROLE_SYSTEM_ADMINISTRATOR,
    has_any_role,
)

# Permission identifiers (also returned on GET /auth/me for UI gating)
PERM_LOGIN = "login"
PERM_PORTAL_ACCESS = "portal:access"
PERM_VIEW_CASES = "case:view"
PERM_MANAGE_CLIENTS = "client:manage"
PERM_CREATE_CASE = "case:create"
PERM_UPLOAD_DOCUMENT = "document:upload"
PERM_REQUEST_AI = "ai:request"
PERM_APPROVE_AI = "ai:approve"
PERM_VIEW_AUDIT = "audit:read"
PERM_OPERATIONS = "operations:dashboard"
PERM_MANAGE_USERS = "admin:users"
PERM_MANAGE_WORKFLOWS = "workflow:manage"

ALL_PERMISSIONS: frozenset[str] = frozenset(
    {
        PERM_LOGIN,
        PERM_PORTAL_ACCESS,
        PERM_VIEW_CASES,
        PERM_MANAGE_CLIENTS,
        PERM_CREATE_CASE,
        PERM_UPLOAD_DOCUMENT,
        PERM_REQUEST_AI,
        PERM_APPROVE_AI,
        PERM_VIEW_AUDIT,
        PERM_OPERATIONS,
        PERM_MANAGE_USERS,
        PERM_MANAGE_WORKFLOWS,
    }
)

_CREATE_CASE_ROLES = ENTERPRISE_ROLES - {ROLE_LEGAL_ASSISTANT}
_UPLOAD_ROLES = ENTERPRISE_ROLES
_REQUEST_AI_ROLES = ENTERPRISE_ROLES - {ROLE_PARALEGAL, ROLE_LEGAL_ASSISTANT}
_APPROVE_AI_ROLES = frozenset(
    {ROLE_SYSTEM_ADMINISTRATOR, ROLE_MANAGING_PARTNER, ROLE_PARTNER, ROLE_ATTORNEY}
)
_AUDIT_ROLES = frozenset({ROLE_SYSTEM_ADMINISTRATOR, ROLE_MANAGING_PARTNER})
_OPERATIONS_ROLES = _AUDIT_ROLES
_MANAGE_USERS_ROLES = frozenset({ROLE_SYSTEM_ADMINISTRATOR})
_MANAGE_WORKFLOWS_ROLES = frozenset({ROLE_SYSTEM_ADMINISTRATOR, ROLE_MANAGING_PARTNER})

_MANAGE_CLIENTS_ROLES = ENTERPRISE_ROLES

_PERMISSION_ROLE_MAP: dict[str, frozenset[str]] = {
    PERM_LOGIN: LOGIN_ROLES,
    PERM_PORTAL_ACCESS: PORTAL_ROLES,
    PERM_VIEW_CASES: ENTERPRISE_ROLES,
    PERM_MANAGE_CLIENTS: _MANAGE_CLIENTS_ROLES,
    PERM_CREATE_CASE: _CREATE_CASE_ROLES,
    PERM_UPLOAD_DOCUMENT: _UPLOAD_ROLES,
    PERM_REQUEST_AI: _REQUEST_AI_ROLES,
    PERM_APPROVE_AI: _APPROVE_AI_ROLES,
    PERM_VIEW_AUDIT: _AUDIT_ROLES,
    PERM_OPERATIONS: _OPERATIONS_ROLES,
    PERM_MANAGE_USERS: _MANAGE_USERS_ROLES,
    PERM_MANAGE_WORKFLOWS: _MANAGE_WORKFLOWS_ROLES,
}


def has_permission(user_roles: set[str], permission: str) -> bool:
    allowed = _PERMISSION_ROLE_MAP.get(permission)
    if allowed is None:
        return False
    return has_any_role(user_roles, allowed)


def permissions_for_roles(user_roles: set[str]) -> list[str]:
    return sorted(p for p in ALL_PERMISSIONS if has_permission(user_roles, p))


def require_permission_message(permission: str) -> str:
    labels = {
        PERM_MANAGE_CLIENTS: "manage clients",
        PERM_CREATE_CASE: "create cases",
        PERM_REQUEST_AI: "request AI summaries",
        PERM_APPROVE_AI: "approve AI summaries",
        PERM_VIEW_AUDIT: "view audit logs",
        PERM_OPERATIONS: "access the operations dashboard",
        PERM_MANAGE_USERS: "manage users",
        PERM_MANAGE_WORKFLOWS: "manage workflows",
    }
    action = labels.get(permission, permission)
    return f"Your role is not permitted to {action}."
