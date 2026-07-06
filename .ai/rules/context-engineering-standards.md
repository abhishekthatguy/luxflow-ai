# Context Engineering Standards — LexFlow AI

**Applies to:** `.ai/` directory and AI assistant configuration  
**Docs:** `docs/README.md`, all numbered `docs/` sections

---

## Purpose

Define how to **maintain the `.ai/` layer** — rules, prompts, and curated context — so AI assistants work effectively without duplicating or contradicting `docs/`.

---

## Layer Model

```
docs/               Human-readable architecture (canonical, comprehensive)
.ai/rules/          Actionable constraints for AI assistants (this directory)
.ai/prompts/        Reusable task prompts for common assistant workflows
.ai/context/        Curated snippets loaded for specific task types
```

| Layer | Audience | Content Style |
|-------|----------|---------------|
| `docs/` | Engineers, auditors, onboarding | Narrative, diagrams, tradeoffs |
| `.ai/rules/` | AI assistants | Imperative, checklists, do/don't |
| `.ai/prompts/` | AI assistants | Task templates with explicit outputs |
| `.ai/context/` | AI assistants | Short excerpts + links, not full docs |

**Rule:** `docs/` is source of truth. `.ai/` **summarizes and constrains** — never contradicts ADRs or security docs.

---

## When to Update `.ai/`

| Trigger | Update |
|---------|--------|
| New ADR accepted | Relevant rule files + README invariant list |
| API contract change | `api-standards.md`, `error-handling.md` |
| New matter wall rule | `security-rules.md`, `testing-standards.md` |
| New bounded context | `folder-structure.md`, `backend-standards.md` |
| n8n policy change | `workflow-standards.md` |
| New prompt registry pattern | `prompt-engineering-standards.md` |
| CI gate change | `testing-standards.md`, `code-review-checklist.md` |

Update `.ai/rules/` in the **same PR** as the behavioral change when possible.

---

## Rule File Authoring Standards

Every rule file must include:

1. **Applies to** — paths and roles
2. **Purpose** — one paragraph
3. **Do / Don't table** — actionable
4. **Checklist** — for PR or task completion
5. **Good vs Bad examples** — pseudocode OK
6. **References** — links to `docs/` sections

| Do | Don't |
|----|-------|
| Keep rules under ~300 lines | Paste entire `docs/` chapters |
| Use imperatives ("Must", "Never") | Use vague "consider" without default |
| Link to docs for depth | Duplicate ADR full text |
| Mark blockers explicitly | Bury security rules in prose |

---

## `.ai/prompts/` Conventions

```
.ai/prompts/
├── README.md
├── add-api-endpoint.md
├── add-case-feature.md
├── add-n8n-workflow.md
├── fix-matter-wall.md
└── review-pr-security.md
```

### Prompt Template Structure

```markdown
# Task: {Title}

## Load These Rules
- .ai/rules/{file}.md
- docs/{section}/{file}.md

## Context
{What the assistant needs to know — 5-10 bullets}

## Constraints
- {Non-negotiable constraints}

## Output Format
- {Expected deliverables}

## Verification
- [ ] Checklist items
```

---

## `.ai/context/` Conventions

Curated snippets for token-efficient loading:

```
.ai/context/
├── platform-invariants.md      # 1-page invariant summary
├── matter-walls-quickref.md    # MW-001 through MW-008
├── api-envelope-quickref.md    # Envelope + RFC 7807 shape
└── bounded-contexts-map.md     # Context ownership table
```

| Do | Don't |
|----|-------|
| Keep snippets < 100 lines | Store full API endpoint catalogs |
| Include "last synced" date | Let snippets drift from docs |
| Link to canonical doc | Copy doc content that changes often |

---

## Sync & Drift Prevention

| Practice | Frequency |
|----------|-----------|
| Review `.ai/rules/README.md` invariants vs `docs/README.md` | Each ADR merge |
| CI check: rule files reference valid `docs/` paths | Phase 2 |
| Quarterly audit of `.ai/context/` snippets | Quarterly |

When `docs/` and `.ai/rules/` conflict:

1. **`docs/13-decisions/` (ADRs) win**
2. **`docs/08-security/` wins** over convenience
3. Update `.ai/rules/` to match — do not change docs from rules alone

---

## AI Assistant Loading Guide

### Minimum Context by Task

| Task | Load |
|------|------|
| Any code change | `.ai/rules/README.md` + layer-specific rule |
| Security-sensitive | + `security-rules.md` |
| API endpoint | + `api-standards.md`, `docs/04-api/` |
| n8n only | `workflow-standards.md` only |
| Prompt template | `prompt-engineering-standards.md` |

### Token Budget Priority

1. Security rules and ADR invariants
2. Layer-specific standards
3. `.ai/context/` quickrefs
4. Linked `docs/` sections (read on demand)

---

## Do / Don't for Assistants

| Do | Don't |
|----|-------|
| Read rules before coding | Improvise architecture |
| Cite ADR number when applying decision | Contradict ADR-002 or ADR-007 |
| Ask before deploying to production n8n | Push workflow JSON live without approval |
| Update rules when user changes conventions | Silently encode one-off hacks in rules |

---

## Creating New Rule Files

1. Add file to `.ai/rules/`
2. Add entry to `.ai/rules/README.md` index
3. Cross-link from related rule files
4. Reference canonical `docs/` section
5. PR with description of what behavior it encodes

---

## References

- [README.md](./README.md)
- [docs/README.md](../../docs/README.md)
- [docs/13-decisions/README.md](../../docs/13-decisions/README.md)
- [docs/MIGRATION.md](../../docs/MIGRATION.md)
