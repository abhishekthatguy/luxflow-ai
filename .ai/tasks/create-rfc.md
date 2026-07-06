# Task: Create RFC

**Use when:** Starting a major feature, new module, API resource group, AI capability, or n8n workflow family.

**Do not use when:** Bug fix, refactor without contract change, dependency bump, doc typo.

---

## Before You Start

1. Read [`docs/18-rfc/README.md`](../../docs/18-rfc/README.md) — process and index
2. Check if RFC already exists (Accepted, Draft, or Planned stub)
3. Read [`.ai/handbook/rfc-process.md`](../handbook/rfc-process.md)
4. Load related ADRs from `docs/13-decisions/`

---

## Inputs Required from User

| Input | Required |
|-------|----------|
| Feature name | Yes |
| Target sprint / epic | Yes |
| Primary persona | Yes |
| Bounded context | Yes |
| Security-sensitive? | Yes / No |
| AI involved? | Yes / No |

---

## Steps

### 1. Allocate RFC Number

- Read index in `docs/18-rfc/README.md`
- Next number = highest + 1 (or expand Planned stub in place)

### 2. Copy Template

```
docs/18-rfc/_template.md → docs/18-rfc/RFC-NNN-kebab-title.md
```

### 3. Fill Sections (in order)

| Section | Load from |
|---------|-----------|
| Problem & personas | `docs/01-product/user-personas.md`, `capabilities.md` |
| Non-goals | `docs/01-product/non-goals.md` |
| Domain | `docs/02-domain/{aggregate}.md` |
| API sketch | `docs/04-api/rest-standards.md`, existing endpoint docs |
| Data model | `docs/05-database/{schema}-schema.md` |
| UI | `docs/16-design-system/screens/` |
| Security | `docs/08-security/matter-walls.md`, ADR-007 |
| AI | `docs/07-ai/`, ADR-004, ADR-008 |
| n8n | `docs/06-workflows/`, ADR-002 |
| Stories | `docs/17-sprint-planning/sprint-NN-*.md` |

### 4. Add Diagrams

Minimum one of: sequence, state, ER, or flowchart (Mermaid).

### 5. ADR Check

If RFC introduces binding architecture choice → draft ADR in `docs/13-decisions/` per [adr-process.md](../handbook/adr-process.md).

### 6. Update Index

Add row to `docs/18-rfc/README.md` RFC Index table.

### 7. Present for Review

Output summary for user:
- RFC number and path
- Open questions needing product/security input
- Recommended reviewers
- **Do not implement** until status is **Accepted** (unless user explicitly overrides)

---

## Output Checklist

- [ ] `RFC-NNN-*.md` created with all template sections (or N/A justified)
- [ ] README index updated
- [ ] Related Planned stub replaced or expanded
- [ ] ADR drafted if needed
- [ ] Open questions table populated
- [ ] Implementation plan maps to sprint stories

---

## Status Transitions

| From | To | Action |
|------|-----|--------|
| — | Draft | File created |
| Draft | In Review | PR opened on `rfc/NNN-*` branch |
| In Review | Accepted | Tech lead + product approve; merge |
| Accepted | Implemented | Epic complete; fill Implementation Notes |

---

## References

- [RFC Template](../../docs/18-rfc/_template.md)
- [000-rfc-process.md](../../docs/18-rfc/000-rfc-process.md)
- [Definition of Ready](../handbook/definition-of-ready.md)
