"""Resolve notification recipients by RBAC role from database users."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from lexflow_api.config import settings
from lexflow_api.models.identity import User


@dataclass(frozen=True)
class NotificationRecipient:
    user_id: UUID | None
    email: str
    display_name: str
    roles: frozenset[str]


class RecipientResolver:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def resolve_by_roles(
        self,
        *,
        firm_id: UUID,
        roles: set[str] | frozenset[str],
    ) -> list[NotificationRecipient]:
        result = await self._session.execute(
            select(User)
            .where(User.firm_id == firm_id, User.status == "active")
            .options(selectinload(User.roles))
        )
        recipients: list[NotificationRecipient] = []
        seen_emails: set[str] = set()
        role_set = set(roles)

        for user in result.scalars().all():
            user_roles = {r.name for r in user.roles}
            if not user_roles & role_set:
                continue
            email = user.email.strip()
            if not settings.is_deliverable_notification_email(email):
                continue
            email_key = email.lower()
            if email_key in seen_emails:
                continue
            seen_emails.add(email_key)
            recipients.append(
                NotificationRecipient(
                    user_id=user.id,
                    email=email,
                    display_name=f"{user.first_name} {user.last_name}".strip(),
                    roles=frozenset(user_roles),
                )
            )

        for role in role_set:
            fallback = settings.role_email_fallbacks.get(role)
            if fallback and settings.is_deliverable_notification_email(fallback):
                if fallback.lower() not in seen_emails:
                    seen_emails.add(fallback.lower())
                    recipients.append(
                        NotificationRecipient(
                            user_id=None,
                            email=fallback,
                            display_name=role.replace("ManagingPartner", "Managing Partner"),
                            roles=frozenset({role}),
                        )
                    )

        return recipients

    async def resolve_case_participants(
        self,
        *,
        firm_id: UUID,
        user_ids: set[UUID],
    ) -> list[NotificationRecipient]:
        if not user_ids:
            return []
        result = await self._session.execute(
            select(User)
            .where(User.firm_id == firm_id, User.id.in_(user_ids), User.status == "active")
            .options(selectinload(User.roles))
        )
        return [
            NotificationRecipient(
                user_id=u.id,
                email=u.email,
                display_name=f"{u.first_name} {u.last_name}".strip(),
                roles=frozenset(r.name for r in u.roles),
            )
            for u in result.scalars().all()
        ]

    async def resolve_managing_partners(self, *, firm_id: UUID) -> list[NotificationRecipient]:
        return await self.resolve_by_roles(
            firm_id=firm_id,
            roles={"ManagingPartner", "SystemAdministrator"},
        )

    async def resolve_attorneys(self, *, firm_id: UUID) -> list[NotificationRecipient]:
        return await self.resolve_by_roles(
            firm_id=firm_id,
            roles={"Attorney", "Associate", "ManagingPartner"},
        )
