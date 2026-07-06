from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser
from lexflow_api.models.notifications import Notification, NotificationChannel, NotificationStatus
from lexflow_api.schemas.notifications import NotificationResponse


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_in_app(
        self,
        *,
        user_id: UUID,
        firm_id: UUID,
        title: str,
        body: str,
        case_id: UUID | None = None,
        metadata: dict[str, object] | None = None,
    ) -> Notification:
        now = datetime.now(UTC)
        notification = Notification(
            user_id=user_id,
            firm_id=firm_id,
            case_id=case_id,
            channel=NotificationChannel.IN_APP,
            title=title,
            body=body,
            status=NotificationStatus.SENT,
            sent_at=now,
            metadata_=metadata or {},
        )
        self._session.add(notification)
        await self._session.flush()
        return notification

    async def list_for_user(
        self,
        user: CurrentUser,
        *,
        page: int = 1,
        page_size: int = 25,
        unread_only: bool = False,
    ) -> tuple[list[NotificationResponse], int]:
        filters = [Notification.user_id == user.id, Notification.firm_id == user.firm_id]
        if unread_only:
            filters.append(Notification.status != NotificationStatus.READ)

        count_stmt = select(func.count()).select_from(Notification).where(*filters)
        total = int((await self._session.scalar(count_stmt)) or 0)

        stmt = (
            select(Notification)
            .where(*filters)
            .order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self._session.scalars(stmt)).all()
        return [NotificationResponse.model_validate(row) for row in rows], total

    async def mark_read(self, user: CurrentUser, notification_id: UUID) -> NotificationResponse:
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user.id,
            Notification.firm_id == user.firm_id,
        )
        notification = await self._session.scalar(stmt)
        if not notification:
            from lexflow_api.exceptions import NotFoundError

            raise NotFoundError("Notification not found.")
        notification.status = NotificationStatus.READ
        notification.read_at = datetime.now(UTC)
        await self._session.flush()
        return NotificationResponse.model_validate(notification)

    async def unread_count(self, user: CurrentUser) -> int:
        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user.id,
                Notification.firm_id == user.firm_id,
                Notification.status != NotificationStatus.READ,
            )
        )
        return int((await self._session.scalar(stmt)) or 0)
