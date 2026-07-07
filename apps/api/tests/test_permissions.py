"""Enterprise permission matrix unit tests."""

import pytest

from lexflow_api.auth.permissions import (
    PERM_APPROVE_AI,
    PERM_CREATE_CASE,
    PERM_MANAGE_USERS,
    PERM_MANAGE_WORKFLOWS,
    PERM_OPERATIONS,
    PERM_REQUEST_AI,
    PERM_VIEW_AUDIT,
    has_permission,
    permissions_for_roles,
)
from lexflow_api.auth.rbac import (
    ROLE_ASSOCIATE,
    ROLE_ATTORNEY,
    ROLE_LEGAL_ASSISTANT,
    ROLE_MANAGING_PARTNER,
    ROLE_PARALEGAL,
    ROLE_PARTNER,
    ROLE_SYSTEM_ADMINISTRATOR,
)


@pytest.mark.parametrize(
    ("roles", "permission", "expected"),
    [
        ({ROLE_LEGAL_ASSISTANT}, PERM_CREATE_CASE, False),
        ({ROLE_PARALEGAL}, PERM_CREATE_CASE, True),
        ({ROLE_PARALEGAL}, PERM_REQUEST_AI, False),
        ({ROLE_LEGAL_ASSISTANT}, PERM_REQUEST_AI, False),
        ({ROLE_ASSOCIATE}, PERM_REQUEST_AI, True),
        ({ROLE_ASSOCIATE}, PERM_APPROVE_AI, False),
        ({ROLE_PARTNER}, PERM_APPROVE_AI, True),
        ({ROLE_ATTORNEY}, PERM_APPROVE_AI, True),
        ({ROLE_MANAGING_PARTNER}, PERM_VIEW_AUDIT, True),
        ({ROLE_ATTORNEY}, PERM_VIEW_AUDIT, False),
        ({ROLE_SYSTEM_ADMINISTRATOR}, PERM_MANAGE_USERS, True),
        ({ROLE_MANAGING_PARTNER}, PERM_MANAGE_USERS, False),
        ({ROLE_MANAGING_PARTNER}, PERM_MANAGE_WORKFLOWS, True),
        ({ROLE_ATTORNEY}, PERM_OPERATIONS, False),
    ],
)
def test_enterprise_permission_matrix(roles: set[str], permission: str, expected: bool) -> None:
    assert has_permission(roles, permission) is expected


def test_admin_has_full_operational_permissions() -> None:
    perms = set(permissions_for_roles({ROLE_SYSTEM_ADMINISTRATOR}))
    assert PERM_MANAGE_USERS in perms
    assert PERM_MANAGE_WORKFLOWS in perms
    assert PERM_OPERATIONS in perms
    assert PERM_APPROVE_AI in perms
