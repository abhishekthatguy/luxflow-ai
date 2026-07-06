# Alembic Migration Pattern

## Purpose

Reversible, review-safe PostgreSQL schema change following LexFlow multi-schema conventions.

## Applies To

`apps/api/alembic/versions/{timestamp}_{seq}_{description}.py`

## Mandatory Reads

- `docs/05-database/migrations.md`
- Relevant `docs/05-database/*-schema.md`
- `docs/09-deployment/zero-downtime-deploy.md`

---

## Structure Template

```
apps/api/alembic/
├── alembic.ini
├── env.py
└── versions/
    └── 20260706_0003_add_documents_version_column.py

# Naming: YYYYMMDD_NNNN_snake_description.py
# NNNN = sequential within date
```

---

## Pseudocode Outline

```
"""add documents version column

Revision ID: 20260706_0003
Revises: 20260706_0002
Create Date: 2026-07-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260706_0003"
down_revision = "20260706_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Schema-qualified table names
    op.add_column(
        "documents",
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        schema="documents",
    )

    # 2. Remove server_default after backfill if needed
    op.alter_column("documents", "version_number", server_default=None, schema="documents")

    # 3. Index — CONCURRENTLY in separate migration for large tables (prod)
    op.create_index(
        "ix_documents_case_id_status",
        "documents",
        ["case_id", "status"],
        schema="documents",
    )


def downgrade() -> None:
    op.drop_index("ix_documents_case_id_status", table_name="documents", schema="documents")
    op.drop_column("documents", "version_number", schema="documents")
```

---

## Schema Creation Order

Per `docs/05-database/migrations.md`:

```
0000 extensions (vector)
→ identity → cases → documents → workflows → ai → audit → shared
```

Never add FK to table that doesn't exist yet.

---

## Zero-Downtime Patterns

| Change | Pattern |
|--------|---------|
| Add nullable column | Deploy code reading old → migration → deploy code reading new |
| Add NOT NULL column | Add nullable → backfill → set NOT NULL in follow-up migration |
| Rename column | Add new → dual-write → migrate data → drop old (multi-deploy) |
| Index on large table | Separate migration with `CREATE INDEX CONCURRENTLY` |
| Drop column | Stop reading in code first → migration drop |

---

## Invariants

| # | Rule |
|---|------|
| 1 | Both `upgrade()` and `downgrade()` implemented |
| 2 | UUID PKs on new tables |
| 3 | Explicit `schema=` on all ops |
| 4 | FK `ON DELETE` documented in PR |
| 5 | No destructive prod ops without DBA approval |
| 6 | Two reviewer rule for locking/risky migrations |

---

## Anti-Patterns

- Manual DDL in production console
- Non-concurrent index on million-row table
- Downgrade that drops data without warning
- Cross-schema FK without schema qualification

---

## Checklist

- [ ] Filename follows convention
- [ ] `down_revision` chain correct
- [ ] Schema doc updated if new table/column
- [ ] Downgrade tested locally
- [ ] FK dependency order respected
- [ ] Index strategy per indexing-strategy.md
- [ ] Zero-downtime sequence documented in PR if non-trivial
- [ ] ORM models updated in same PR
