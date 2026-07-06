from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import json

from lexflow_api.auth.dependencies import CurrentUser, get_current_user
from lexflow_api.db.session import get_db
from lexflow_api.schemas.common import Envelope, envelope, pagination_meta
from lexflow_api.schemas.notifications import NotificationResponse
from lexflow_api.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


@router.get("", response_model=Envelope[list[NotificationResponse]])
async def list_notifications(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100, alias="pageSize"),
    unread_only: bool = Query(False, alias="unreadOnly"),
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[NotificationResponse]]:
    service = NotificationService(session)
    items, total = await service.list_for_user(
        user, page=page, page_size=page_size, unread_only=unread_only
    )
    return envelope(items, _request_id(request), pagination_meta(page, page_size, total))


@router.get("/unread-count", response_model=Envelope[dict[str, int]])
async def unread_count(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[dict[str, int]]:
    service = NotificationService(session)
    count = await service.unread_count(user)
    return envelope({"count": count}, _request_id(request))


@router.post("/{notification_id}/read", response_model=Envelope[NotificationResponse])
async def mark_read(
    request: Request,
    notification_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[NotificationResponse]:
    service = NotificationService(session)
    item = await service.mark_read(user, notification_id)
    await session.commit()
    return envelope(item, _request_id(request))


@router.get("/stream")
async def notification_stream(
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """SSE heartbeat + unread count — full push delivery deferred to worker."""

    async def event_generator():
        service = NotificationService(session)
        while True:
            count = await service.unread_count(user)
            payload = json.dumps({"type": "unread_count", "count": count})
            yield f"data: {payload}\n\n"
            await asyncio.sleep(30)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
