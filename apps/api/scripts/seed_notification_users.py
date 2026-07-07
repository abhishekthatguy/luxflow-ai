"""Seed notification RBAC users — emails from environment, not hardcoded in services."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sqlalchemy import select

from lexflow_api.auth.password import hash_password
from lexflow_api.db.session import async_session_factory
from lexflow_api.models.identity import Firm, Role, User, UserRole


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


USERS = [
    ("MANAGING_PARTNER_EMAIL", "Managing", "Partner", "ManagingPartner", "partner@example.com"),
    ("PARTNER_EMAIL", "Sam", "Partner", "Partner", "equity@example.com"),
    ("ATTORNEY_EMAIL", "Jane", "Attorney", "Attorney", "jane@example.com"),
    ("ASSOCIATE_EMAIL", "John", "Associate", "Associate", "john@example.com"),
    ("PARALEGAL_EMAIL", "Alex", "Paralegal", "Paralegal", "alex@example.com"),
    ("LEGAL_ASSISTANT_EMAIL", "Lisa", "Assistant", "LegalAssistant", "assistant@example.com"),
    ("SYSTEM_ADMINISTRATOR_EMAIL", "Sys", "Admin", "SystemAdministrator", "admin@example.com"),
]


async def seed() -> None:
    async with async_session_factory() as session:
        firm = await session.scalar(select(Firm).where(Firm.slug == "lexflow-dev"))
        if firm is None:
            print("Run make seed first — firm lexflow-dev missing.")
            return

        roles = {
            r.name: r
            for r in (
                await session.scalars(select(Role).where(Role.firm_id == firm.id))
            ).all()
        }

        for name, description in [
            ("Partner", "Equity partner — case operations and AI approval"),
            ("LegalAssistant", "Legal assistant — intake and document support"),
        ]:
            if name not in roles:
                role = Role(firm_id=firm.id, name=name, description=description, is_system=True)
                session.add(role)
                await session.flush()
                roles[name] = role
                print(f"Added role: {name}")

        for env_key, first, last, role_name, fallback in USERS:
            email = _env(env_key, fallback)
            if not email:
                continue
            existing = await session.scalar(select(User).where(User.email == email))
            if existing:
                print(f"SKIP  {email} (exists)")
                continue
            role = roles.get(role_name)
            if role is None:
                print(f"SKIP  {email} — role {role_name} missing")
                continue
            user = User(
                firm_id=firm.id,
                email=email,
                password_hash=hash_password("password123"),
                first_name=first,
                last_name=last,
                status="active",
            )
            session.add(user)
            await session.flush()
            session.add(UserRole(user_id=user.id, role_id=role.id))
            print(f"OK    {email} → {role_name}")

        await session.commit()
        print("Notification user seed complete.")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
