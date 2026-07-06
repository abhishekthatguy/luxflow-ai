from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.models.shared import OutboxEvent


async def write_outbox_event(
    session: AsyncSession,
    *,
    firm_id: UUID,
    aggregate_type: str,
    aggregate_id: UUID,
    event_type: str,
    payload: dict[str, object] | None = None,
) -> OutboxEvent:
    event = OutboxEvent(
        firm_id=firm_id,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        event_type=event_type,
        payload=payload or {},
    )
    session.add(event)
    await session.flush()
    return event
