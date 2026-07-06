# Task: Generate Documentation

**LexFlow AI** — AI prompt template for technical documentation.

---

## Prompt (Copy-Paste Ready)

```
You are generating documentation for LexFlow AI, an enterprise AI automation platform for law firms.

## Target
- Document type: {{doc_type}} (api | architecture | domain | playbook | adr | testing | security | ui)
- Topic: {{topic}}
- Audience: {{audience}} (engineer | security | product | ops | all)
- Ticket: {{ticket_id}}

## Context to Load
Read these before writing:

1. `.ai/memory/` — project memory and recent decisions
2. `.ai/rules/` — AI coding rules for this repo
3. `docs/README.md` — documentation index and standards
4. Relevant section README (e.g., `docs/04-api/README.md`)
5. Related existing docs in the target section
6. Source code or implementation being documented
7. `.ai/handbook/` — engineering standards and lifecycle

## Constraints
Follow LexFlow enterprise document standards (see docs/README.md):

Required sections for every document:
- **Purpose** — why this document exists
- **Scope** — what is and is not covered
- **Responsibilities** — who owns what
- **Architecture** — technical design with Mermaid diagrams
- **Flow Diagrams** — sequence, state, ER, or deployment diagrams as appropriate
- **Best Practices** — recommended patterns
- **Tradeoffs** — pros/cons table
- **Future Improvements** — planned evolution
- **References** — links to related documents

Additional rules:
- Version and last-updated date in header
- Mermaid diagrams for flows and architecture
- No duplication — link to canonical docs instead of copying
- Platform invariants referenced where relevant
- Use ubiquitous language from `docs/02-domain/ubiquitous-language.md`
- ADRs in `docs/13-decisions/` only (not `docs/adr/`)

## Step-by-Step Instructions
1. **Audience** — Identify what the reader needs to know and what they can skip
2. **Outline** — Map required sections; identify cross-references
3. **Research** — Read source code, existing docs, ADRs for accuracy
4. **Draft** — Write each section; include at least one Mermaid diagram
5. **Examples** — Add JSON examples for API docs; SQL for schema docs
6. **Cross-links** — Link to related docs in other folders
7. **Glossary** — Use terms from ubiquitous-language.md consistently
8. **Review** — Check against platform invariants and ADRs
9. **Index update** — Add entry to section README.md
10. **Migration** — If superseding legacy flat doc, note in MIGRATION.md

## Output Format

### 1. File Path
Exact path: `docs/{{section}}/{{filename}}.md`

### 2. Complete Document
Full markdown with all required sections.

### 3. Diagrams
List of Mermaid diagrams included (with type: flowchart, sequence, erDiagram, etc.)

### 4. Index Updates
Exact additions to section README.md and docs/README.md if needed.

### 5. Cross-Reference Updates
Other documents that should link to this new doc.

## Verification Checklist
- [ ] All required sections present (Purpose, Scope, Responsibilities, Architecture, etc.)
- [ ] Version and date in header
- [ ] At least one Mermaid diagram
- [ ] Ubiquitous language used consistently
- [ ] Platform invariants referenced where applicable
- [ ] No duplication of content from other docs (links instead)
- [ ] JSON/SQL examples included where appropriate
- [ ] Section README.md updated with new entry
- [ ] Cross-references to/from related docs
- [ ] ADR references correct (13-decisions/, not adr/)
- [ ] Audience-appropriate depth and tone
```

---

## Example Variables

| Variable | Example Value |
|----------|---------------|
| `{{doc_type}}` | api |
| `{{topic}}` | Case deadline endpoints |
| `{{audience}}` | engineer |
| `{{section}}` | 04-api |
| `{{filename}}` | endpoints-case-deadlines |
| `{{ticket_id}}` | LEX-142 |
