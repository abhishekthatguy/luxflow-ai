from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.models.audit import AuditLog


async def write_audit_log(
    session: AsyncSession,
    *,
    firm_id: UUID,
    actor_id: UUID | None,
    action: str,
    resource_type: str,
    resource_id: UUID | None = None,
    details: dict[str, object] | None = None,
) -> AuditLog:
    entry = AuditLog(
        firm_id=firm_id,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
    )
    session.add(entry)
    await session.flush()
    return entry
