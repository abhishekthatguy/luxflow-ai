# ADR-002: n8n as Orchestration Engine Only

**Status:** Accepted  
**Date:** 2026-07-06  
**Deciders:** Architecture Team

## Context

LexFlow AI requires workflow automation to integrate with external systems (Microsoft 365, court e-filing, email). n8n is selected as the orchestration engine. There is a strong temptation to put business logic in n8n workflows because it is visual and fast to prototype.

However, legal automation requires audit trails, authorization checks, matter wall enforcement, and deterministic business rules — none of which n8n provides natively.

## Options Considered

1. **Business logic in n8n** — Use n8n Code nodes and PostgreSQL nodes for decisions.
   - Pros: Fast prototyping, visual debugging
   - Cons: No audit trail, no authorization, logic not version-controlled in Python, not testable with pytest, vendor lock-in on logic

2. **n8n as orchestration only** — FastAPI owns all decisions; n8n calls external APIs and returns results.
   - Pros: Testable business logic, full audit trail, authorization in one place, n8n replaceable
   - Cons: More code in FastAPI, slightly higher latency for simple flows

3. **Replace n8n with custom orchestrator** — Build workflow engine in FastAPI/Celery.
   - Pros: Full control, no external dependency
   - Cons: Significant development effort, reinventing integration connectors

## Decision

n8n is an **orchestration engine only**. It connects external systems, retries HTTP calls, and routes data. All business logic, authorization, validation, and state management lives in FastAPI. n8n is not publicly accessible.

## Consequences

- **Easier:** Business logic is testable, auditable, and version-controlled in Python
- **Easier:** n8n can be replaced without migrating business logic
- **Easier:** Security review is simpler — n8n has no decision authority
- **Harder:** More FastAPI code for workflow state management
- **Harder:** Developers must resist putting logic in n8n Code nodes
- **Enforcement:** Code review checklist includes "no business logic in n8n"; n8n PostgreSQL nodes are prohibited
