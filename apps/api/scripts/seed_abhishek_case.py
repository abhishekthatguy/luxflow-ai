"""Seed Abhishek S client for motor vehicle insurance PDF demo (idempotent)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sqlalchemy import select

from lexflow_api.db.session import async_session_factory
from lexflow_api.models.cases import Client, ClientType
from lexflow_api.models.identity import Firm

CLIENT_NAME = "Abhishek S"
CLIENT_EMAIL = "kashyapabhi688@gmail.com"
CLIENT_PHONE = "+91-9621482434"


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
                    Client.name == CLIENT_NAME,
                    Client.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if existing:
            existing.email = CLIENT_EMAIL
            existing.phone = CLIENT_PHONE
            await session.commit()
            print(f"OK  Updated client {CLIENT_NAME} ({CLIENT_EMAIL})")
            return

        session.add(
            Client(
                firm_id=firm.id,
                type=ClientType.INDIVIDUAL.value,
                name=CLIENT_NAME,
                email=CLIENT_EMAIL,
                phone=CLIENT_PHONE,
            )
        )
        await session.commit()
        print(f"OK  Seeded client {CLIENT_NAME} ({CLIENT_EMAIL})")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
