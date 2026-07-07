# Phase 1 Go-Live Checklist (LEX-513)

Use before production promotion. Full playbook: `docs/14-playbooks/deploy-production.md`.  
**Complete checklist:** [`PRODUCTION-DEPLOYMENT-CHECKLIST.md`](./PRODUCTION-DEPLOYMENT-CHECKLIST.md)

## Pre-flight

- [ ] `make verify-sprint5` passes on staging
- [ ] Playwright E2E green (PR + nightly workflow)
- [ ] k6 baseline: `k6 run tests/load/cases-read.js` — p95 &lt; 500ms, errors &lt; 1%
- [ ] Trivy CRITICAL = 0 on API image
- [ ] Alembic at head; backup verified within 24h
- [ ] Secrets in AWS Secrets Manager (not `.env` in prod)
- [ ] n8n not publicly reachable (security scan must fail external access)
- [ ] WAF + rate limiting enabled on auth (staging validated)
- [ ] Rollback: previous ECS task definition id documented

## Sign-off

| Role | Name | Date |
|------|------|------|
| Tech Lead | | |
| Product Owner | | |
| Security | | |
