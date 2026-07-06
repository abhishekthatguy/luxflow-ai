from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from lexflow_api.auth.dependencies import CurrentUser
from lexflow_api.auth.matter_wall import user_can_access_case
from lexflow_api.auth.rbac import FIRM_WIDE_ACCESS_ROLES, ROLE_MANAGING_PARTNER
from lexflow_api.exceptions import NotFoundError


@pytest.mark.asyncio
async def test_matter_wall_admin_sees_firm_case() -> None:
    session = AsyncMock()
    scalar_result = MagicMock()
    scalar_result.scalar_one_or_none.return_value = uuid4()
    session.execute = AsyncMock(return_value=scalar_result)

    user = CurrentUser(
        id=uuid4(),
        firm_id=uuid4(),
        email="admin@lexflow.local",
        first_name="Admin",
        last_name="User",
        roles=FIRM_WIDE_ACCESS_ROLES,
    )
    case_id = uuid4()
    allowed = await user_can_access_case(
        session,
        user_id=user.id,
        firm_id=user.firm_id,
        user_roles=user.roles,
        case_id=case_id,
    )
    assert allowed is True


@pytest.mark.asyncio
async def test_matter_wall_participant_access() -> None:
    session = AsyncMock()
    scalar_result = MagicMock()
    scalar_result.scalar_one_or_none.return_value = uuid4()
    session.execute = AsyncMock(return_value=scalar_result)

    user = CurrentUser(
        id=uuid4(),
        firm_id=uuid4(),
        email="jane@lexflow.local",
        first_name="Jane",
        last_name="Attorney",
        roles={"Attorney"},
    )
    allowed = await user_can_access_case(
        session,
        user_id=user.id,
        firm_id=user.firm_id,
        user_roles=user.roles,
        case_id=uuid4(),
    )
    assert allowed is True


@pytest.mark.asyncio
async def test_matter_wall_denied_returns_none_from_db() -> None:
    session = AsyncMock()
    scalar_result = MagicMock()
    scalar_result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=scalar_result)

    user = CurrentUser(
        id=uuid4(),
        firm_id=uuid4(),
        email="outsider@lexflow.local",
        first_name="Out",
        last_name="Sider",
        roles={"Attorney"},
    )
    allowed = await user_can_access_case(
        session,
        user_id=user.id,
        firm_id=user.firm_id,
        user_roles=user.roles,
        case_id=uuid4(),
    )
    assert allowed is False


def test_not_found_error_is_404() -> None:
    err = NotFoundError("Case not found.")
    assert err.status == 404
    assert err.type_suffix == "not-found"


def test_managing_partner_in_firm_wide_roles() -> None:
    assert ROLE_MANAGING_PARTNER in FIRM_WIDE_ACCESS_ROLES
