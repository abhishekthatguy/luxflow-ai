# React Query Hook Pattern

## Purpose

Typed data-fetching hook wrapping the FastAPI client with consistent query keys, error parsing, cache invalidation, and mutation side effects.

## Applies To

`apps/web/src/hooks/use*.ts` and `apps/web/src/lib/query-keys.ts`

## Mandatory Reads

- `docs/12-ui/state-management.md`
- `docs/04-api/rest-standards.md`
- `docs/04-api/error-handling.md`

---

## Structure Template

```
apps/web/src/
├── lib/
│   ├── api-client.ts       # Typed fetch wrapper (envelope unwrap)
│   └── query-keys.ts       # Hierarchical key factory
└── hooks/
    ├── useCases.ts         # list + detail
    ├── useCreateCase.ts    # mutation
    └── useCaseTimeline.ts  # infinite query
```

---

## Pseudocode Outline

```
# --- query-keys.ts ---
export const queryKeys = {
  cases: {
    all: ["cases"] as const,
    lists: () => [...queryKeys.cases.all, "list"] as const,
    list: (filters: CaseFilters) => [...queryKeys.cases.lists(), filters] as const,
    details: () => [...queryKeys.cases.all, "detail"] as const,
    detail: (id: string) => [...queryKeys.cases.details(), id] as const,
  },
  documents: { ... },
}


# --- useCaseDetail.ts ---
export function useCaseDetail(caseId: string) {
  return useQuery({
    queryKey: queryKeys.cases.detail(caseId),
    queryFn: () => apiClient.get<CaseResponse>(`/api/v1/cases/${caseId}`),
    enabled: !!caseId,
    staleTime: 30_000,
    retry: (count, error) => error.status !== 404 && count < 2,
  })
}


# --- useCreateCase.ts ---
export function useCreateCase() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (input: CreateCaseRequest) =>
      apiClient.post<CaseResponse>("/api/v1/cases", input, {
        headers: idempotencyHeader(),  // optional UUID per submit
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.cases.lists() })
      queryClient.setQueryData(queryKeys.cases.detail(data.id), data)
    },
    onError: (error: ApiError) => {
      // RFC 7807 — surface validation errors to form
    },
  })
}


# --- useCaseAuditLog.ts (infinite) ---
export function useCaseAuditLog(caseId: string) {
  return useInfiniteQuery({
    queryKey: [...queryKeys.cases.detail(caseId), "audit"],
    queryFn: ({ pageParam }) =>
      apiClient.get(`/api/v1/cases/${caseId}/audit-logs`, { cursor: pageParam }),
    getNextPageParam: (last) => last.meta.nextCursor,
    initialPageParam: undefined as string | undefined,
  })
}


# --- api-client.ts (envelope unwrap) ---
async function get<T>(path: string): Promise<T> {
  const res = await fetch(baseUrl + path, { headers: authHeaders() })
  if (!res.ok) throw await parseProblemJson(res)
  const envelope = await res.json()
  return envelope.data as T
}
```

---

## Invariants

| # | Rule |
|---|------|
| 1 | Keys from `query-keys.ts` factory — no string literals in components |
| 2 | Unwrap `{ data, meta }` in client — hooks return domain types |
| 3 | Parse RFC 7807 into typed `ApiError` |
| 4 | Don't retry 404 |
| 5 | Mutations invalidate related lists + set detail cache |
| 6 | No server data in Zustand |
| 7 | `enabled` guard when id param may be empty |

---

## Anti-Patterns

- Duplicate query keys across hooks
- Raw fetch in hook without api-client
- Optimistic update without rollback on error
- Caching sensitive data with long staleTime + persistence

---

## Checklist

- [ ] Query key in centralized factory
- [ ] api-client handles auth header refresh
- [ ] Error type includes status, title, detail, validation errors
- [ ] Mutation invalidation scope correct
- [ ] 404 not retried
- [ ] Hook exported with typed return
- [ ] Vitest with MSW mock
