# Task: Verify Platform Readiness

**Use when:** Before starting Sprint 2, RFC-002, authentication, RBAC, domain models, or any business logic.

**Block if:** Any item in the Platform Readiness Checklist fails.

---

## Canonical Doc

[`docs/14-playbooks/platform-readiness-gate.md`](../../docs/14-playbooks/platform-readiness-gate.md)

---

## Checklist (All Must Pass)

| # | Check | Command |
|---|-------|---------|
| 1 | Docker Compose boots all services | `make dev && make ps` |
| 2 | Health endpoints for every service | `make verify-health` |
| 3 | Structured logging + correlation IDs | `make verify-logging` |
| 4 | OpenTelemetry traces in Grafana | `make verify-traces` |
| 5 | Redis cache abstraction tested | `make verify-redis` |
| 6 | RabbitMQ publish/consume sample | `make verify-rabbitmq` |
| 7 | Celery sample job | `make verify-celery` |
| 8 | n8n → FastAPI internal network | `make verify-n8n-callback` |
| 9 | MinIO upload/download | `make verify-minio` |
| 10 | GitHub Actions CI green | Check `main` branch status |

**All-in-one:** `make verify-platform`

---

## AI Assistant Rules

1. **Do not implement auth, JWT, matter walls, domain entities, or case logic** if platform gate is not verified.
2. If user asks for Sprint 2 work and gate status is unknown → run or request verification first.
3. Infrastructure-only PRs (Sprint 1) are allowed without this gate passing.
4. Report failing check number and suggested fix from playbook.

---

## Output

```markdown
## Platform Readiness Report

| # | Check | Status |
|---|-------|--------|
| 1 | Docker Compose | ✅ / ❌ |
| ... | ... | ... |

**Gate:** PASS / FAIL
**Action:** {proceed to auth / fix Sprint 1 item N}
```

---

## References

- [Platform Readiness Gate](../../docs/14-playbooks/platform-readiness-gate.md)
- [Sprint 1 exit criteria](../../docs/17-sprint-planning/sprint-01-infrastructure.md)
- [RFC-002](../../docs/18-rfc/RFC-002-authentication-rbac.md)
