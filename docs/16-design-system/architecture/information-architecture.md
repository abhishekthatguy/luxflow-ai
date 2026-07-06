# Information Architecture — Case-Centric Content Hierarchy

**LexFlow AI** — Enterprise Legal SaaS Information Architecture  
**Version:** 1.0  
**Status:** Draft — Pre-Implementation  
**Last Updated:** 2026-07-06

---

## Purpose

Define the **content hierarchy**, **mental models**, and **information grouping** for LexFlow AI's firm dashboard and client portal. The Case (legal matter) is the central organizing unit — all documents, tasks, workflows, AI outputs, and audit events are scoped to a case. This document guides navigation design, screen layout, search scope, and matter wall UX implications.

**Invariant:** The UI reflects API responses only. Fields absent from a DTO are not rendered — never hidden client-side. Authorization is enforced in FastAPI; IA describes what authorized users see.

Cross-reference: [../../12-ui/page-architecture.md](../../12-ui/page-architecture.md), [../../01-product/user-personas.md](../../01-product/user-personas.md), [../../04-api/authorization-rbac.md](../../04-api/authorization-rbac.md), [../../08-security/matter-walls.md](../../08-security/matter-walls.md).

---

## Scope

| In Scope | Out of Scope |
|----------|--------------|
| Content taxonomy and hierarchy | Visual design tokens (see [../../12-ui/design-system.md](../../12-ui/design-system.md)) |
| Case-centric IA model | Component implementation |
| Firm vs portal information boundaries | Marketing website structure |
| Matter wall UX implications | Database schema |
| Search and discovery scope | n8n workflow internals |

---

## Core Mental Model

LexFlow AI organizes legal work around **Cases** — not clients, not documents, not users. Clients, documents, workflows, and AI jobs are **subordinate entities** accessed through or in relation to a case.

```mermaid
flowchart TB
    subgraph Platform["LexFlow AI — Information Domains"]
        CASE["Case (Central Aggregate)"]
        CLIENT[Client Record]
        DOC[Documents]
        TASK[Tasks & Deadlines]
        WF[Workflow Executions]
        AI[AI Jobs & Summaries]
        AUDIT[Audit Events]
        USER[Users & Participants]
    end

    CASE --> CLIENT
    CASE --> DOC
    CASE --> TASK
    CASE --> WF
    CASE --> AI
    CASE --> AUDIT
    CASE --> USER

    style CASE fill:#1E3A5F,color:#fff
```

### Why Case-Centric?

| Alternative | Why Not Primary |
|-------------|-----------------|
| Client-centric | One client may have many matters; conflates relationship with active work |
| Document-centric | Documents belong to matters; firm-wide doc search is secondary discovery |
| User-centric | Users span many cases; assignment is a filter, not a container |
| Workflow-centric | Workflows orchestrate case work; they do not own case data |

---

## Content Hierarchy — Firm Dashboard

### Level 0: Application Shell

The authenticated firm application presents four persistent zones:

```mermaid
block-beta
    columns 12
    block:header:12
        Logo["LexFlow"] space Search["Global Search ⌘K"] space Notif["Notifications"] space User["User Menu"]
    end
    block:body:12
        block:sidebar:2
            Nav["Primary Navigation<br/>Role-filtered"]
        end
        block:main:7
            Content["Page Content<br/>Lists · Forms · Detail Views"]
        end
        block:panel:3
            Context["Optional Context Panel<br/>AI Review · Activity"]
        end
    end
```

| Zone | Content Type | Update Frequency |
|------|--------------|------------------|
| Header | Global actions, search, notifications | Real-time (SSE) for notifications |
| Sidebar | Primary navigation — role-filtered | Session-stable |
| Main | Page-specific content | Per navigation |
| Context panel | Case-scoped auxiliary content | Per case selection |

### Level 1: Primary Domains

```mermaid
flowchart TB
    ROOT["Firm Application"]

    ROOT --> WORK["Work Domain<br/>Day-to-day case operations"]
    ROOT --> GOV["Governance Domain<br/>Compliance & oversight"]
    ROOT --> OPS["Operations Domain<br/>Automation & reporting"]
    ROOT --> ADMIN["Administration Domain<br/>Configuration"]
    ROOT --> PERSONAL["Personal Domain<br/>User preferences"]

    WORK --> CASES[Cases]
    WORK --> CLIENTS[Clients]
    WORK --> DOCS[Firm Documents]
    WORK --> APPROVALS[Approvals Inbox]

    GOV --> AUDIT[Audit Log]
    GOV --> AI_DASH[AI Usage Dashboard]

    OPS --> WF[Workflows]
    OPS --> REPORTS[Reports]

    ADMIN --> USERS[Users & Roles]
    ADMIN --> INTEGRATIONS[Integrations]
    ADMIN --> CONFIG[Firm Config]

    PERSONAL --> SETTINGS[Settings & Profile]
```

| Domain | Primary Personas | IA Principle |
|--------|------------------|--------------|
| Work | Attorney, Paralegal, Associate, Legal Assistant | Case-first; minimize clicks to active matter |
| Governance | Compliance Officer, Managing Partner | Firm-wide read; no mutation paths |
| Operations | Operations Team, Managing Partner | Template and metrics focus |
| Administration | System Admin, IT Admin | Separated from case data |
| Personal | All firm users | Decoupled from case context |

### Level 2: Case Workspace — Tab Hierarchy

Within a case, content is organized by **functional tabs** — each tab maps to API sub-resources:

```mermaid
flowchart LR
    CASE["Case: Smith v. Acme Corp"]

    CASE --> OVERVIEW["Overview<br/>Summary · Key metrics · Upcoming"]
    CASE --> DOCUMENTS["Documents<br/>Files · Versions · Visibility"]
    CASE --> TIMELINE["Timeline<br/>Chronological events"]
    CASE --> TASKS["Tasks<br/>Assignments · Deadlines · Hearings"]
    CASE --> WORKFLOWS["Workflows<br/>Executions · Triggers"]
    CASE --> AI["AI<br/>Jobs · Summaries · Approvals"]
    CASE --> PARTICIPANTS["Participants<br/>Matter wall membership"]
    CASE --> SETTINGS["Settings<br/>Case config · Client visibility"]

    style OVERVIEW fill:#EFF6FF
    style DOCUMENTS fill:#ECFDF5
    style AI fill:#F5F3FF
```

| Tab | API Root | Content Priority |
|-----|----------|------------------|
| Overview | `GET /cases/{id}` + aggregates | Status, lead, counts, next deadline |
| Documents | `GET /cases/{id}/documents` | Primary working surface for paralegals |
| Timeline | `GET /cases/{id}/timeline` | Audit-friendly event stream |
| Tasks | `GET /cases/{id}/tasks`, `/deadlines`, `/hearings` | Operational calendar |
| Workflows | `GET /cases/{id}/workflows` | Automation status |
| AI | `GET /cases/{id}/ai/jobs` | Human-in-the-loop review |
| Participants | `GET /cases/{id}/participants` | Matter wall management |
| Settings | `PATCH /cases/{id}` + client visibility | Lead attorney only |

Tab visibility is driven by **capabilities** returned in `GET /api/v1/cases/{id}` — not computed from role alone.

---

## Content Hierarchy — Client Portal

The portal uses a **flat, client-scoped** hierarchy — maximum three levels deep:

```mermaid
flowchart TB
    PORTAL["Client Portal"]

    PORTAL --> HOME["My Matters<br/>Case list"]
    PORTAL --> MESSAGES["Messages<br/>Firm requests"]
    PORTAL --> PROFILE["Profile<br/>Account settings"]

    HOME --> CASE_DETAIL["Case Detail<br/>Milestone · Documents · Timeline"]
    CASE_DETAIL --> UPLOAD["Upload Documents"]

    style PORTAL fill:#2563EB,color:#fff
```

| Portal Level | Firm Equivalent | Deliberately Omitted |
|--------------|-----------------|-------------------|
| My Matters | Cases list (filtered) | Internal case numbers, other clients |
| Case Detail | Case overview + documents | AI, workflows, internal notes, participants |
| Upload | Document upload | Version history, privilege labels |
| Messages | N/A (firm-initiated requests) | Internal task assignments |

Cross-reference: [../../12-ui/client-portal.md](../../12-ui/client-portal.md).

---

## Entity Relationship — Information Model

```mermaid
erDiagram
    CASE ||--o{ DOCUMENT : contains
    CASE ||--o{ TASK : contains
    CASE ||--o{ DEADLINE : contains
    CASE ||--o{ HEARING : contains
    CASE ||--o{ WORKFLOW_EXECUTION : triggers
    CASE ||--o{ AI_JOB : requests
    CASE ||--o{ TIMELINE_EVENT : generates
    CASE ||--o{ PARTICIPANT : assigns
    CASE }o--|| CLIENT : "belongs to"
    CASE ||--o{ NOTE : "internal only"

    DOCUMENT {
        uuid id
        string filename
        enum visibility
        uuid caseId
    }

    AI_JOB {
        uuid id
        enum status
        enum approvalStatus
        uuid caseId
    }

    PARTICIPANT {
        uuid userId
        enum role
        uuid caseId
    }
```

### Visibility Taxonomy (Documents & Notes)

| Level | Firm UI | Portal UI | API Field |
|-------|---------|-----------|-----------|
| Internal | Default — no badge | **Not returned** | `visibility: internal` |
| Privileged | Lock icon + left border | **Not returned** | `visibility: privileged` |
| Work product | Muted badge | **Not returned** | `visibility: work_product` |
| Client shared | Green badge | Visible in document list | `visibility: client_shared` |
| Client uploaded | "Client upload" badge | Own uploads visible | `visibility: client_uploaded` |

---

## Matter Wall UX Implications

Matter walls enforce ethical boundaries at the API layer. IA must **never leak information** about cases the user cannot access.

### MW-004: Uniform 404 Response

When a user requests a case they are not authorized to view:

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Frontend
    participant API as FastAPI

    U->>UI: Navigate to /cases/{blockedCaseId}
    UI->>API: GET /api/v1/cases/{blockedCaseId}
    API-->>UI: 404 Not Found
    UI->>UI: Render not-found.tsx
    Note over UI: Same message for<br/>nonexistent AND blocked cases
    UI-->>U: "This case could not be found<br/>or you may not have access."
```

### IA Rules for Matter Walls

| Scenario | UI Behavior | Rationale |
|----------|-------------|-----------|
| Case not in list | **Never shown** — API filters list | No enumeration via list gaps |
| Direct URL to blocked case | Generic 404 page | MW-004 — no "access denied" |
| Search result for blocked case | **Not returned** in results | Server-side filter |
| Breadcrumb to removed case | 404 at case level | No partial render |
| Notification link to blocked case | 404 on follow | No toast revealing existence |
| Recently viewed (local) | Remove on 404 | Prevent stale links |

### Firm-Wide Read Exception

`ManagingPartner` and `ComplianceOfficer` with `case:read:firm` see cases they are not assigned to — but **ethical wall overrides** may still block specific cases:

```mermaid
flowchart TD
    REQ[User requests case]
    RBAC{Has case:read permission?}
    FIRM{Has case:read:firm?}
    PART{Is participant?}
    WALL{Ethical wall block?}

    REQ --> RBAC
    RBAC -->|No| FORBIDDEN[403 Forbidden]
    RBAC -->|Yes| PART
    PART -->|Yes| WALL
    PART -->|No| FIRM
    FIRM -->|No| NOTFOUND[404 Not Found]
    FIRM -->|Yes| WALL
    WALL -->|Blocked| NOTFOUND
    WALL -->|Clear| ALLOW[200 OK — Read-only or full per role]
```

Compliance Officer IA note: firm-wide read surfaces appear in **Audit** and **Reports** — not mixed into personal case lists without explicit filter.

---

## Content Grouping by Persona

```mermaid
flowchart TB
    subgraph Attorney["Attorney — Primary Surfaces"]
        A1[Cases → Active matter]
        A2[Approvals inbox]
        A3[Case AI tab]
        A4[Documents review]
    end

    subgraph Paralegal["Paralegal — Primary Surfaces"]
        P1[Cases → Intake queue]
        P2[Case Documents tab]
        P3[Case Tasks tab]
        P4[Workflow triggers]
    end

    subgraph ManagingPartner["Managing Partner — Primary Surfaces"]
        MP1[Reports dashboard]
        MP2[Firm case metrics]
        MP3[AI usage dashboard]
    end

    subgraph Compliance["Compliance Officer — Primary Surfaces"]
        C1[Audit log explorer]
        C2[AI prompt history]
        C3[Firm-wide case search]
    end

    subgraph Client["Client — Primary Surfaces"]
        CL1[My Matters]
        CL2[Upload documents]
        CL3[Messages / requests]
    end
```

Cross-reference: [../../01-product/user-personas.md](../../01-product/user-personas.md).

---

## Search & Discovery Architecture

### Search Scopes

```mermaid
flowchart LR
    SEARCH["Global Search ⌘K"]

    SEARCH --> CASES_S["Cases<br/>title · caseNumber"]
    SEARCH --> DOCS_S["Documents<br/>filename · metadata"]
    SEARCH --> CLIENTS_S["Clients<br/>name · email"]
    SEARCH --> TASKS_S["Tasks<br/>title · assignee"]

    CASES_S --> MW[Matter wall filter]
    DOCS_S --> MW
    TASKS_S --> MW
```

| Scope | API Endpoint | Matter Wall |
|-------|--------------|-------------|
| Cases | `GET /cases?search=` | Applied — only assigned (+ firm read) |
| Documents | `GET /documents?search=` | Applied — case-scoped |
| Clients | `GET /clients?search=` | Role-gated — not all roles |
| Tasks | `GET /tasks?search=` | Applied — assigned cases only |

Search results **never include** blocked case titles, document names, or metadata snippets from walled matters.

### Discovery Patterns

| Pattern | Location | Content |
|---------|----------|---------|
| **Assigned cases** | `/cases` default view | User's active matters |
| **Approvals queue** | `/approvals` | Pending AI + workflow approvals |
| **Upcoming deadlines** | Case overview + dashboard widget | Cross-case deadline aggregation |
| **Recent activity** | Case timeline | Per-case event stream |
| **Firm-wide audit** | `/audit` | Compliance search only |

---

## Labeling & Terminology

Consistent terminology reduces cognitive load across personas:

| Concept | Firm UI Label | Portal UI Label | Avoid |
|---------|---------------|-----------------|-------|
| Case | Case / Matter | Your Matter | Ticket, Issue, Project |
| Client | Client | — (implicit) | Customer |
| AI output | AI Draft / AI Summary | *(hidden)* | Generated text (unlabeled) |
| Workflow | Workflow | *(hidden — use Milestone)* | Automation, n8n |
| Deadline | Deadline | Important Date | Due date (ambiguous) |
| Participant | Team Member | Your Contact | User |
| Privileged doc | Privileged | *(hidden)* | Confidential (vague) |

---

## Content Density by Surface

```mermaid
quadrantChart
    title Information Density vs Interaction Frequency
    x-axis Low Frequency --> High Frequency
    y-axis Low Density --> High Density
    quadrant-1 Power User Tools
    quadrant-2 Daily Workhorse
    quadrant-3 Occasional Admin
    quadrant-4 Reference & Oversight

    Case Documents: [0.85, 0.90]
    Case Overview: [0.75, 0.55]
    Approvals Inbox: [0.70, 0.65]
    Audit Log: [0.25, 0.85]
    Client Portal: [0.60, 0.20]
    Admin Users: [0.15, 0.50]
    Reports: [0.20, 0.70]
```

| Surface | Density Mode | Rationale |
|---------|--------------|-----------|
| Firm dashboard tables | Compact-capable | Attorneys prefer dense data |
| Client portal | Spacious (fixed) | External users, mobile-first |
| Audit log | Compact (default) | Compliance needs scanability |
| AI review panel | Comfortable | Long-form reading |

---

## IA Wireframe — Case Detail Information Zones

```mermaid
block-beta
    columns 12
    block:caseHeader:12
        Title["Smith v. Acme Corp · #2026-00142"] space Status["Active"] space Priority["High"]
    end
    block:meta:12
        Lead["Lead: Jane Attorney"] space Client["Client: John Smith"] space Opened["Opened: Jan 15, 2026"]
    end
    block:tabs:12
        TabNav["Overview | Documents | Timeline | Tasks | Workflows | AI | Participants | Settings"]
    end
    block:tabContent:12
        block:primary:8
            MainTab["Tab Content Area<br/>Lists · Detail · Forms"]
        end
        block:sidebar2:4
            QuickInfo["Upcoming Deadlines<br/>Recent Activity<br/>Quick Actions"]
        end
    end
```

---

## Best Practices

1. **Case as URL anchor** — Deep links always include `caseId`; shareable within authorized team.
2. **API-driven tab visibility** — Never show empty tabs; omit tabs user cannot access.
3. **No phantom content** — Do not render placeholders for walled data ("Document hidden").
4. **Separate portal IA** — Client portal is not a "lite" dashboard; it is a distinct product surface.
5. **Governance isolation** — Audit and compliance surfaces do not embed in case tabs.
6. **Consistent 404 copy** — Matter wall denials use identical messaging everywhere.
7. **Search respects walls** — Global search is a discovery tool, not an enumeration vector.

---

## Tradeoffs

| Decision | Benefit | Cost |
|----------|---------|------|
| Case-centric over client-centric | Matches legal mental model | Client history requires navigation |
| Tab-based case workspace | Deep linking per concern | More layout complexity |
| Capabilities from API vs role UI | Accurate per-case permissions | Extra API field on case DTO |
| 404 for walled cases | Security (MW-004) | User confusion — mitigate with copy |
| Separate portal hierarchy | Clear external boundary | Duplicate some patterns (upload) |

---

## References

| Document | Path |
|----------|------|
| Page architecture | [../../12-ui/page-architecture.md](../../12-ui/page-architecture.md) |
| User personas | [../../01-product/user-personas.md](../../01-product/user-personas.md) |
| Authorization RBAC | [../../04-api/authorization-rbac.md](../../04-api/authorization-rbac.md) |
| Case endpoints | [../../04-api/endpoints-cases.md](../../04-api/endpoints-cases.md) |
| Client portal | [../../12-ui/client-portal.md](../../12-ui/client-portal.md) |
| Matter walls | [../../08-security/matter-walls.md](../../08-security/matter-walls.md) |
| Navigation structure | [navigation-structure.md](./navigation-structure.md) |
| Screen hierarchy | [screen-hierarchy.md](./screen-hierarchy.md) |
