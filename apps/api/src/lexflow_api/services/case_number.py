"""Firm-scoped case number generation (format: YYYY-NNNNN)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.models.cases import Case


async def generate_case_number(session: AsyncSession, *, firm_id: UUID) -> str:
    """Return the next case number for the firm in the current calendar year."""
    year = datetime.now(UTC).year
    prefix = f"{year}-"
    result = await session.execute(
        select(Case.case_number)
        .where(
            Case.firm_id == firm_id,
            Case.case_number.like(f"{prefix}%"),
        )
        .order_by(Case.case_number.desc())
        .limit(1)
    )
    last = result.scalar_one_or_none()
    seq = 1
    if last:
        try:
            seq = int(last.split("-", 1)[1]) + 1
        except (IndexError, ValueError):
            seq = 1
    return f"{prefix}{seq:05d}"
