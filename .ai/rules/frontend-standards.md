# Frontend Standards — LexFlow AI

**Applies to:** `apps/web/`, `packages/ui/`, `packages/shared/`, `packages/sdk/`  
**Docs:** `docs/12-ui/`, `docs/04-api/`, `docs/08-security/matter-walls.md`

---

## Purpose

Standards for Next.js App Router, React Query, Zustand, and ShadCN UI. The frontend is a **presentation layer** — never the security boundary.

---

## Core Rules

| Rule | Detail |
|------|--------|
| Server Components default | Add `"use client"` only for interactivity |
| React Query for server data | All API data through typed hooks |
| Zustand for UI state only | Sidebar, modals, filters — not cases/documents |
| ShadCN primitives | Use `components/ui/` — do not edit generated files |
| Generated SDK | Use `packages/sdk` — never hardcode `/api/v1` |
| No domain logic | No RBAC decisions, no matter wall enforcement |
| No secrets in client | No API keys, no LLM keys in browser bundle |

---

## State Boundaries

| State Type | Tool | Examples |
|------------|------|----------|
| Server/API data | React Query | Cases, documents, job status |
| UI chrome | Zustand | Sidebar open, theme, table density |
| Auth tokens | Memory (authStore) | Access token — never localStorage for privileged sessions |
| Ephemeral filters | Zustand or URL params | List filters, sort order |
| Form drafts | react-hook-form + local state | Intake forms |
| URL-shareable state | Search params | Pagination, selected tab |

**Ref:** `docs/12-ui/state-management.md`

### Decision Flow

```
Data from API?           → React Query
Privileged case data?    → React Query (never Zustand persist)
UI-only, cross-component → Zustand
Single component ephemeral → useState
```

---

## Do / Don't

| Do | Don't |
|----|-------|
| Use `useCases()`, `useCaseDetail(id)` hooks | `fetch()` in components |
| Invalidate query keys on mutation success | Manually patch cache with guessed server state |
| Show permission-based UI hints from API flags | Hide buttons as sole security measure |
| Handle RFC 7807 errors via shared `ApiErrorPanel` | Parse error strings ad hoc |
| Use `Suspense` + skeletons for loading | Blank screen while loading |
| Forward `X-Correlation-Id` on BFF routes | Drop correlation on client-initiated requests |

---

## Component Conventions

| Type | Convention |
|------|------------|
| Functional components only | No class components |
| Colocate feature components | `components/cases/CaseTimeline.tsx` |
| Props interfaces | `CaseTimelineProps` — explicit, no `any` |
| Composition | Prefer ShadCN + Tailwind over custom CSS |
| Accessibility | WCAG 2.1 AA — labels, focus, keyboard nav |

### Server vs Client

```tsx
// GOOD — Server Component fetches via server-side client
// app/(dashboard)/cases/[id]/page.tsx
export default async function CaseDetailPage({ params }: { params: { id: string } }) {
  const caseData = await serverApi.getCase(params.id);
  return <CaseDetailView initialData={caseData} />;
}

// GOOD — Client Component for interactivity only
// components/cases/CaseActions.tsx
"use client";
export function CaseActions({ caseId }: { caseId: string }) {
  const { mutate } = useTriggerWorkflow();
  return <Button onClick={() => mutate({ caseId })}>Run Workflow</Button>;
}
```

---

## React Query Patterns

### Query Keys

Centralize in `lib/query-keys.ts`:

```typescript
// GOOD
export const caseKeys = {
  all: ["cases"] as const,
  lists: () => [...caseKeys.all, "list"] as const,
  list: (filters: CaseFilters) => [...caseKeys.lists(), filters] as const,
  detail: (id: string) => [...caseKeys.all, "detail", id] as const,
};
```

### Mutations

```typescript
// GOOD — invalidate affected queries on success
const queryClient = useQueryClient();
return useMutation({
  mutationFn: (body: CreateCaseRequest) => api.cases.create(body),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: caseKeys.lists() });
  },
});
```

| Do | Don't |
|----|-------|
| Optimistic updates only for low-risk UI (task checkbox) | Optimistic update on case creation |
| Poll job status for async AI (`refetchInterval`) | Block UI waiting for LLM |
| Clear cache on logout | Leave case data in memory after sign-out |

---

## Zustand Stores

```typescript
// GOOD — UI-only store, no persistence of case data
interface UiStore {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
}

// BAD — privileged data in Zustand
interface BadStore {
  cases: Case[];  // ← belongs in React Query
}
```

| Do | Don't |
|----|-------|
| `persist` only for non-sensitive UI prefs | Persist tokens or case lists to localStorage |
| Reset stores on logout | Leave stale auth state |

---

## API Client

```typescript
// GOOD — SDK with version constant
import { apiClient, API_VERSION } from "@lexflow/sdk";

// BAD
const BASE = "http://localhost:8000/api/v1";  // hardcoded
```

- Types from `packages/shared` (OpenAPI-generated)
- Attach `Authorization`, `X-Correlation-Id`, `Idempotency-Key` in client middleware
- Parse `application/problem+json` errors

---

## Matter Walls (UX Only)

| Do | Don't |
|----|-------|
| Show empty state on 404 from API | Display "Access Denied" with case ID for 404 |
| Use API-provided `permissions` flags for button visibility | Implement wall logic in frontend |
| Clear case detail cache on 404 | Retry forbidden resource indefinitely |

**Ref:** ADR-007, `docs/08-security/matter-walls.md`

---

## Real-Time Updates

- SSE for notifications and async job status (`docs/12-ui/real-time-updates.md`)
- Invalidate React Query on SSE events — do not duplicate server state in Zustand

---

## Testing (Vitest)

| Test | Tool |
|------|------|
| Components | Vitest + Testing Library |
| Hooks | `renderHook` with QueryClientProvider |
| API client | Mock at fetch/SDK layer |

Test behavior, not implementation. Frontend tests **do not replace** backend matter wall tests.

---

## Frontend PR Checklist

- [ ] No raw `fetch` in components — use hooks
- [ ] No business/authorization logic in frontend
- [ ] `"use client"` only where needed
- [ ] Loading, error, empty states handled
- [ ] Accessibility: labels, focus management
- [ ] No secrets or tokens in localStorage
- [ ] Types from `packages/shared`, not duplicated

---

## References

- [docs/12-ui/state-management.md](../../docs/12-ui/state-management.md)
- [docs/12-ui/page-architecture.md](../../docs/12-ui/page-architecture.md)
- [docs/12-ui/design-system.md](../../docs/12-ui/design-system.md)
- [docs/12-ui/accessibility.md](../../docs/12-ui/accessibility.md)
- [api-standards.md](./api-standards.md)
- [security-rules.md](./security-rules.md)
