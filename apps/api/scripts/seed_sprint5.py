"""Seed Sprint 5 data — managing partner user for audit UI."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sqlalchemy import select

from lexflow_api.auth.password import hash_password
from lexflow_api.db.session import async_session_factory
from lexflow_api.models.identity import Firm, Role, User, UserRole


async def seed() -> None:
    async with async_session_factory() as session:
        firm = (
            await session.execute(select(Firm).where(Firm.slug == "lexflow-dev"))
        ).scalar_one_or_none()
        if firm is None:
            print("Run seed_dev.py first.")
            return

        existing = (
            await session.execute(select(User).where(User.email == "partner@example.com"))
        ).scalar_one_or_none()
        if existing:
            print("Sprint 5 seed already applied (partner@example.com).")
            return

        role = (
            await session.execute(
                select(Role).where(Role.firm_id == firm.id, Role.name == "ManagingPartner")
            )
        ).scalar_one()
        user = User(
            firm_id=firm.id,
            email="partner@example.com",
            password_hash=hash_password("password123"),
            first_name="Pat",
            last_name="Partner",
            status="active",
        )
        session.add(user)
        await session.flush()
        session.add(UserRole(user_id=user.id, role_id=role.id))
        await session.commit()
        print("Sprint 5 seed complete: partner@example.com / password123 (ManagingPartner)")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
