"""Role-based access control constants and helpers."""

ROLE_ATTORNEY = "Attorney"
ROLE_PARALEGAL = "Paralegal"
ROLE_MANAGING_PARTNER = "ManagingPartner"
ROLE_SYSTEM_ADMINISTRATOR = "SystemAdministrator"

SYSTEM_ROLES = frozenset(
    {ROLE_ATTORNEY, ROLE_PARALEGAL, ROLE_MANAGING_PARTNER, ROLE_SYSTEM_ADMINISTRATOR}
)

FIRM_WIDE_ACCESS_ROLES = frozenset({ROLE_MANAGING_PARTNER, ROLE_SYSTEM_ADMINISTRATOR})


def has_any_role(user_roles: set[str], required: set[str] | frozenset[str]) -> bool:
    return bool(user_roles & required)


def can_manage_participants(user_roles: set[str], participant_role: str | None) -> bool:
    if has_any_role(user_roles, FIRM_WIDE_ACCESS_ROLES):
        return True
    return participant_role == "lead"
