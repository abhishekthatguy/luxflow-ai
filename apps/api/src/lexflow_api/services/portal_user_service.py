"""Provision client portal users linked to Client records."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from lexflow_api.auth.rbac import ROLE_CLIENT
from lexflow_api.models.cases import Client
from lexflow_api.models.identity import Role, User, UserRole

logger = logging.getLogger(__name__)


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split(None, 1)
    if not parts:
        return "Client", "User"
    if len(parts) == 1:
        return parts[0], "Client"
    return parts[0], parts[1]


class PortalUserService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def ensure_client_role(self, firm_id: UUID) -> Role:
        role = await self._session.scalar(
            select(Role).where(Role.firm_id == firm_id, Role.name == ROLE_CLIENT)
        )
        if role is not None:
            return role
        role = Role(
            firm_id=firm_id,
            name=ROLE_CLIENT,
            description="Client portal — limited external access",
            is_system=True,
        )
        self._session.add(role)
        await self._session.flush()
        logger.info("Created Client role for firm_id=%s", firm_id)
        return role

    async def get_portal_user_by_email(self, email: str) -> User | None:
        normalized = email.strip().lower()
        result = await self._session.execute(
            select(User)
            .options(selectinload(User.roles))
            .where(func.lower(User.email) == normalized, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    def is_portal_user(self, user: User) -> bool:
        return any(role.name == ROLE_CLIENT for role in user.roles)

    async def provision_for_client(self, client: Client) -> User | None:
        if not client.email or not client.email.strip():
            return None

        email = client.email.strip().lower()
        existing = await self.get_portal_user_by_email(email)
        if existing is not None:
            if self.is_portal_user(existing):
                return existing
            logger.warning(
                "portal_user_skipped email=%s reason=existing_non_client_user user_id=%s",
                email,
                existing.id,
            )
            return None

        first, last = _split_name(client.name)
        user = User(
            firm_id=client.firm_id,
            email=email,
            password_hash=None,
            first_name=first,
            last_name=last,
            status="active",
        )
        self._session.add(user)
        await self._session.flush()

        client_role = await self.ensure_client_role(client.firm_id)
        self._session.add(UserRole(user_id=user.id, role_id=client_role.id))
        await self._session.flush()
        logger.info("portal_user_provisioned client_id=%s user_id=%s email=%s", client.id, user.id, email)
        return user
