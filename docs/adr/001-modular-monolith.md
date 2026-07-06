# ADR-001: Start with Modular Monolith

**Status:** Accepted  
**Date:** 2026-07-06  
**Deciders:** Architecture Team

## Context

LexFlow AI has multiple bounded contexts (Case Management, Document Management, AI, Workflow Orchestration, etc.) that could be deployed as separate microservices. However, the team is pre-implementation with no production traffic patterns to justify the operational complexity of microservices.

The target deployment is a single law firm (not multi-tenant SaaS initially), and the team size is expected to be 5–10 engineers in Phase 1.

## Options Considered

1. **Microservices from day one** — Independent deployable services per bounded context with separate databases.
   - Pros: Independent scaling, team autonomy, technology flexibility
   - Cons: Operational complexity (service mesh, distributed tracing, multiple deploys), premature optimization, slower initial development

2. **Modular monolith** — Single FastAPI application with bounded context modules, shared PostgreSQL with schema separation.
   - Pros: Simple deployment, fast development, easy refactoring, single transaction boundary, can extract services later
   - Cons: All modules deploy together, shared database scaling ceiling

3. **Monolith without boundaries** — Single codebase with no module separation.
   - Pros: Simplest initially
   - Cons: Becomes unmaintainable quickly, no extraction path

## Decision

Start with a **modular monolith**: a single FastAPI application organized into bounded context modules (`services/{context}/`), with PostgreSQL schema separation per context. Extract to independent services only when metrics (CPU, memory, deployment frequency conflicts) justify the operational cost.

## Consequences

- **Easier:** Single deploy, shared transactions, simpler debugging, faster feature development
- **Easier:** Clean module boundaries preserved for future extraction
- **Harder:** Cannot scale individual contexts independently in Phase 1
- **Harder:** All engineers must understand the full codebase initially
- **Migration path:** Each bounded context module has its own schema, repository interfaces, and event contracts — extraction requires adding an HTTP/gRPC adapter and moving the schema to a separate database
