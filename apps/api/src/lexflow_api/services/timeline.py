"""Timeline events — async (API) and sync (Celery workers)."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from lexflow_api.models.cases import CaseTimelineEvent


async def write_timeline_event(
    session: AsyncSession,
    *,
    case_id: UUID,
    firm_id: UUID,
    event_type: str,
    title: str,
    actor_id: UUID | None = None,
    payload: dict[str, object] | None = None,
) -> CaseTimelineEvent:
    event = CaseTimelineEvent(
        case_id=case_id,
        firm_id=firm_id,
        event_type=event_type,
        title=title,
        actor_id=actor_id,
        payload=payload or {},
    )
    session.add(event)
    await session.flush()
    return event


def write_timeline_event_sync(
    session: Session,
    *,
    case_id: UUID,
    firm_id: UUID,
    event_type: str,
    title: str,
    actor_id: UUID | None = None,
    payload: dict[str, object] | None = None,
) -> CaseTimelineEvent:
    event = CaseTimelineEvent(
        case_id=case_id,
        firm_id=firm_id,
        event_type=event_type,
        title=title,
        actor_id=actor_id,
        payload=payload or {},
    )
    session.add(event)
    session.flush()
    return event
