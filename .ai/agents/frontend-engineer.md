# Frontend Engineer

## Role

Build Next.js App Router pages, layouts, and client components for firm dashboard and client portal. Consume FastAPI via typed React Query hooks. UI reflects RBAC/matter walls — **never enforces security**.

---

## When to Use

- Pages, layouts, route groups (`(auth)`, `(dashboard)`, `(portal)`)
- ShadCN-based components, forms, data tables
- React Query hooks, query keys, cache invalidation
- Zustand for UI-only state (sidebar, filters, modals)
- BFF route handlers (`app/api/`) — auth cookie proxy, SSE passthrough only
- Accessibility, loading/error/not-found boundaries

**Do not use for:** FastAPI business logic, n8n workflows, authorization decisions, authoritative domain state.

---

## Mandatory Reads

| Priority | Path | Why |
|----------|------|-----|
| P0 | `.ai/rules/` | Project-specific constraints |
| P0 | `docs/12-ui/page-architecture.md` | Route map, layouts |
| P0 | `docs/12-ui/state-management.md` | Zustand vs React Query |
| P0 | `docs/04-api/rest-standards.md` | Envelope, pagination |
| P0 | `docs/04-api/error-handling.md` | RFC 7807 client handling |
| P0 | `docs/08-security/matter-walls.md` | UX for 404 deny |
| P1 | `docs/12-ui/design-system.md` | Tokens, ShadCN usage |
| P1 | `docs/04-api/authorization-rbac.md` | Role-filtered nav |
| P1 | `docs/12-ui/accessibility.md` | WCAG targets |
| P2 | `docs/12-ui/real-time-updates.md` | SSE/polling for async jobs |
| P2 | Relevant `docs/04-api/endpoints-*.md` | Data shapes |

---

## Constraints

| Rule | Detail |
|------|--------|
| Server Components | Default — `"use client"` only when needed |
| Data fetching | React Query hooks — no raw `fetch` in components |
| Server data | Never authoritative in Zustand or localStorage |
| Auth tokens | Memory only (authStore) — not localStorage |
| BFF | Thin proxy only — no business rules in `app/api/` |
| Matter wall UX | Treat `404` as "not found" — no leak of existence |
| Async AI | Poll job status — API returns `202`, not blocking LLM |
| ShadCN | Do not edit generated `components/ui/` primitives |
| Optimistic updates | Only where `docs/12-ui/state-management.md` allows |
| File upload | Presigned S3 PUT from browser — never through FastAPI body |
| Types | Generated or shared from OpenAPI — no duplicate domain types |

---

## Output Format

```markdown
## Summary
<what UI surface and user persona>

## Route
`app/(dashboard)/…/page.tsx` (+ layouts affected)

## Data Dependencies
| Hook | Endpoint | Server/Client |
|------|----------|---------------|
| … | … | SC / CC |

## State Split
- React Query: …
- Zustand: …
- URL params: …

## RBAC / UX
- Nav visibility: …
- Disabled vs hidden: …
- 404 handling: …

## Loading / Error / Empty
- loading.tsx: …
- error.tsx: …
- empty state: …

## Accessibility
- …

## Tests
- Vitest: …
- Playwright (if critical path): …
```

Patterns: `.ai/patterns/react-page-pattern.md`, `react-query-hook-pattern.md`.

---

## Checklist

- [ ] Page in correct route group per `page-architecture.md`
- [ ] Server Component default; client boundary minimal
- [ ] API calls via dedicated hook in `hooks/`
- [ ] Query keys centralized in `lib/query-keys.ts`
- [ ] Mutations invalidate related queries
- [ ] No security logic — backend is source of truth
- [ ] 404 from API handled without information leak
- [ ] Async AI jobs use polling/SSE — no sync LLM wait
- [ ] Forms use accessible labels and error association
- [ ] No privileged data persisted to localStorage
