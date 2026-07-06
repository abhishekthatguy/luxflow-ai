# Jira Import Package — LexFlow AI

**Project Key suggestion:** `LEX` or `LFA`  
**Template:** Scrum  
**Total Epics:** 6  
**Total Stories:** 69  
**Sprint Duration:** 2 weeks each (Sprints 0–5 = 12 weeks)

---

## Import Order

1. **Configure project** — Components and labels (see below)
2. **Import `epics.csv`** — Creates 6 epics
3. **Import `stories.csv`** — Links stories to epics via Epic Link column
4. **Create sprints** — Sprint 0 through Sprint 5 in Jira backlog
5. **Assign stories** — Filter by `Sprint` column or `sprint-N` label
6. **Optional:** Import `tasks.csv` as sub-tasks (link manually to parent stories)

---

## Jira Cloud CSV Import

**Path:** Jira Settings → System → External System Import → CSV

### epics.csv mapping

| CSV Column | Jira Field |
|------------|------------|
| Summary | Summary |
| Issue Type | Epic |
| Description | Description |
| Priority | Priority |
| Labels | Labels |
| Components | Components |

### stories.csv mapping

| CSV Column | Jira Field |
|------------|------------|
| Issue Key | External issue ID (optional — for reference) |
| Summary | Summary |
| Issue Type | Story |
| Description | Description |
| Epic Link | Epic Link (match Epic Summary text) |
| Story Points | Story Points / Story point estimate |
| Priority | Priority |
| Labels | Labels |
| Components | Components |
| Acceptance Criteria | Description (append) or Custom field |

**Note:** If Epic Link import fails, use Jira's bulk edit to set Epic Link after both files are imported.

---

## Recommended Components

Create in Project Settings → Components:

| Component | Lead Role |
|-----------|-----------|
| `backend` | Backend Engineer |
| `frontend` | Frontend Engineer |
| `infra` | DevOps |
| `n8n` | Workflow Engineer |
| `ai` | AI/ML Engineer |
| `qa` | SDET |
| `docs` | Tech Lead / PO |

---

## Recommended Labels

| Label | Usage |
|-------|-------|
| `sprint-0` … `sprint-5` | Sprint assignment |
| `matter-wall` | Requires matter wall tests |
| `security` | Security-sensitive |
| `epic` | Epic marker |
| `blocker` | Cross-sprint dependency |
| `ci` | CI/CD work |
| `aws` | AWS infrastructure |
| `observability` | Logging/tracing/metrics |

---

## Story Point Summary by Sprint

| Sprint | Stories | Total SP |
|--------|---------|----------|
| Sprint 0 | 7 | 34 |
| Sprint 1 | 10 | 55 |
| Sprint 2 | 11 | 62 |
| Sprint 3 | 14 | 68 |
| Sprint 4 | 14 | 72 |
| Sprint 5 | 13 | 58 |
| **Total** | **69** | **349** |

---

## Epic Link Text (must match exactly)

| Epic Link Value in CSV |
|------------------------|
| Documentation & Alignment |
| Platform Infrastructure |
| Identity Auth & Domain Foundation |
| Case Management Module |
| AI Services & Workflow Orchestration |
| Production Readiness & AWS Deployment |

---

## Alternative: Jira REST API

For automated import, use Jira REST API v3:

```bash
# Example — create epic (adapt URL, auth, project key)
curl -X POST -H "Content-Type: application/json" \
  -d '{"fields":{"project":{"key":"LEX"},"summary":"Platform Infrastructure","issuetype":{"name":"Epic"}}}' \
  https://your-domain.atlassian.net/rest/api/3/issue
```

Refer to detailed stories in [`../sprint-00-documentation.md`](../sprint-00-documentation.md) through [`../sprint-05-production.md`](../sprint-05-production.md) for full acceptance criteria.

---

## Linear Import

1. Create Project "LexFlow AI"
2. Import CSV via Linear CSV import (Settings → Import)
3. Map Epic Link → Project/Milestone
4. Create Cycles: Sprint 0–5 (2 weeks each)

---

## Azure DevOps Import

1. Create project with Agile process
2. Import `stories.csv` as User Stories
3. Map Epic Link → Feature parent link
4. Create Iterations: Sprint 0–5
