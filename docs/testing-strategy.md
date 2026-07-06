# Testing Strategy

**LexFlow AI** — Quality Assurance Framework  
**Version:** 1.0  
**Status:** Draft — Pre-Implementation  
**Last Updated:** 2026-07-06

---

## 1. Overview

LexFlow AI requires comprehensive testing across all layers — from unit tests for domain logic to end-to-end tests for critical user journeys. Testing is integrated into CI/CD and gates deployment.

---

## 2. Testing Pyramid

```
                    ┌─────────┐
                    │   E2E   │  ~10 tests — critical journeys
                   ┌┴─────────┴┐
                   │ Integration│  ~100 tests — API, DB, queue
                  ┌┴───────────┴┐
                  │    Unit     │  ~500+ tests — domain, services
                  └─────────────┘
```

| Layer | Scope | Speed | Coverage Target |
|-------|-------|-------|-----------------|
| Unit | Domain logic, use cases, utilities | < 10s total | 90% line coverage (domain + application layers) |
| Integration | API endpoints, database, queue, external adapters (mocked) | < 5 min total | All API endpoints, all event handlers |
| E2E | Browser-based user journeys | < 15 min total | Critical paths (see §5) |
| Load | Performance under scale | On demand | 1000 concurrent users, 50K workflows/month |
| Security | Auth, matter walls, injection | Every PR + weekly | All auth paths, all RBAC combinations |

---

## 3. Unit Tests

### 3.1 Backend (Python — pytest)

```
services/{context}/tests/
├── domain/
│   ├── test_case_entity.py          # Invariants, state transitions
│   ├── test_case_status_machine.py
│   └── test_value_objects.py
├── application/
│   ├── test_create_case.py          # Use case tests with mocked repos
│   ├── test_authorization.py        # RBAC + matter wall logic
│   └── test_ai_summary_approval.py
```

**Rules:**
- Domain tests have zero external dependencies
- Application tests mock infrastructure (repositories, external adapters)
- Use factories (factory_boy) for test data
- Parameterized tests for RBAC permission matrix

### 3.2 Frontend (TypeScript — Vitest + Testing Library)

```
apps/web/src/
├── components/cases/__tests__/
├── hooks/__tests__/
└── lib/__tests__/
```

**Rules:**
- Component tests focus on behavior, not implementation
- Mock API client — never hit real backend in unit tests
- Test accessibility (axe-core integration)

---

## 4. Integration Tests

### 4.1 API Integration (pytest + Testcontainers)

```
tests/integration/
├── conftest.py                       # Testcontainers: PostgreSQL, Redis, RabbitMQ
├── test_case_api.py
├── test_document_api.py
├── test_auth_api.py
├── test_matter_wall.py               # Critical — authorization tests
├── test_workflow_trigger.py
├── test_ai_summary_flow.py
└── test_audit_logging.py
```

**Infrastructure:** Testcontainers spin up real PostgreSQL (with pgvector), Redis, and RabbitMQ in Docker during test runs.

### 4.2 Key Integration Scenarios

| Scenario | Validates |
|----------|-----------|
| Create case → audit log written | End-to-end audit trail |
| Upload document → OCR event → embedding generated | Document pipeline |
| Trigger workflow → n8n mock callback → case updated | Workflow orchestration |
| Request AI summary → approve → visible in case | AI + approval flow |
| User without matter wall access → 404 | Security — matter walls |
| Concurrent case update → 409 conflict | Optimistic concurrency |
| Duplicate idempotency key → same response | Idempotency |

### 4.3 Event Handler Tests

```
tests/integration/events/
├── test_case_created_handler.py
├── test_document_processed_handler.py
├── test_workflow_completed_handler.py
└── test_outbox_publisher.py
```

---

## 5. End-to-End Tests (Playwright)

```
tests/e2e/
├── auth.spec.ts                      # Login, logout, token refresh
├── case-intake.spec.ts               # Full intake journey
├── document-upload.spec.ts           # Upload, view, download
├── ai-summary.spec.ts                # Request, review, approve summary
├── workflow-trigger.spec.ts          # Trigger workflow, monitor status
├── approval-flow.spec.ts             # Request and decide approval
├── matter-wall.spec.ts               # Verify access restrictions in UI
└── admin-user-management.spec.ts     # Admin creates user, assigns role
```

**Environment:** E2E runs against staging with seeded test data.

---

## 6. Load Tests (k6)

```
tests/load/
├── scenarios/
│   ├── api-read-heavy.js             # 1000 concurrent users browsing cases
│   ├── document-upload-burst.js      # 100 simultaneous uploads
│   ├── workflow-trigger-sustained.js # 50K workflows over 24 hours
│   └── ai-request-sustained.js       # AI endpoint under load
└── thresholds/
    └── production.json               # p95 < 500ms, error rate < 1%
```

Run before major releases and after infrastructure changes.

---

## 7. Security Tests

| Test | Tool | Frequency |
|------|------|-----------|
| Matter wall authorization | pytest (automated) | Every PR |
| RBAC permission matrix | pytest (parameterized) | Every PR |
| SQL injection | pytest + OWASP ZAP | Weekly (staging) |
| XSS | Playwright + manual | Weekly (staging) |
| Dependency vulnerabilities | Dependabot + Trivy | Every PR |
| Secret scanning | git-secrets / TruffleHog | Every PR |
| Container scanning | Trivy | Every build |

---

## 8. CI Test Pipeline

```yaml
# Conceptual CI stages
stages:
  - lint          # ruff, mypy, eslint, tsc
  - unit          # pytest (unit), vitest
  - integration   # pytest (integration) with Testcontainers
  - build         # Docker build
  - scan          # Trivy container scan
  - deploy-staging
  - e2e           # Playwright against staging
  - deploy-production  # Manual approval gate
```

**PR requirements:**
- All unit + integration tests pass
- No CRITICAL/HIGH container vulnerabilities
- Coverage does not decrease
- Matter wall tests pass (non-negotiable)

---

## 9. Test Data Management

| Environment | Data Source |
|-------------|-------------|
| Unit/Integration | Factories + fixtures (generated per test) |
| Local dev | `scripts/seed/dev_seed.py` — realistic but fake data |
| Staging | Anonymized production subset (refreshed monthly) |
| E2E | Dedicated test firm with known users and cases |
| Load | Generated at scale via k6 scripts |

**Never use real client data in non-production environments.**

---

## 10. Related Documents

- [development-standards.md](./development-standards.md)
- [deployment-architecture.md](./deployment-architecture.md)
- [security-architecture.md](./security-architecture.md)
- [api-architecture.md](./api-architecture.md)
