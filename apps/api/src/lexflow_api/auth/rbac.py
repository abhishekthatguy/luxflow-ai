"""Role-based access control constants and helpers."""

ROLE_SYSTEM_ADMINISTRATOR = "SystemAdministrator"
ROLE_MANAGING_PARTNER = "ManagingPartner"
ROLE_PARTNER = "Partner"
ROLE_ATTORNEY = "Attorney"
ROLE_ASSOCIATE = "Associate"
ROLE_PARALEGAL = "Paralegal"
ROLE_LEGAL_ASSISTANT = "LegalAssistant"
ROLE_CLIENT = "Client"

ENTERPRISE_ROLES = frozenset(
    {
        ROLE_SYSTEM_ADMINISTRATOR,
        ROLE_MANAGING_PARTNER,
        ROLE_PARTNER,
        ROLE_ATTORNEY,
        ROLE_ASSOCIATE,
        ROLE_PARALEGAL,
        ROLE_LEGAL_ASSISTANT,
    }
)

PORTAL_ROLES = frozenset({ROLE_CLIENT})
LOGIN_ROLES = ENTERPRISE_ROLES | PORTAL_ROLES

SYSTEM_ROLES = ENTERPRISE_ROLES | PORTAL_ROLES

FIRM_WIDE_ACCESS_ROLES = frozenset({ROLE_MANAGING_PARTNER, ROLE_SYSTEM_ADMINISTRATOR})


def has_any_role(user_roles: set[str], required: set[str] | frozenset[str]) -> bool:
    return bool(user_roles & required)


def can_manage_participants(user_roles: set[str], participant_role: str | None) -> bool:
    if has_any_role(user_roles, FIRM_WIDE_ACCESS_ROLES):
        return True
    return participant_role == "lead"
