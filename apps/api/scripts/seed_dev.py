"""Seed local development data for Sprint 2–3 auth and cases."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Allow running as script from repo root or apps/api
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sqlalchemy import select

from lexflow_api.auth.password import hash_password
from lexflow_api.db.session import async_session_factory
from lexflow_api.models.cases import Client, ClientType
from lexflow_api.models.identity import Firm, Role, User, UserRole


ROLES = [
    ("SystemAdministrator", "System administrator"),
    ("ManagingPartner", "Managing partner with firm-wide access"),
    ("Partner", "Equity partner — case operations and AI approval"),
    ("Attorney", "Licensed attorney"),
    ("Associate", "Associate attorney"),
    ("Paralegal", "Paralegal staff"),
    ("LegalAssistant", "Legal assistant — intake and document support"),
]

USERS = [
    ("admin@example.com", "Sys", "Admin", "SystemAdministrator", "password123"),
    ("partner@example.com", "Pat", "ManagingPartner", "ManagingPartner", "password123"),
    ("equity@example.com", "Sam", "Partner", "Partner", "password123"),
    ("jane@example.com", "Jane", "Attorney", "Attorney", "password123"),
    ("john@example.com", "John", "Associate", "Associate", "password123"),
    ("alex@example.com", "Alex", "Paralegal", "Paralegal", "password123"),
    ("assistant@example.com", "Lisa", "Assistant", "LegalAssistant", "password123"),
    ("outsider@example.com", "Outsider", "User", "Attorney", "password123"),
]


async def seed() -> None:
    async with async_session_factory() as session:
        existing = await session.execute(select(Firm).where(Firm.slug == "lexflow-dev"))
        if existing.scalar_one_or_none() is not None:
            print("Seed data already exists (firm lexflow-dev). Skipping.")
            print("Run seed_rbac_enterprise.py to add Partner/LegalAssistant roles on existing DBs.")
            return

        firm = Firm(name="LexFlow Dev Firm", slug="lexflow-dev")
        session.add(firm)
        await session.flush()

        role_map: dict[str, Role] = {}
        for name, description in ROLES:
            role = Role(firm_id=firm.id, name=name, description=description, is_system=True)
            session.add(role)
            role_map[name] = role
        await session.flush()

        for email, first, last, role_name, password in USERS:
            user = User(
                firm_id=firm.id,
                email=email,
                password_hash=hash_password(password),
                first_name=first,
                last_name=last,
                status="active",
            )
            session.add(user)
            await session.flush()
            session.add(UserRole(user_id=user.id, role_id=role_map[role_name].id))

        client = Client(
            firm_id=firm.id,
            type=ClientType.INDIVIDUAL.value,
            name="Acme Corporation",
            email="contact@acme.example",
            phone="+1-555-0100",
        )
        session.add(client)
        await session.commit()
        print("Seed complete: firm=lexflow-dev, 8 users (all enterprise roles), 1 client")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
