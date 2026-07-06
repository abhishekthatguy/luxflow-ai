from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.rbac import FIRM_WIDE_ACCESS_ROLES, has_any_role
from lexflow_api.models.cases import Case, CaseParticipant


async def user_can_access_case(
    session: AsyncSession,
    *,
    user_id: UUID,
    firm_id: UUID,
    user_roles: set[str],
    case_id: UUID,
) -> bool:
    if has_any_role(user_roles, FIRM_WIDE_ACCESS_ROLES):
        result = await session.execute(
            select(Case.id).where(
                Case.id == case_id,
                Case.firm_id == firm_id,
                Case.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none() is not None

    result = await session.execute(
        select(CaseParticipant.id)
        .join(Case, Case.id == CaseParticipant.case_id)
        .where(
            CaseParticipant.case_id == case_id,
            CaseParticipant.user_id == user_id,
            Case.firm_id == firm_id,
            Case.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none() is not None


async def get_participant_role(
    session: AsyncSession,
    *,
    user_id: UUID,
    case_id: UUID,
) -> str | None:
    result = await session.execute(
        select(CaseParticipant.role).where(
            CaseParticipant.case_id == case_id,
            CaseParticipant.user_id == user_id,
        )
    )
    row = result.scalar_one_or_none()
    return str(row) if row is not None else None
