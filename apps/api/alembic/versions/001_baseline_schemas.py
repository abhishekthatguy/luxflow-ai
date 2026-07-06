"""Baseline empty schemas per bounded context.

Revision ID: 001_baseline
Revises:
Create Date: 2026-07-06
"""

from alembic import op

revision = "001_baseline"
down_revision = None
branch_labels = None
depends_on = None

SCHEMAS = ("identity", "cases", "documents", "workflows", "ai", "audit", "shared")


def upgrade() -> None:
    for schema in SCHEMAS:
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")


def downgrade() -> None:
    for schema in reversed(SCHEMAS):
        op.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
