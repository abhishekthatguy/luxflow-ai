# Notifications — Toast, In-App, Bell & Teams Integration

**LexFlow AI** — Notification Interaction Specifications  
**Version:** 1.0  
**Status:** Draft — Pre-Implementation  
**Last Updated:** 2026-07-06

---

## Purpose

Define **notification interaction patterns** for LexFlow — transient toasts, persistent in-app notifications, the top-nav bell feed, and Microsoft Teams integration status indicators. Notifications keep attorneys and paralegals informed of workflow completion, approval requests, deadlines, and async AI job results without disrupting legal work.

**Reference aesthetic:** GitHub notification bell, Linear's subtle toasts, Stripe's success/error feedback, Fluent UI message bar for persistent alerts.

---

## Anatomy

### Toast Notification Wireframe

```mermaid
flowchart LR
    subgraph Toast["Toast — bottom-right stack · max 3 visible"]
        ICON["Status icon — 16px"]
        CONTENT["Title — text-sm font-medium<br/>Description — text-xs muted · optional"]
        ACTION["Action link — optional"]
        CLOSE["× dismiss"]
    end

    ICON --- CONTENT --- ACTION --- CLOSE
```

### Notification Bell Wireframe

```mermaid
flowchart TB
    subgraph TopNav["Top Nav — right section"]
        BELL["Bell icon button · 20px"]
        DOT["Unread dot — 8px primary · top-right"]
    end

    subgraph Popover["Notification Popover — 380px · max-h-480px"]
        HEADER["Notifications · Mark all read · Settings link"]
        TABS["All · Approvals · Workflows · Mentions"]
        subgraph List["ScrollArea"]
            N1["Unread — bold · blue dot · 2m ago"]
            N2["Read — muted · 1h ago"]
            N3["Unread — approval — purple pill"]
        end
        FOOTER["View all notifications →"]
    end

    BELL --> Popover
```

### In-App Notification Item Wireframe

```mermaid
flowchart LR
    subgraph Item["Notification Item — min-h-64px px-4 py-3"]
        DOT2["Unread indicator — 8px circle"]
        ICON2["Category icon — 20px"]
        subgraph Text["Content — flex-1"]
            TITLE2["Title — text-sm"]
            DESC2["Description — text-xs muted · 2 line clamp"]
            META["Case FMG-2024-0847 · 15m ago"]
        end
        ACTION2["Quick action button — optional"]
    end

    DOT2 --- ICON2 --- Text --- ACTION2
```

### Teams Integration Status Wireframe

```mermaid
flowchart TB
    subgraph TeamsStatus["Teams Integration — Settings → Integrations"]
        HEADER2["Microsoft Teams"]
        subgraph StatusRow["Connection Status"]
            INDICATOR["Status dot — green · amber · red · gray"]
            LABEL["Connected · Degraded · Disconnected · Not configured"]
            LAST["Last sync: 2 minutes ago"]
        end
        CHANNELS["Default channel: #case-updates"]
        ACTIONS["Configure · Test · Disconnect"]
    end
```

### Full Notifications Page Wireframe

```mermaid
flowchart TB
    subgraph Page["/notifications"]
        PAGEHEADER["Notifications · Mark all read"]
        FILTERS2["Filter: All · Unread · Approvals · Deadlines · System"]
        TABLE2["NotificationTable — date, category, message, case, actions"]
        PAGINATE["Pagination"]
    end
```

---

## States

### Toast States

| State | Icon | Duration | Dismiss |
|-------|------|----------|---------|
| **Success** | CheckCircle — green | 5s auto | × or swipe |
| **Error** | AlertCircle — red | Persistent until dismissed | × required |
| **Warning** | AlertTriangle — amber | 8s auto | × or swipe |
| **Info** | Info — blue | 5s auto | × or swipe |
| **Loading** | Loader2 — spin | Until resolve | Not dismissible |
| **Action** | Context icon | 8s auto | × or action click |

```mermaid
stateDiagram-v2
    [*] --> Entering: toast triggered
    Entering --> Visible: slide-in 300ms
    Visible --> Exiting: timeout or dismiss
    Visible --> Visible: hover pauses timer
    Exiting --> [*]: fade-out 200ms
    Loading --> Success: operation complete
    Loading --> Error: operation failed
```

**Rule:** Toasts are for **transient feedback** — never for critical legal confirmations. Use [dialogs.md](./dialogs.md) for approve/reject/delete.

### Notification Item States

| State | Visual | Behavior |
|-------|--------|----------|
| **Unread** | Bold title + blue dot | Click marks read + navigates |
| **Read** | Normal weight + no dot | Click navigates only |
| **Archived** | Hidden from default views | Restorable from settings |
| **Expired** | Removed after 90 days | Configurable firm retention |

### Bell Icon States

| State | Visual |
|-------|--------|
| No unread | Bell icon only |
| Unread (1–9) | Blue dot overlay |
| Unread (10+) | Blue dot + "9+" badge |
| Popover open | `bg-accent` on bell button |
| Real-time update | Dot appears without page refresh (SSE) |

```mermaid
stateDiagram-v2
    [*] --> NoUnread
    NoUnread --> HasUnread: SSE notification.received
    HasUnread --> NoUnread: all marked read
    HasUnread --> HasUnread: new notification arrives
    HasUnread --> PopoverOpen: click bell
    PopoverOpen --> HasUnread: close popover
```

### Teams Integration States

| State | Dot Color | Label | User Action |
|-------|-----------|-------|-------------|
| **Connected** | Green `#047857` | Connected | None |
| **Degraded** | Amber `#B45309` | Degraded — delays detected | View details |
| **Disconnected** | Red `#B91C1C` | Disconnected | Reconnect |
| **Not configured** | Gray `#71717A` | Not configured | Configure |
| **Syncing** | Blue pulse | Syncing… | Wait |
| **Error** | Red | Error — permissions revoked | Re-authorize |

---

## Variants

### Notification Categories

| Category | Icon | Color accent | Typical Events |
|----------|------|--------------|----------------|
| **Approval** | ShieldCheck | Purple `status-approval` | AI summary pending, document approval |
| **Workflow** | GitBranch | Blue `status-info` | Workflow completed, failed, cancelled |
| **Deadline** | Clock | Urgency-scaled | Overdue, due today, reminder |
| **Document** | FileText | Neutral | Upload complete, OCR ready |
| **AI** | Sparkles | Purple | AI job complete, draft ready for review |
| **Mention** | AtSign | Primary | @mention in case notes (Phase 2) |
| **System** | Settings | Neutral | Maintenance, integration status |
| **Client portal** | Users | Green | Client uploaded document |

### Toast vs In-App vs Email Routing

| Event | Toast | In-app | Email | Teams |
|-------|-------|--------|-------|-------|
| AI job complete | Yes | Yes | User pref | No |
| Approval required | No | Yes | Yes — attorney | Yes — if configured |
| Workflow failed | Yes | Yes | Ops pref | Yes |
| Deadline overdue | No | Yes | Yes | Optional |
| Document uploaded | Yes | Yes | No | No |
| Bulk action complete | Yes | Yes | No | No |
| Teams disconnected | No | Yes — system | Admin | — |

### Deadline Notification Urgency Variants

| Urgency | Title prefix | Chip color | Icon |
|---------|--------------|------------|------|
| Overdue | "Overdue:" | Red | AlertTriangle |
| Due today | "Due today:" | Amber | Clock |
| Due tomorrow | "Due tomorrow:" | Neutral | Calendar |
| Reminder (7d) | "Upcoming:" | Muted | Calendar |

```mermaid
flowchart LR
    subgraph UrgencyScale["Deadline Urgency — notification rendering"]
        O["Overdue — red"]
        T["Due today — amber"]
        S["Due soon — neutral"]
        N["Normal — muted"]
    end

    O --> T --> S --> N
```

### Approval Notification Variant

```mermaid
flowchart TB
    subgraph ApprovalNotif["Approval Notification"]
        PILL["Pending Review — status-approval pill"]
        TITLE3["AI summary ready for review"]
        CASE["Case FMG-2024-0847 — Smith v. Jones"]
        PREVIEW2["First line of summary — truncated"]
        ACTIONS3["Review now — primary | Dismiss"]
    end
```

Attorneys see "Review now" → opens approval dialog.  
Paralegals see "View status" → read-only AI draft panel.

---

## Interaction Specs

### Toast Behavior

| Action | Behavior |
|--------|----------|
| Appear | Stack bottom-right; push existing up |
| Max visible | 3; oldest dismissed when 4th arrives |
| Hover | Pause auto-dismiss timer |
| Click action link | Navigate + dismiss toast |
| Click × | Dismiss immediately |
| Swipe right (mobile) | Dismiss |
| Duplicate suppression | Same message within 5s ignored |

### Bell Popover Behavior

| Action | Behavior |
|--------|----------|
| Click bell | Toggle popover |
| Click outside | Close popover |
| Click notification | Mark read + navigate to resource + close |
| Mark all read | PATCH API; dot clears |
| Tab switch | Filter list client-side; no refetch |
| Scroll to bottom | Load more (cursor pagination) |
| Real-time | SSE prepends new item + increment badge |

```mermaid
sequenceDiagram
    participant SSE as SSE Stream
    participant B as NotificationBell
    participant API as FastAPI
    participant U as User

    SSE->>B: notification.received event
    B->>B: Increment unread badge
    alt Popover open
        B->>B: Prepend to list with slide-in
    end
    U->>B: Click notification
    B->>API: PATCH /api/v1/notifications/{id}/read
    B->>U: Navigate to /cases/{id}/ai-review
```

### In-App Notification Actions

| Action | Behavior |
|--------|----------|
| Primary quick action | Context-specific — "Approve", "View", "Retry" |
| Dismiss / archive | Swipe or × ; removes from active list |
| Mark unread | Available on full notifications page |
| Batch mark read | Checkbox selection on notifications page |

### Teams Integration Interaction

| Action | Behavior |
|--------|----------|
| Configure | OAuth flow → Microsoft Entra ID |
| Test | Send test message to default channel; toast result |
| Disconnect | Confirm dialog → revoke tokens |
| Channel picker | Dropdown of Teams channels post-connect |
| Status refresh | Manual refresh + auto every 5 min |
| Degraded detail | Sheet with last 5 delivery failures |

**Teams message format (orchestrated by n8n, displayed status in UI):**

| Field | Source |
|-------|--------|
| Connection status | API health check |
| Last successful delivery | Notification delivery log |
| Failed count (24h) | Metrics endpoint |
| Default channel | Firm settings |

### Real-Time Delivery Architecture

```mermaid
flowchart LR
    subgraph Backend["Backend"]
        EVENT[Domain Event]
        NOTIF_SVC[Notification Service]
        SSE_EP[SSE /api/v1/events/stream]
    end

    subgraph Frontend["Frontend"]
        SSE_CLIENT[SSE Client]
        RQ[React Query cache]
        BELL[NotificationBell]
        TOAST[Toast]
    end

    EVENT --> NOTIF_SVC
    NOTIF_SVC --> SSE_EP
    SSE_EP --> SSE_CLIENT
    SSE_CLIENT --> RQ
    SSE_CLIENT --> BELL
    SSE_CLIENT --> TOAST
```

Cross-reference: [../../12-ui/real-time-updates.md](../../12-ui/real-time-updates.md)

---

## Accessibility

| Requirement | Implementation |
|-------------|----------------|
| Toast | `role="status"` for info/success; `role="alert"` for error |
| Toast | Not focus-trapped; action link is focusable |
| Bell | `aria-label="Notifications, 3 unread"` — count updates |
| Popover | `aria-expanded` on bell button |
| List | `role="list"` + `role="listitem"` per notification |
| Unread | `aria-label="Unread"` on dot — not color alone |
| Mark all read | Button with clear label |
| Real-time | `aria-live="polite"` on unread count |
| Teams status | Status text + icon — not dot color alone |
| Keyboard | Arrow keys navigate notification list in popover |

Cross-reference: [../../12-ui/accessibility.md](../../12-ui/accessibility.md)

---

## Do / Don't

| Do | Don't |
|----|-------|
| Use toast for "Saved" and async completion | Use toast for "Delete 50 cases?" confirmation |
| Persist approval notifications until acted | Auto-dismiss approval toasts |
| Update bell badge via SSE | Require page refresh for unread count |
| Show case number in notification metadata | Generic "Something happened" |
| Route attorneys to approval dialog | Show approve button to unauthorized roles |
| Suppress duplicate toasts within 5s | Stack 10 identical "Saved" toasts |
| Use urgency colors for deadline notifications | Same styling for overdue and FYI |
| Show Teams degraded status proactively | Silent message delivery failures |
| Allow mark-all-read | Force individual dismiss only |
| Respect user notification preferences | Email every event to everyone |

---

## References

| Document | Path |
|----------|------|
| Component library | [component-library.md](./component-library.md) |
| Interactions | [component-interactions.md](./component-interactions.md) |
| Dialogs (approval flow) | [dialogs.md](./dialogs.md) |
| Real-time updates | [../../12-ui/real-time-updates.md](../../12-ui/real-time-updates.md) |
| Human-in-the-loop | [../../07-ai/human-in-the-loop.md](../../07-ai/human-in-the-loop.md) |
| Workflow webhooks | [../../06-workflows/webhook-contracts.md](../../06-workflows/webhook-contracts.md) |
| Data tables (notifications page) | [data-tables.md](./data-tables.md) |
| Design tokens | [../../12-ui/design-system.md](../../12-ui/design-system.md) |
