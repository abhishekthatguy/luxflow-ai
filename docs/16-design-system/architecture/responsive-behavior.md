# Responsive Behavior — Breakpoints, Layouts & Mobile Legal Workflows

**LexFlow AI** — Enterprise Legal SaaS Responsive Design Architecture  
**Version:** 1.0  
**Status:** Draft — Pre-Implementation  
**Last Updated:** 2026-07-06

---

## Purpose

Define **responsive behavior** across LexFlow AI surfaces — breakpoint system, layout adaptations, collapsible sidebar patterns, and mobile/tablet use cases for legal professionals and client portal users. Attorneys and paralegals increasingly access case status from court, client sites, and travel — responsive design is operational, not cosmetic.

Cross-reference: [../../12-ui/design-system.md](../../12-ui/design-system.md), [navigation-structure.md](./navigation-structure.md), [screen-hierarchy.md](./screen-hierarchy.md), [../../12-ui/client-portal.md](../../12-ui/client-portal.md).

---

## Scope

| In Scope | Out of Scope |
|----------|--------------|
| Breakpoint definitions and layout rules | Native mobile app (Phase 4+) |
| Collapsible sidebar behavior | Print stylesheets |
| Tablet and mobile lawyer use cases | Device-specific bug fixes |
| Portal mobile-first patterns | PWA offline mode |
| Touch target requirements | Implementation CSS |

---

## Breakpoint System

LexFlow uses Tailwind CSS default breakpoints with legal-enterprise layout conventions:

| Token | Min Width | Target Devices | Primary Use Case |
|-------|-----------|----------------|------------------|
| `(default)` | 0px | Mobile phones | Portal, quick case checks |
| `sm` | 640px | Large phones, small tablets | Portal upload, notifications |
| `md` | 768px | Tablets (iPad) | Court-side review, depositions |
| `lg` | 1024px | Laptops, small desktops | Primary firm work — sidebar visible |
| `xl` | 1280px | Desktop monitors | Full case workspace + right panel |
| `2xl` | 1536px | Ultra-wide | Max content width 1400px centered |

### Breakpoint Flow

```mermaid
flowchart LR
    MOBILE["Mobile<br/>&lt; 768px"] --> TABLET["Tablet<br/>768–1023px"]
    TABLET --> DESKTOP["Desktop<br/>1024–1279px"]
    DESKTOP --> WIDE["Wide<br/>≥ 1280px"]

    MOBILE --> M1["Sheet nav · stacked content"]
    TABLET --> T1["Collapsible sidebar · scrollable tabs"]
    DESKTOP --> D1["Fixed sidebar 240px"]
    WIDE --> W1["Sidebar + content + optional panel"]
```

---

## Layout Adaptation Matrix

| Component | Mobile (<768px) | Tablet (768–1023px) | Desktop (≥1024px) |
|-----------|-----------------|---------------------|-------------------|
| Primary sidebar | Hidden — hamburger sheet | Collapsed icon rail OR overlay | Fixed 240px |
| Top nav | Full width — compact search | Full width | Full width |
| Case tabs | Dropdown selector | Horizontal scroll | Full tab bar |
| Data tables | Card list view | Horizontal scroll table | Full table |
| Right context panel | Bottom sheet / hidden | Collapsible drawer | Fixed 320px |
| Breadcrumbs | Truncated — last segment | Collapsed middle | Full trail |
| Command palette | Full screen | Centered modal 640px | Centered modal 640px |
| Portal nav | Hamburger menu | Horizontal links | Horizontal links |

---

## Firm Dashboard — Responsive Layouts

### Desktop (≥1024px) — Standard App Shell

```mermaid
block-beta
    columns 12
    block:header:12
        Logo["LexFlow"]:1
        Search["Search ⌘K"]:5
        space:3
        Notif["🔔"]:1
        User["User ▾"]:2
    end
    block:body:12
        columns 12
        block:sidebar:2
            Nav["Sidebar<br/>240px<br/>Full labels"]
        end
        block:content:10
            Main["Main Content Area"]
        end
    end
```

### Tablet (768–1023px) — Collapsible Sidebar

```mermaid
block-beta
    columns 12
    block:thead:12
        Menu["☰"]:1
        Logo["LexFlow"]:2
        Search["🔍"]:6
        Notif["🔔"]:1
        User["▾"]:2
    end
    block:tbody:12
        columns 12
        block:icons:1
            I1["📁"]
            I2["📄"]
            I3["🛡"]
        end
        block:tmain:11
            Content["Expanded Content<br/>Tabs scroll horizontally"]
        end
    end
```

**Tablet sidebar modes:**

| Mode | Width | Trigger | Behavior |
|------|-------|---------|----------|
| Icon rail | 56px | Default on tablet | Icons only + tooltip on hover |
| Expanded overlay | 240px | Click hamburger or icon | Overlays content — dismiss on navigate |
| Hidden | 0px | User preference | Full-width content |

### Mobile (<768px) — Sheet Navigation

```mermaid
block-beta
    columns 12
    block:mheader:12
        Menu["☰"]:2
        Title["Cases"]:6
        Notif["🔔"]:2
        User["▾"]:2
    end
    block:mbody:12
        MobileContent["Single column content<br/>Cards replace tables<br/>FAB for primary action"]
    end
```

**Mobile firm app priorities (Phase 1):**
- Case list with status badges
- Case overview — key metrics only
- Notifications and approvals queue
- Document list (no inline preview — link to detail)
- **Deferred on mobile:** Audit log, admin, workflow templates, AI review editing

---

## Collapsible Sidebar — Behavior Specification

```mermaid
stateDiagram-v2
    [*] --> Expanded: Desktop default (≥1024px)
    [*] --> Collapsed: Tablet default (768–1023px)
    [*] --> Hidden: Mobile default (<768px)

    Expanded --> Collapsed: User toggle OR viewport shrink
    Collapsed --> Expanded: User toggle OR viewport grow
    Hidden --> SheetOpen: Hamburger tap
    SheetOpen --> Hidden: Navigate OR dismiss overlay

    note right of Expanded
        240px width
        Icons + labels
        Persist preference in localStorage
    end note

    note right of Collapsed
        56px icon rail
        Tooltip on hover/focus
    end note

    note right of SheetOpen
        280px sheet from left
        Focus trap
        Escape to close
    end note
```

### Sidebar Collapse Interaction

```mermaid
sequenceDiagram
    participant U as User
    participant UI as AppShell
    participant STORE as User Preferences

    U->>UI: Click collapse toggle
    UI->>STORE: Save sidebarState: collapsed
    UI->>UI: Animate sidebar 240px → 56px
    UI->>UI: Expand main content area
    Note over UI: Icons remain visible<br/>Labels hidden<br/>Tooltips on focus

    U->>UI: Resize window to < 1024px
    UI->>UI: Auto-collapse to icon rail
    U->>UI: Resize window to < 768px
    UI->>UI: Hide sidebar — show hamburger
```

### Sidebar Wireframe — Three States

```mermaid
block-beta
    columns 3
    block:expanded:1
        columns 1
        E1["📁 Cases"]
        E2["👥 Clients"]
        E3["📄 Documents"]
        E4["◀ Collapse"]
    end
    block:collapsed:1
        columns 1
        C1["📁"]
        C2["👥"]
        C3["📄"]
        C4["▶"]
    end
    block:mobile:1
        columns 1
        M0["☰ Menu"]
        M1[" "]
        M2["Content"]
        M3["full width"]
    end
```

---

## Case Workspace — Responsive Adaptations

### Case Tabs by Viewport

```mermaid
flowchart TB
    subgraph Desktop["Desktop ≥1024px"]
        DT["Overview | Documents | Timeline | Tasks | Workflows | AI | Team | Settings"]
    end

    subgraph Tablet["Tablet 768–1023px"]
        TT["Overview | Documents | Timeline | Tasks | +4 more →"]
    end

    subgraph Mobile["Mobile <768px"]
        MT["Current: Documents ▾<br/>Dropdown lists all tabs"]
    end

    Desktop --> Tablet --> Mobile
```

### Case Overview — Content Reflow

| Element | Desktop | Tablet | Mobile |
|---------|---------|--------|--------|
| Case header | Single row — title + status + actions | Wrapped — actions in menu | Stacked — title, status, actions menu |
| Metrics cards | 4-column grid | 2×2 grid | Single column stack |
| Upcoming deadlines | Right rail panel | Below metrics | Below metrics |
| Quick actions | Button row | Button row — scroll | FAB + overflow menu |
| Timeline preview | Side panel | Collapsed accordion | Link to full timeline tab |

### Case Workspace Wireframe — Mobile

```mermaid
block-beta
    columns 4
    block:mcaseheader:4
        Back["← Cases"]
        CaseName["Smith v. Acme"]
        Status["Active"]
    end
    block:mtabselect:4
        TabDrop["Tab: Overview ▾"]
    end
    block:mmetrics:4
        M1["12 Tasks"]
        M2["34 Docs"]
        M3["2 Deadlines"]
    end
    block:mlist:4
        Item1["Next: Response due Jul 18"]
        Item2["AI summary pending approval"]
        Item3["Discovery workflow running"]
    end
    block:mfab:4
        FAB["+ Quick Action"]
    end
```

---

## Data Tables — Responsive Patterns

```mermaid
flowchart TD
    TABLE[Data Table Component]
    TABLE --> DESKTOP_T["Desktop: Full DataTable<br/>Sort · Filter · Pagination"]
    TABLE --> TABLET_T["Tablet: Horizontal scroll<br/>Sticky first column"]
    TABLE --> MOBILE_T["Mobile: Card list<br/>Key fields only · tap to expand"]

    MOBILE_T --> CARD["Card: Title · Status · Date · Chevron"]
    CARD --> DETAIL["Full detail on navigate"]
```

### Case List — Mobile Card Layout

```mermaid
block-beta
    columns 4
    block:card1:4
        columns 4
        T1["Smith v. Acme Corp"]:3
        S1["Active"]:1
        M1["#2026-00142 · Litigation"]:2
        D1["2 deadlines"]:2
    end
    block:card2:4
        columns 4
        T2["Johnson Estate"]:3
        S2["Intake"]:1
        M2["#2026-00138 · Estate"]:2
        D2["No deadlines"]:2
    end
```

---

## Client Portal — Mobile-First

The client portal is **mobile-first by design** — clients frequently access from phones:

```mermaid
flowchart LR
    subgraph Priority
        P1["1. My Matters list"]
        P2["2. Document upload"]
        P3["3. Messages / requests"]
        P4["4. Case status view"]
    end

    P1 --> P2 --> P3 --> P4
```

### Portal Responsive Rules

| Rule | Value | Rationale |
|------|-------|-----------|
| Base font size | 16px (all viewports) | Readability for external users |
| Touch target minimum | 44×44px | WCAG / Apple HIG |
| Upload drop zone | Full width on mobile | Primary mobile action |
| Navigation | Hamburger below `md` | Maximize content area |
| Case cards | Full width stack | Thumb-friendly scrolling |

### Portal Wireframe — Mobile

```mermaid
block-beta
    columns 4
    block:pheader:4
        Ham["☰"]:1
        Firm["Acme Law"]:2
        Out["Sign Out"]:1
    end
    block:ptitle:4
        H1["My Matters"]
    end
    block:pcard:4
        CardTitle["Your Matter with Acme Corp"]
        CardStatus["In Progress"]
        CardAction["View Details →"]
    end
    block:pupload:4
        UploadBtn["Upload Documents"]
    end
```

### Portal Wireframe — Desktop

```mermaid
block-beta
    columns 12
    block:pdheader:12
        FirmLogo["Acme Law Firm Portal"]:4
        PNav["My Matters · Messages · Profile · Help"]:6
        SignOut["Sign Out"]:2
    end
    block:pdcontent:12
        columns 12
        block:pdcards:8
            CardRow["Case cards — 2 column grid"]
        end
        block:pdside:4
            SideInfo["Need help?<br/>Contact Jane Attorney<br/>jane@firm.com"]
        end
    end
```

---

## Mobile Lawyer Use Cases

Legal professionals use mobile/tablet in specific contexts — design priorities reflect actual workflows:

```mermaid
quadrantChart
    title Mobile Use Case Priority
    x-axis Low Frequency --> High Frequency
    y-axis Low Priority --> High Priority
    quadrant-1 Optimize First
    quadrant-2 Monitor
    quadrant-3 Defer
    quadrant-4 Desktop Only

    Check case status: [0.85, 0.90]
    Approve AI summary: [0.70, 0.85]
    Review notifications: [0.80, 0.80]
    Upload photo of doc: [0.55, 0.75]
    Full document review: [0.30, 0.40]
    Audit log search: [0.10, 0.20]
    Workflow template edit: [0.05, 0.15]
    Admin user mgmt: [0.05, 0.10]
```

### Use Case Detail

| Scenario | Device | Priority Screens | Notes |
|----------|--------|------------------|-------|
| **Court — check deadline** | Phone | Case overview, tasks | Read-only; fast load |
| **Client dinner — approval** | Phone | Approvals inbox, AI review | Read + approve/reject |
| **Deposition — photo upload** | Tablet | Document upload | Camera integration Phase 2 |
| **Travel — notification triage** | Phone | Notifications list | Deep link to context |
| **Conference room — case review** | Tablet | Case overview, timeline | Landscape orientation |
| **Full document redline** | Desktop | Document detail | **Not mobile target** |
| **Audit investigation** | Desktop | Audit explorer | **Not mobile target** |

---

## Orientation Behavior

| Surface | Portrait | Landscape |
|---------|----------|-----------|
| Firm case list | Card stack | Optional 2-column cards |
| Document preview | Full width | Side-by-side metadata + preview (tablet+) |
| Portal upload | Full width drop zone | Same — centered max 600px |
| AI review | Single column draft | Draft + source panel (tablet+) |

```mermaid
flowchart LR
    ORIENT{Orientation change}
    ORIENT -->|Portrait| P["Stack panels vertically"]
    ORIENT -->|Landscape| L["Side-by-side where space allows"]
    P --> PRESERVE["Preserve scroll position<br/>Preserve form state"]
    L --> PRESERVE
```

---

## Touch & Interaction Guidelines

| Pattern | Desktop | Touch Device |
|---------|---------|--------------|
| Hover prefetch | Sidebar links prefetch on hover | Prefetch on touch start |
| Tooltips | On hover | On long-press OR always visible label |
| Context menu | Right-click | Long-press OR action sheet |
| Drag-drop upload | Supported | Supported + explicit file picker button |
| Table row actions | Hover reveal | Always visible OR swipe actions (Phase 2) |
| Sidebar toggle | Click chevron | Tap hamburger |

---

## Performance Budgets by Viewport

| Viewport | Initial JS Target | Skeleton First Paint | Notes |
|----------|-------------------|----------------------|-------|
| Mobile | < 150KB gzip | < 1.5s | Defer non-critical panels |
| Tablet | < 180KB gzip | < 1.2s | Icon rail — no sidebar JS until expand |
| Desktop | < 200KB gzip | < 1.0s | Full shell — prefetch active case |

---

## Accessibility Across Breakpoints

Cross-reference: [../../12-ui/accessibility.md](../../12-ui/accessibility.md).

| Requirement | Mobile | Desktop |
|-------------|--------|---------|
| Focus trap in sheet nav | Required | N/A |
| Skip to main content | Required | Required |
| Pinch zoom | Never disabled | Never disabled |
| Minimum touch target | 44×44px | 32×32px (mouse precision) |
| Reduced motion | Respect `prefers-reduced-motion` | Same |

---

## Phase Roadmap

| Phase | Enhancement |
|-------|-------------|
| Phase 1 | Collapsible sidebar, mobile card lists, portal mobile-first |
| Phase 2 | Swipe actions on mobile tables; camera upload |
| Phase 2 | Offline indicator (no offline data) |
| Phase 3 | Dark mode — responsive tokens |
| Phase 4 | Dedicated mobile case workspace layout |
| Phase 4 | PWA install prompt for portal |

---

## Best Practices

1. **Mobile-first portal, desktop-first firm app** — Different primary devices per audience.
2. **Never hide critical actions on mobile** — Approvals and notifications remain accessible.
3. **Preserve state on resize** — Form inputs, scroll position, tab selection survive orientation change.
4. **Test at 320px width** — Minimum supported viewport.
5. **Sheet nav focus trap** — Keyboard and screen reader must work in mobile menu.
6. **Tables degrade gracefully** — Card list is not a truncated table — it's a purpose-built mobile view.
7. **Defer desktop-only surfaces** — Audit and admin redirect to "best on desktop" notice on mobile (optional link).

---

## Tradeoffs

| Decision | Benefit | Cost |
|----------|---------|------|
| Icon rail on tablet vs hidden | Faster nav for power users | Uses 56px horizontal space |
| Card list vs horizontal scroll table on mobile | Readable without zoom | Loses column scanability |
| Mobile AI review read-only vs full | Faster Phase 1 ship | Approve requires desktop for long edits |
| Portal mobile-first | Matches client behavior | Different patterns from firm app |
| localStorage sidebar preference | Persists user choice | SSR flash on first load |

---

## References

| Document | Path |
|----------|------|
| Design system | [../../12-ui/design-system.md](../../12-ui/design-system.md) |
| Navigation structure | [navigation-structure.md](./navigation-structure.md) |
| Screen hierarchy | [screen-hierarchy.md](./screen-hierarchy.md) |
| Client portal | [../../12-ui/client-portal.md](../../12-ui/client-portal.md) |
| Accessibility | [../../12-ui/accessibility.md](../../12-ui/accessibility.md) |
| UX guidelines | [ux-guidelines.md](./ux-guidelines.md) |
