# Screen Hierarchy — Complete Route & Screen Map

**LexFlow AI** — Enterprise Legal SaaS Screen Inventory  
**Version:** 1.0  
**Status:** Draft — Pre-Implementation  
**Last Updated:** 2026-07-06

---

## Purpose

Provide the **complete screen map** for LexFlow AI — every major route, layout boundary, and screen relationship across the firm dashboard, authentication flows, and client portal. This document is the visual companion to [../../12-ui/page-architecture.md](../../12-ui/page-architecture.md).

Cross-reference: [information-architecture.md](./information-architecture.md), [navigation-structure.md](./navigation-structure.md), [../../01-product/user-personas.md](../../01-product/user-personas.md), [../../04-api/](../../04-api/).

---

## Scope

| In Scope | Out of Scope |
|----------|--------------|
| All major routes and screens | Component-level specs |
| Layout group boundaries | API implementation |
| Modal and intercepting routes (Phase 1) | E2E test definitions |
| Screen-to-API mapping summary | n8n workflow screens |

---

## Master Screen Tree

```mermaid
flowchart TB
    ROOT["LexFlow AI — apps/web"]

    ROOT --> AUTH["(auth)/ — Public"]
    ROOT --> DASH["(dashboard)/ — Firm Users"]
    ROOT --> PORTAL["(portal)/ — Client Users"]
    ROOT --> BFF["api/ — BFF Handlers"]
    ROOT --> GLOBAL["Global Boundaries<br/>not-found · error"]

    AUTH --> A1["/login"]
    AUTH --> A2["/reset-password"]
    AUTH --> A3["/accept-invite"]

    DASH --> D0["/ — Role redirect"]
    DASH --> CASES["/cases/*"]
    DASH --> CLIENTS["/clients/*"]
    DASH --> DOCS["/documents"]
    DASH --> WF["/workflows/*"]
    DASH --> APPROVALS["/approvals"]
    DASH --> AI["/ai"]
    DASH --> AUDIT["/audit"]
    DASH --> REPORTS["/reports"]
    DASH --> ADMIN["/admin/*"]
    DASH --> SETTINGS["/settings/*"]

    PORTAL --> P0["/portal"]
    PORTAL --> PCASES["/portal/cases/*"]
    PORTAL --> PMSG["/portal/messages"]
    PORTAL --> PINTAKE["/portal/intake/*"]
    PORTAL --> PPROF["/portal/profile"]

    BFF --> B1["/api/auth/refresh"]
    BFF --> B2["/api/events/stream"]
```

---

## Route Group Screen Inventory

### `(auth)` — Authentication Screens

| Screen | Route | Layout | Primary API |
|--------|-------|--------|-------------|
| Login | `/login` | Auth card — centered | `POST /api/v1/auth/login` |
| Reset Password | `/reset-password` | Auth card | `POST /api/v1/auth/reset-password` |
| Accept Invite | `/accept-invite` | Auth card | `POST /api/v1/auth/accept-invite` |

```mermaid
flowchart LR
    LOGIN["Login"] --> DASH_HOME["Firm Dashboard"]
    LOGIN --> PORTAL_HOME["Client Portal"]
    INVITE["Accept Invite"] --> SETPASS["Set Password"]
    SETPASS --> DASH_HOME
    SETPASS --> PORTAL_HOME
    RESET["Reset Password"] --> LOGIN
```

---

### `(dashboard)` — Firm Application Screens

#### Top-Level Screens

| Screen | Route | Personas | API Dependencies |
|--------|-------|----------|------------------|
| Home redirect | `/` | All firm | Session role resolution |
| Case list | `/cases` | All assigned roles | `GET /cases` |
| Create case | `/cases/new` | Paralegal+ | `POST /cases` |
| Client list | `/clients` | Paralegal+ | `GET /clients` |
| Client detail | `/clients/[clientId]` | Paralegal+ | `GET /clients/{id}` |
| Firm documents | `/documents` | Attorney, Paralegal, Ops | `GET /documents` |
| Workflow executions | `/workflows` | Trigger roles | `GET /workflows/executions` |
| Workflow templates | `/workflows/templates` | Operations, SysAdmin | `GET /workflows/definitions` |
| Execution detail | `/workflows/executions/[id]` | Trigger roles | `GET /workflows/executions/{id}` |
| Approvals inbox | `/approvals` | Attorney+ | `GET /approvals` |
| AI dashboard | `/ai` | MP, Compliance | `GET /ai/usage` |
| Audit log | `/audit` | Compliance, MP | `GET /audit/logs` |
| Reports | `/reports` | MP, Operations | `GET /reports/*` |
| User settings | `/settings` | All | `GET /users/me` |
| User profile | `/settings/profile` | All | `PATCH /users/me` |

#### Admin Screens

| Screen | Route | Personas | API |
|--------|-------|----------|-----|
| Users | `/admin/users` | SysAdmin, ITAdmin | `GET /admin/users` |
| Roles | `/admin/roles` | SysAdmin | `GET /admin/roles` |
| Integrations | `/admin/integrations` | SysAdmin, ITAdmin | `GET /admin/integrations` |
| Firm config | `/admin/config` | SysAdmin | `GET /admin/config` |

---

### Case Workspace — Nested Screen Tree

```mermaid
flowchart TB
    CL["/cases — Case List"]
    CL --> NEW["/cases/new — Create Case"]
    CL --> CID["/cases/[caseId] — Redirect → overview"]

    CID --> OVER["/overview — Case Overview"]
    CID --> DOC["/documents — Document List"]
    CID --> DOCD["/documents/[documentId] — Document Detail"]
    CID --> TIME["/timeline — Event Timeline"]
    CID --> TASK["/tasks — Tasks & Deadlines"]
    CID --> WF["/workflows — Case Workflows"]
    CID --> AI["/ai — AI Job List"]
    CID --> AIJ["/ai/[jobId] — AI Job Detail / Review"]
    CID --> PART["/participants — Team Members"]
    CID --> SET["/settings — Case Settings"]

    style CL fill:#1E3A5F,color:#fff
    style CID fill:#2563EB,color:#fff
```

#### Case Screen Detail

| Screen | Route | Key UI Elements | API |
|--------|-------|-----------------|-----|
| Case overview | `/cases/[id]/overview` | Status, metrics, upcoming deadlines, quick actions | `GET /cases/{id}` |
| Document list | `/cases/[id]/documents` | Filterable table, upload, visibility badges | `GET /cases/{id}/documents` |
| Document detail | `/cases/[id]/documents/[docId]` | Preview, metadata, version history, share | `GET /cases/{id}/documents/{docId}` |
| Timeline | `/cases/[id]/timeline` | Infinite scroll event feed | `GET /cases/{id}/timeline` |
| Tasks | `/cases/[id]/tasks` | Task list, deadline calendar, hearings | `GET /tasks`, `/deadlines`, `/hearings` |
| Workflows | `/cases/[id]/workflows` | Trigger panel, execution history | `GET /cases/{id}/workflows` |
| AI list | `/cases/[id]/ai` | Job queue, status filters | `GET /cases/{id}/ai/jobs` |
| AI review | `/cases/[id]/ai/[jobId]` | Draft viewer, approve/reject, disclaimer | `GET /ai/jobs/{id}` |
| Participants | `/cases/[id]/participants` | Member list, add/remove | `GET /cases/{id}/participants` |
| Case settings | `/cases/[id]/settings` | Client visibility, display name | `PATCH /cases/{id}` |

---

### `(portal)` — Client Portal Screens

```mermaid
flowchart TB
    PH["/portal — My Matters"]
    PH --> PC["/portal/cases/[caseId] — Case Detail"]
    PC --> PU["/portal/cases/[caseId]/upload — Upload"]
    PH --> PM["/portal/messages — Requests Inbox"]
    PH --> PI["/portal/intake/[token] — Intake Form"]
    PH --> PP["/portal/profile — Profile"]

    style PH fill:#2563EB,color:#fff
```

| Screen | Route | Key Elements | API |
|--------|-------|--------------|-----|
| My Matters | `/portal` | Case cards, milestone badges | `GET /portal/cases` |
| Case detail | `/portal/cases/[id]` | Status, contact, shared docs, timeline | `GET /portal/cases/{id}` |
| Upload | `/portal/cases/[id]/upload` | Drag-drop, progress, confirm | Presigned upload flow |
| Messages | `/portal/messages` | Firm requests, respond action | `GET /portal/messages` |
| Intake | `/portal/intake/[token]` | Dynamic form from schema | `GET/POST /portal/intake/{token}` |
| Profile | `/portal/profile` | Name, password, notifications | `GET/PATCH /portal/profile` |

---

## Layout Hierarchy Diagram

```mermaid
flowchart TD
    RL["Root Layout<br/>fonts · providers · analytics"]
    
    RL --> AL["Auth Layout<br/>centered card"]
    RL --> DL["Dashboard Layout<br/>AppShell — sidebar + top nav"]
    RL --> PL["Portal Layout<br/>PortalShell — top nav only"]

    AL --> AP["Auth Pages"]

    DL --> DP["Dashboard Pages"]
    DL --> CL["Cases Layout<br/>list toolbar"]
    CL --> CIL["Case Layout<br/>header + tabs"]
    CIL --> CP["Case Tab Pages"]

    DL --> ADL["Admin Layout<br/>sub-nav"]
    ADL --> ADP["Admin Pages"]

    PL --> PP["Portal Pages"]
```

---

## Screen Relationship Map — Firm User Flow

```mermaid
flowchart TB
    subgraph Entry["Entry Points"]
        LOGIN["Login"]
        NOTIF["Notification deep link"]
        SEARCH["Global search result"]
        BOOKMARK["Bookmark / shared URL"]
    end

    subgraph Hub["Hub Screens"]
        CASELIST["Case List"]
        APPROVALS["Approvals Inbox"]
        AUDIT["Audit Log"]
    end

    subgraph CaseWS["Case Workspace"]
        OVERVIEW["Overview"]
        DOCUMENTS["Documents"]
        AI_REVIEW["AI Review"]
        TASKS["Tasks"]
        WF_CASE["Workflows"]
    end

    subgraph Admin["Administration"]
        USERS["Users"]
        CONFIG["Config"]
    end

    LOGIN --> CASELIST
    LOGIN --> AUDIT
    NOTIF --> AI_REVIEW
    SEARCH --> DOCUMENTS
    BOOKMARK --> OVERVIEW

    CASELIST --> OVERVIEW
    OVERVIEW --> DOCUMENTS
    OVERVIEW --> AI_REVIEW
    OVERVIEW --> TASKS
    DOCUMENTS --> AI_REVIEW
    APPROVALS --> AI_REVIEW
```

---

## Screen-to-Persona Matrix

```mermaid
flowchart LR
    subgraph Screens
        S1[Case List]
        S2[Create Case]
        S3[AI Review]
        S4[Approvals]
        S5[Audit]
        S6[Workflow Templates]
        S7[Reports]
        S8[Admin Users]
        S9[Portal Home]
    end

    subgraph Personas
        ATTY[Attorney]
        PARA[Paralegal]
        COMP[Compliance]
        OPS[Operations]
        MP[Managing Partner]
        SYS[System Admin]
        CLIENT[Client]
    end

    ATTY --> S1 & S3 & S4
    PARA --> S1 & S2
    COMP --> S5
    OPS --> S6
    MP --> S7
    SYS --> S8
    CLIENT --> S9
```

| Screen | Attorney | Associate | Paralegal | LA | MP | Ops | Compliance | SysAdmin | Client |
|--------|:--------:|:---------:|:---------:|:--:|:--:|:---:|:----------:|:--------:|:------:|
| Case list | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Portal |
| Create case | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | ✓ | |
| AI review | ✓ | view | view | | ✓ | | ✓ | ✓ | |
| Approvals decide | ✓ | | | | ✓ | | | ✓ | |
| Audit log | | | | | ✓ | | ✓ | ✓ | |
| WF templates | | | | | ✓ | ✓ | | ✓ | |
| Admin | | | | | | | | ✓ | |
| Portal | | | | | | | | | ✓ |

---

## Modal & Overlay Screens (Phase 1)

| Screen | Pattern | Route Fallback |
|--------|---------|----------------|
| Create case modal | Intercepting `@modal` | `/cases/new` full page |
| Document quick preview | Parallel `@modal` | Document detail page |
| Confirm destructive action | Dialog overlay | N/A — inline |
| Add participant | Dialog overlay | N/A — inline |
| Trigger workflow | Sheet overlay | N/A — inline |

```mermaid
flowchart LR
    LIST["Case List"] -->|Click New| MODAL["Create Case Modal"]
    MODAL -->|Submit success| DETAIL["Case Overview"]
    MODAL -->|Direct URL| FULL["/cases/new Full Page"]
```

---

## Error & Boundary Screens

| Screen | Trigger | Route Context |
|--------|---------|---------------|
| Global 404 | Unknown route | `not-found.tsx` |
| Case 404 | Matter wall / missing case | `cases/[caseId]/not-found.tsx` |
| Global error | Unhandled exception | `error.tsx` |
| Case error | Case fetch failure | `cases/[caseId]/error.tsx` |
| Loading skeleton | Route transition | `loading.tsx` per segment |

---

## App Shell Wireframe — Firm Dashboard

```mermaid
block-beta
    columns 12
    block:header:12
        columns 12
        Logo["LexFlow"]:2
        SearchBox["Search ⌘K"]:4
        space:2
        Bell["Notifications"]:1
        UserMenu["User ▾"]:1
    end
    block:body:12
        columns 12
        block:sidebar:2
            NavItem1["Cases"]
            NavItem2["Clients"]
            NavItem3["Documents"]
            NavItem4["Approvals"]
            NavItem5["Workflows"]
            space
            NavItem6["Settings"]
        end
        block:main:10
            block:breadcrumb:10
                Crumb["Cases › Smith v. Acme › Documents"]
            end
            block:page:10
                PageTitle["Documents"]
                ContentArea["Table · Filters · Actions"]
            end
        end
    end
```

---

## App Shell Wireframe — Client Portal

```mermaid
block-beta
    columns 12
    block:pheader:12
        FirmName["Acme Law Firm Portal"]:4
        PNav["My Matters · Messages · Profile · Help"]:6
        SignOut["Sign Out"]:2
    end
    block:pbody:12
        block:pcards:12
            Card1["Your Matter with Acme Corp<br/>Status: In Progress"]
            Card2["Estate Planning Matter<br/>Status: Review"]
        end
    end
```

---

## Case Workspace Wireframe

```mermaid
block-beta
    columns 12
    block:caseheader:12
        CaseTitle["Smith v. Acme Corp"]:6
        CaseMeta["Active · High · #2026-00142"]:4
        CaseActions["Actions ▾"]:2
    end
    block:tabs:12
        TabRow["Overview | Documents | Timeline | Tasks | Workflows | AI | Team | Settings"]
    end
    block:casebody:12
        columns 12
        block:maincontent:8
            TabContent["Primary Tab Content"]
        end
        block:rightrail:4
            SidePanel["Upcoming Deadlines<br/>Quick Actions<br/>Recent Activity"]
        end
    end
```

---

## Screen Count Summary

| Route Group | Screen Count | Nested Depth |
|-------------|:------------:|:------------:|
| `(auth)` | 3 | 1 |
| `(dashboard)` top-level | 14 | 1 |
| `(dashboard)` case workspace | 11 | 3 |
| `(dashboard)` admin | 4 | 2 |
| `(portal)` | 6 | 2 |
| BFF handlers | 2 | 1 |
| **Total major screens** | **~40** | **Max 4** |

---

## API Screen Mapping Summary

```mermaid
flowchart TB
    subgraph UI["Frontend Screens"]
        CASES_UI[Case Screens]
        DOC_UI[Document Screens]
        AI_UI[AI Screens]
        WF_UI[Workflow Screens]
        AUDIT_UI[Audit Screens]
        PORTAL_UI[Portal Screens]
    end

    subgraph API["FastAPI /api/v1"]
        CASES_API["/cases/*"]
        DOCS_API["/documents/*"]
        AI_API["/ai/*"]
        WF_API["/workflows/*"]
        AUDIT_API["/audit/*"]
        PORTAL_API["/portal/*"]
    end

    CASES_UI --> CASES_API
    DOC_UI --> DOCS_API
    AI_UI --> AI_API
    WF_UI --> WF_API
    AUDIT_UI --> AUDIT_API
    PORTAL_UI --> PORTAL_API
```

Cross-reference: [../../04-api/endpoints-cases.md](../../04-api/endpoints-cases.md), [../../04-api/endpoints-documents.md](../../04-api/endpoints-documents.md), [../../04-api/endpoints-ai.md](../../04-api/endpoints-ai.md), [../../04-api/endpoints-workflows.md](../../04-api/endpoints-workflows.md).

---

## Best Practices

1. **One screen per route** — Avoid multi-view SPA patterns without URL state.
2. **Colocate screen components** — Route-specific components under route directory.
3. **Consistent case header** — Shared layout across all case tabs.
4. **Portal screen isolation** — No imports from `(dashboard)/` into `(portal)/`.
5. **404 at case level** — Matter wall uses case-scoped `not-found.tsx`.
6. **Loading skeletons match layout** — Each major screen has shape-matched skeleton.

---

## References

| Document | Path |
|----------|------|
| Page architecture | [../../12-ui/page-architecture.md](../../12-ui/page-architecture.md) |
| Information architecture | [information-architecture.md](./information-architecture.md) |
| Navigation structure | [navigation-structure.md](./navigation-structure.md) |
| User journeys | [user-journeys.md](./user-journeys.md) |
| Client portal | [../../12-ui/client-portal.md](../../12-ui/client-portal.md) |
| API index | [../../04-api/README.md](../../04-api/README.md) |
