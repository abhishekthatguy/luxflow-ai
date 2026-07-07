"""Build notification context from case/document/workflow entities."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.config import settings
from lexflow_api.models.cases import Case, Client
from lexflow_api.models.identity import User


async def build_case_context(
    session: AsyncSession,
    *,
    firm_id: UUID,
    case_id: UUID | None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ctx: dict[str, Any] = {
        "timestamp": datetime.now(UTC).strftime("%H:%M UTC"),
        "footer_note": "Generated automatically by LexFlow AI Workflow Engine.",
    }
    if extra:
        ctx.update(extra)

    if case_id is None:
        return ctx

    result = await session.execute(
        select(Case).where(Case.id == case_id, Case.firm_id == firm_id, Case.deleted_at.is_(None))
    )
    case = result.scalar_one_or_none()
    if case is None:
        return ctx

    ctx["case_title"] = case.title
    ctx["case_number"] = case.case_number
    ctx["practice_area"] = case.practice_area
    ctx["priority"] = case.priority
    ctx["case_url"] = f"{settings.notification_web_base_url.rstrip('/')}/cases/{case.id}/overview"

    if case.client_id:
        client = await session.scalar(
            select(Client).where(Client.id == case.client_id, Client.deleted_at.is_(None))
        )
        if client:
            ctx["client_name"] = client.name

    if case.lead_attorney_id:
        attorney = await session.scalar(select(User).where(User.id == case.lead_attorney_id))
        if attorney:
            ctx["attorney_name"] = f"{attorney.first_name} {attorney.last_name}".strip()

    return ctx


def status_color_for(status_badge: str) -> str:
    label = status_badge.lower()
    if "fail" in label or "critical" in label:
        return "#D13438"
    if "approv" in label or "complete" in label:
        return "#107C10"
    if "pending" in label or "required" in label:
        return "#FF8C00"
    return "#0078D4"
