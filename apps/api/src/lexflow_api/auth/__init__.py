from lexflow_api.auth.dependencies import CurrentUser, get_current_user
from lexflow_api.auth.jwt import create_access_token, decode_access_token, generate_refresh_token
from lexflow_api.auth.matter_wall import get_participant_role, user_can_access_case
from lexflow_api.auth.password import hash_password, verify_password
from lexflow_api.auth.rbac import (
    FIRM_WIDE_ACCESS_ROLES,
    ROLE_ATTORNEY,
    ROLE_MANAGING_PARTNER,
    ROLE_PARALEGAL,
    ROLE_SYSTEM_ADMINISTRATOR,
    can_manage_participants,
    has_any_role,
)

__all__ = [
    "CurrentUser",
    "FIRM_WIDE_ACCESS_ROLES",
    "ROLE_ATTORNEY",
    "ROLE_MANAGING_PARTNER",
    "ROLE_PARALEGAL",
    "ROLE_SYSTEM_ADMINISTRATOR",
    "can_manage_participants",
    "create_access_token",
    "decode_access_token",
    "generate_refresh_token",
    "get_current_user",
    "get_participant_role",
    "hash_password",
    "has_any_role",
    "user_can_access_case",
    "verify_password",
]
