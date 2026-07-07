"""Seed John Doe client for the simple insurance demo (idempotent)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sqlalchemy import select

from lexflow_api.db.session import async_session_factory
from lexflow_api.models.cases import Client, ClientType
from lexflow_api.models.identity import Firm


async def seed() -> None:
    async with async_session_factory() as session:
        firm = (
            await session.execute(select(Firm).where(Firm.slug == "lexflow-dev"))
        ).scalar_one_or_none()
        if firm is None:
            print("Run make seed first (firm lexflow-dev missing).")
            return

        existing = (
            await session.execute(
                select(Client).where(
                    Client.firm_id == firm.id,
                    Client.name == "John Doe",
                    Client.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if existing:
            print("OK  John Doe client already exists.")
            return

        session.add(
            Client(
                firm_id=firm.id,
                type=ClientType.INDIVIDUAL.value,
                name="John Doe",
                email="john.doe@gmail.com",
                phone="+1-404-555-0101",
            )
        )
        await session.commit()
        print("OK  Seeded client John Doe (john.doe@gmail.com)")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
