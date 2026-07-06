# Naming Conventions — LexFlow AI

**Applies to:** Python, TypeScript, SQL, API routes, events, n8n, Terraform  
**Docs:** `docs/folder-structure.md`, `docs/04-api/rest-standards.md`

---

## Purpose

Single reference for naming across the monorepo. Consistent names reduce cognitive load and enable safe AI-assisted refactors.

---

## Python (Backend)

| Artifact | Convention | Example |
|----------|------------|---------|
| Packages/modules | `snake_case` | `case_management/` |
| Files | `snake_case` | `create_case.py` |
| Classes | `PascalCase` | `CreateCaseCommand` |
| Functions/methods | `snake_case` | `create_case()` |
| Constants | `SCREAMING_SNAKE` | `MAX_UPLOAD_SIZE_BYTES` |
| Private | Leading `_` | `_validate_participant()` |
| Type aliases | `PascalCase` | `CaseId = UUID` |
| Protocols/interfaces | `PascalCase` + role suffix | `CaseRepository`, `LLMProvider` |

### Use Case Naming

| Type | Pattern | Example |
|------|---------|---------|
| Command | `{Verb}{Noun}Command` | `AssignParticipantCommand` |
| Command handler | `{Verb}{Noun}Handler` | `AssignParticipantHandler` |
| Query | `Get{Noun}Query` | `GetCaseDetailQuery` |
| Query handler | `Get{Noun}Handler` | `GetCaseDetailHandler` |

### Domain Events

| Rule | Example |
|------|---------|
| Past tense PascalCase | `CaseCreated`, `DocumentUploaded` |
| Noun + action completed | `WorkflowCompleted`, `SummaryGenerated` |

---

## TypeScript (Frontend)

| Artifact | Convention | Example |
|----------|------------|---------|
| Components | `PascalCase.tsx` | `CaseTimeline.tsx` |
| Hooks | `camelCase` with `use` prefix | `useCaseDetail.ts` |
| Utilities | `camelCase.ts` | `formatDeadline.ts` |
| Types/interfaces | `PascalCase` | `CaseSummary` |
| Constants | `SCREAMING_SNAKE` | `API_VERSION` |
| Zustand stores | `{name}Store.ts` | `uiStore.ts` |
| React Query keys | Factory in `query-keys.ts` | `caseKeys.detail(id)` |
| App Router pages | `lowercase` folders | `cases/[id]/page.tsx` |

---

## REST API

| Artifact | Convention | Example |
|----------|------------|---------|
| Collection paths | Plural nouns, kebab-case | `/api/v1/cases` |
| Resource IDs | UUID path param camelCase in OpenAPI | `{caseId}` |
| Sub-resources | Nested under parent | `/cases/{caseId}/tasks` |
| Actions | Verb phrase kebab-case | `/workflows/trigger` |
| Query params | camelCase | `?includeArchived=true` |
| JSON fields | camelCase | `practiceArea`, `createdAt` |
| Headers | Standard casing | `X-Correlation-Id`, `Idempotency-Key` |

**Ref:** `docs/04-api/rest-standards.md`, `docs/04-api/versioning.md`

---

## PostgreSQL

| Artifact | Convention | Example |
|----------|------------|---------|
| Schemas | `snake_case` singular context | `cases`, `documents`, `ai` |
| Tables | `snake_case`, plural | `case_participants`, `audit_logs` |
| Columns | `snake_case` | `practice_area`, `created_at` |
| Primary keys | `id` (UUID) | `id` |
| Foreign keys | `{entity}_id` | `case_id`, `user_id` |
| Indexes | `idx_{table}_{columns}` | `idx_cases_firm_id_status` |
| Constraints | `{table}_{description}` | `cases_status_check` |

---

## n8n Workflows

| Artifact | Convention | Example |
|----------|------------|---------|
| File name | `{domain}-{action}-v{major}.json` | `intake-new-client-v1.json` |
| Workflow slug | kebab-case | `intake-new-client-v1` |
| Webhook path segment | matches slug | `/internal/webhooks/n8n/intake-new-client-v1` |
| Folder | domain category | `n8n/workflows/intake/` |

---

## Environment Variables

| Pattern | Example |
|---------|---------|
| `SCREAMING_SNAKE` | `DATABASE_URL`, `JWT_PUBLIC_KEY` |
| Prefix by service | `AZURE_OPENAI_ENDPOINT` |
| No secrets in names that leak values | Use `JWT_SIGNING_KEY_REF` for secret ARNs |

---

## Terraform & AWS

| Artifact | Convention | Example |
|----------|------------|---------|
| Resources | `{env}-{service}-{resource}` | `prod-api-alb` |
| Secrets Manager paths | `{env}/{category}/{name}` | `production/jwt/signing-key` |

---

## Test IDs

| Layer | Pattern | Example |
|-------|---------|---------|
| Integration | `TEST-INT-{area}-{number}` | `TEST-INT-MW-001` |
| Unit | `TEST-UNIT-{context}-{number}` | `TEST-UNIT-CASE-012` |
| E2E | `TEST-E2E-{journey}-{number}` | `TEST-E2E-INTAKE-001` |

---

## Do / Don't

| Do | Don't |
|----|-------|
| Use ubiquitous language from domain glossary | Invent synonyms (`matter` vs `case` inconsistently) |
| Match existing module names when extending | Create parallel `case_mgmt` and `case_management` |
| Use `case` in code; document "matter" for legal audience | Mix terms in same API contract |
| Version prompts and workflows in slug | Overwrite active template without version bump |

**Ref:** `docs/02-domain/ubiquitous-language.md`

---

## Good vs Bad

```
# BAD — inconsistent API + DB naming
GET /api/v1/case/{id}/CaseDocuments
table: CaseDocument

# GOOD
GET /api/v1/cases/{caseId}/documents
table: documents (schema: documents)
```

```
# BAD — vague event name
Event: CaseUpdate

# GOOD — specific past tense
Event: CaseStatusChanged
```

---

## References

- [folder-structure.md](./folder-structure.md)
- [api-standards.md](./api-standards.md)
- [docs/02-domain/ubiquitous-language.md](../../docs/02-domain/ubiquitous-language.md)
