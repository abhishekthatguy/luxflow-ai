"""Seed enterprise RBAC roles and users — idempotent upgrade for existing dev DBs."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sqlalchemy import select

from lexflow_api.auth.password import hash_password
from lexflow_api.db.session import async_session_factory
from lexflow_api.models.identity import Firm, Role, User, UserRole

ROLES = [
    ("Partner", "Equity partner — case operations and AI approval"),
    ("LegalAssistant", "Legal assistant — intake and document support"),
]

USERS = [
    ("admin@example.com", "Sys", "Admin", "SystemAdministrator", "password123"),
    ("equity@example.com", "Sam", "Partner", "Partner", "password123"),
    ("assistant@example.com", "Lisa", "Assistant", "LegalAssistant", "password123"),
]


async def seed() -> None:
    async with async_session_factory() as session:
        firm = (
            await session.execute(select(Firm).where(Firm.slug == "lexflow-dev"))
        ).scalar_one_or_none()
        if firm is None:
            print("Run seed_dev.py first.")
            return

        role_map: dict[str, Role] = {}
        existing_roles = (
            await session.execute(select(Role).where(Role.firm_id == firm.id))
        ).scalars().all()
        for role in existing_roles:
            role_map[role.name] = role

        for name, description in ROLES:
            if name in role_map:
                continue
            role = Role(firm_id=firm.id, name=name, description=description, is_system=True)
            session.add(role)
            await session.flush()
            role_map[name] = role
            print(f"Added role: {name}")

        for email, first, last, role_name, password in USERS:
            existing = (
                await session.execute(select(User).where(User.email == email))
            ).scalar_one_or_none()
            if existing:
                continue
            role = role_map.get(role_name)
            if role is None:
                print(f"Skip {email}: role {role_name} missing")
                continue
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
            session.add(UserRole(user_id=user.id, role_id=role.id))
            print(f"Added user: {email} ({role_name})")

        await session.commit()
        print("Enterprise RBAC seed complete.")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
