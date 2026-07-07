"""Admin user management — SystemAdministrator only."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from lexflow_api.auth.dependencies import CurrentUser
from lexflow_api.models.identity import User
from lexflow_api.schemas.admin import AdminUserSummary


class AdminUserService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_users(self, user: CurrentUser) -> list[AdminUserSummary]:
        result = await self._session.execute(
            select(User)
            .options(selectinload(User.roles))
            .where(User.firm_id == user.firm_id, User.deleted_at.is_(None))
            .order_by(User.last_name, User.first_name)
        )
        rows = result.scalars().all()
        return [
            AdminUserSummary(
                id=u.id,
                email=u.email,
                first_name=u.first_name,
                last_name=u.last_name,
                status=u.status,
                roles=sorted(role.name for role in u.roles),
            )
            for u in rows
        ]
