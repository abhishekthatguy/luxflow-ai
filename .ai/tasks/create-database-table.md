# Task: Create Database Table

**LexFlow AI** — AI prompt template for PostgreSQL schema changes.

---

## Prompt (Copy-Paste Ready)

```
You are creating a new database table (or schema change) for LexFlow AI, an enterprise AI automation platform for law firms.

## Feature
{{feature_name}}

## Schema Specification
- PostgreSQL schema: {{schema_name}}
- Table name: {{table_name}}
- Bounded context: {{bounded_context}}
- Ticket: {{ticket_id}}

## Context to Load
Read these before writing any code:

1. `.ai/memory/` — project memory and recent decisions
2. `.ai/rules/` — AI coding rules for this repo
3. `docs/05-database/schema-overview.md` — 7-schema overview and conventions
4. `docs/05-database/{{schema_name}}-schema.md` — target schema documentation
5. `docs/05-database/migrations.md` — Alembic conventions and zero-downtime patterns
6. `docs/05-database/indexing-strategy.md` — index naming and HNSW/pgvector rules
7. `docs/02-domain/{{bounded_context}}-aggregate.md` — domain model alignment
8. `docs/13-decisions/003-postgresql-single-database.md` — schema separation rules
9. `docs/13-decisions/006-transactional-outbox.md` — if table relates to events
10. Existing migrations: `apps/api/alembic/versions/`

## Constraints
- Single PostgreSQL database with schema separation (ADR-003) — no cross-schema FKs without explicit approval
- Table names: `snake_case`, plural (e.g., `case_deadlines`)
- Primary keys: UUID v4 via `gen_random_uuid()` — no serial integers for domain entities
- Timestamps: `created_at`, `updated_at` with `TIMESTAMPTZ NOT NULL DEFAULT now()`
- Soft delete: `deleted_at TIMESTAMPTZ` where applicable — never hard-delete audit data
- Tenant isolation: `firm_id UUID NOT NULL` on all firm-scoped tables
- Case-scoped tables: `case_id UUID NOT NULL` with index
- Migrations MUST be reversible (upgrade + downgrade tested locally)
- Zero-downtime: additive changes first; destructive changes in separate migration
- pgvector columns follow `docs/05-database/documents-schema.md` conventions
- No PII in column names that appear in logs; sensitive fields encrypted at application layer

## Step-by-Step Instructions
1. **Domain alignment** — Confirm entity maps to aggregate in `docs/02-domain/`
2. **Schema doc** — Update `docs/05-database/{{schema_name}}-schema.md` with ER diagram
3. **SQLAlchemy model** — Add model in `services/{{bounded_context}}/infrastructure/models/` or `apps/api/src/models/`
4. **Alembic migration** — Generate with `alembic revision --autogenerate` then hand-review SQL
5. **Indexes** — Add per indexing-strategy.md (FK indexes, query pattern indexes, partial indexes)
6. **Constraints** — CHECK constraints for enums; UNIQUE where business rules require
7. **Repository** — Add repository interface (domain) and SQLAlchemy implementation (infrastructure)
8. **Seed data** — Update `scripts/seed/` if dev fixtures needed
9. **Tests** — Integration test verifying migration up/down and constraint behavior
10. **Retention** — Check `docs/05-database/retention-backup.md` for data lifecycle

## Output Format
Deliver in this order:

### 1. Design Summary
- Table purpose and bounded context ownership
- Column list with types, nullability, defaults
- Indexes and constraints
- FK relationships (same schema only)
- Migration ordering dependency

### 2. ER Diagram
- Mermaid erDiagram for new table and relationships

### 3. Alembic Migration
- Complete `upgrade()` and `downgrade()` functions
- Migration filename: `YYYYMMDD_NNNN_{{description}}.py`

### 4. SQLAlchemy Model
- Complete model class with relationships

### 5. Repository Interface
- Domain interface + infrastructure implementation stubs

### 6. Documentation Update
- Exact additions to `docs/05-database/{{schema_name}}-schema.md`

## Verification Checklist
- [ ] Table in correct PostgreSQL schema (`{{schema_name}}`)
- [ ] Naming conventions followed (snake_case, plural)
- [ ] UUID primary key with `gen_random_uuid()`
- [ ] `created_at` / `updated_at` timestamps present
- [ ] `firm_id` on firm-scoped tables
- [ ] Foreign keys indexed
- [ ] Migration has working `downgrade()`
- [ ] No cross-schema FK without documented exception
- [ ] Zero-downtime safe (additive-first for production)
- [ ] Domain aggregate doc updated
- [ ] Schema overview doc updated if new schema
- [ ] No secrets or environment-specific values in migration
- [ ] Reviewed against indexing-strategy.md
```

---

## Example Variables

| Variable | Example Value |
|----------|---------------|
| `{{feature_name}}` | Case deadlines with reminder configuration |
| `{{schema_name}}` | cases |
| `{{table_name}}` | case_deadlines |
| `{{bounded_context}}` | case_management |
| `{{ticket_id}}` | LEX-144 |
