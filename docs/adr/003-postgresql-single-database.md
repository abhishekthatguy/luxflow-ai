# ADR-003: Single PostgreSQL with Schema Separation

**Status:** Accepted  
**Date:** 2026-07-06  
**Deciders:** Architecture Team

## Context

LexFlow AI has multiple bounded contexts that each own data. The modular monolith decision (ADR-001) allows a single database, but we need to decide how to organize data within it.

## Options Considered

1. **Single schema, shared tables** — All tables in `public` schema.
   - Pros: Simplest
   - Cons: No boundary enforcement, naming collisions, hard to extract

2. **Schema per bounded context** — `identity`, `cases`, `documents`, `workflows`, `ai`, `audit`, `shared`.
   - Pros: Clear ownership, extraction-ready, permission isolation possible
   - Cons: Cross-schema joins require explicit schema prefix

3. **Database per bounded context** — Separate PostgreSQL databases.
   - Pros: Full isolation
   - Cons: No shared transactions, complex ops, premature for monolith

## Decision

Use a **single PostgreSQL database** with **schema separation per bounded context**. Cross-context queries go through application services, not direct cross-schema joins (except read-only reporting).

## Consequences

- **Easier:** Single transaction boundary for consistency
- **Easier:** Simple backup/restore (one database)
- **Easier:** pgvector and full-text search across documents in one query
- **Harder:** Must discipline teams to not cross schema boundaries directly
- **Migration path:** Schema can be moved to separate database during service extraction
