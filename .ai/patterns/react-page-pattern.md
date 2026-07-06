# React Page Pattern

## Purpose

Next.js App Router page with correct route group, Server/Client split, data loading via hooks, and standard UI boundaries.

## Applies To

`apps/web/src/app/(dashboard)|/(portal)|/(auth)/.../page.tsx`

## Mandatory Reads

- `docs/12-ui/page-architecture.md`
- `docs/12-ui/state-management.md`
- `.ai/patterns/react-query-hook-pattern.md`
- `docs/08-security/matter-walls.md` (404 UX)

---

## Structure Template

```
apps/web/src/app/(dashboard)/cases/[caseId]/overview/
├── page.tsx              # Server Component — composes layout
├── loading.tsx           # Skeleton
├── error.tsx             # Error boundary
└── _components/          # Route-colocated components
    └── CaseOverviewHeader.tsx

apps/web/src/hooks/
└── useCaseDetail.ts      # React Query hook
```

---

## Pseudocode Outline

```
# --- page.tsx (Server Component) ---
import { CaseOverviewClient } from "./_components/CaseOverviewClient"

export default async function CaseOverviewPage({ params }: { params: { caseId: string } }) {
  // Optional: prefetch on server if using RSC + dehydrate pattern
  // Default: client fetches via hook for interactivity

  return (
    <div className="space-y-6">
      <CaseOverviewHeader caseId={params.caseId} />
      <CaseOverviewClient caseId={params.caseId} />
    </div>
  )
}


# --- CaseOverviewClient.tsx ("use client") ---
"use client"

export function CaseOverviewClient({ caseId }: { caseId: string }) {
  const { data, isLoading, error } = useCaseDetail(caseId)

  if (isLoading) return <CaseOverviewSkeleton />
  if (error?.status === 404) return <NotFoundMessage resource="case" />
  if (error) return <ErrorAlert error={error} />

  return (
    <>
      <CaseStatusBadge status={data.status} />
      <CaseMetadataGrid case={data} />
      {/* Actions gated by data.permissions from API — not computed client-side */}
    </>
  )
}


# --- loading.tsx ---
export default function Loading() {
  return <CaseOverviewSkeleton />
}
```

---

## Route Group Rules

| Group | Auth | Shell |
|-------|------|-------|
| `(auth)` | Public | Centered card |
| `(dashboard)` | Firm JWT | AppShell + sidebar |
| `(portal)` | Client JWT | PortalShell |

---

## Invariants

| # | Rule |
|---|------|
| 1 | Data via React Query hooks — not inline fetch |
| 2 | Permissions from API response — UI gates only |
| 3 | 404 → generic not-found — no wall leak |
| 4 | Colocate route-specific components in `_components/` |
| 5 | ShadCN primitives from `components/ui/` unmodified |
| 6 | BFF routes only for auth/SSE — not domain CRUD |

---

## Anti-Patterns

- Authorization logic in component (`if role === 'Attorney'`)
- Storing case list in Zustand
- Client Component for entire page when only button needs interactivity
- Direct S3 upload through Next.js API route body

---

## Checklist

- [ ] Route path matches page-architecture.md map
- [ ] Correct route group and layout ancestry
- [ ] loading.tsx + error.tsx present for data routes
- [ ] Hook in `hooks/` with centralized query key
- [ ] 404/403 handled per security UX guidelines
- [ ] Accessibility: headings, focus order
- [ ] Vitest for hook error states
