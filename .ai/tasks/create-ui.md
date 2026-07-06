# Task: Create UI Component / Page

**LexFlow AI** — AI prompt template for Next.js frontend work.

---

## Prompt (Copy-Paste Ready)

```
You are implementing a new UI component or page for LexFlow AI, an enterprise AI automation platform for law firms.

## Feature
{{feature_name}}

## UI Specification
- Route: {{route_path}}
- Component type: {{component_type}} (page | layout | component | hook)
- User persona: {{user_persona}}
- Ticket: {{ticket_id}}

## Context to Load
Read these before writing any code:

1. `.ai/memory/` — project memory and recent decisions
2. `.ai/rules/` — AI coding rules for this repo
3. `docs/12-ui/design-system.md` — Tailwind, ShadCN, legal enterprise UI
4. `docs/12-ui/page-architecture.md` — Next.js App Router structure
5. `docs/12-ui/state-management.md` — Zustand vs React Query
6. `docs/12-ui/accessibility.md` — WCAG 2.1 AA requirements
7. `docs/04-api/endpoints-{{api_resource}}.md` — API contract for data fetching
8. `docs/08-security/matter-walls.md` — UI must not leak unauthorized case data
9. `docs/12-ui/real-time-updates.md` — if SSE/notifications involved
10. Existing code: `apps/web/src/`, `packages/ui/`, `packages/shared/`

## Constraints
- Server Components by default — Client Components (`"use client"`) only when interactivity required
- BFF routes in `apps/web/src/app/api/` are THIN — proxy to FastAPI, no business logic
- All authorization enforced server-side — UI hides unauthorized UI but never substitutes for API auth
- Use typed API client from `packages/sdk/` or `apps/web/src/lib/api-client.ts`
- React Query for server state; Zustand for client-only UI state
- ShadCN primitives from `apps/web/src/components/ui/` — do not reinvent
- WCAG 2.1 AA: keyboard nav, focus management, ARIA labels, color contrast
- No PII in client-side logs or error boundaries
- TypeScript strict mode; ESLint + Prettier compliant
- Matter wall UX: unauthorized users see empty state or generic error — never case details

## Step-by-Step Instructions
1. **API contract** — Confirm endpoint exists or coordinate with backend (create-api.md)
2. **Route structure** — Place page under correct App Router segment (`(auth)/`, `(dashboard)/`, etc.)
3. **Layout** — Use existing dashboard shell; add breadcrumbs if nested under case hub
4. **Data fetching** — Server Component fetch or React Query hook with proper error/loading states
5. **Components** — Build from ShadCN primitives; extract reusable parts to `components/{{domain}}/`
6. **Forms** — Use react-hook-form + zod validation matching API request schema
7. **Authorization UX** — Handle 404 from API gracefully; no case ID leakage in URLs or network
8. **Accessibility** — Test keyboard flow, screen reader labels, focus traps in modals
9. **Tests** — Plan Vitest component tests and Playwright E2E if critical journey
10. **Docs** — Update `docs/12-ui/` if new pattern introduced

## Output Format
Deliver in this order:

### 1. Design Summary
- Route and file structure
- Server vs Client Component split
- Data flow diagram (fetch → render → mutate)
- Files to create or modify

### 2. Implementation
- Complete code for each file
- Tailwind classes following design system tokens

### 3. Component API
- Props interface with JSDoc
- Usage example

### 4. Test Plan
- Vitest test cases (render, interaction, error states)
- Playwright journey reference (if applicable)

### 5. Accessibility Notes
- ARIA attributes, keyboard shortcuts, focus order

## Verification Checklist
- [ ] Server Component used unless interactivity required
- [ ] No business logic in BFF routes or components
- [ ] API client typed; errors handled with user-friendly messages
- [ ] Loading, empty, and error states implemented
- [ ] Matter wall: 404 handled without leaking case existence
- [ ] Forms validated client-side AND rely on server validation
- [ ] WCAG 2.1 AA: contrast, labels, keyboard navigation
- [ ] No `"use client"` on data-fetching-only components
- [ ] ShadCN components reused (not duplicated)
- [ ] TypeScript strict — no `any` without justification
- [ ] Responsive layout tested at mobile/tablet/desktop breakpoints
```

---

## Example Variables

| Variable | Example Value |
|----------|---------------|
| `{{feature_name}}` | Case deadline list with create/edit modal |
| `{{route_path}}` | /cases/[caseId]/deadlines |
| `{{component_type}}` | page |
| `{{user_persona}}` | Associate Attorney |
| `{{api_resource}}` | cases |
| `{{ticket_id}}` | LEX-143 |
