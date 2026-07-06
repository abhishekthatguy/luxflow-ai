# RFC-002: Authentication & RBAC

**Status:** Planned  
**Author:** TBD  
**Created:** 2026-07-06  
**Sprint / Epic:** Sprint 2 — Auth & Domain  
**Related ADRs:** [ADR-005](../13-decisions/005-jwt-authentication.md), [ADR-007](../13-decisions/007-matter-walls-404-deny.md)

---

## Summary

> **Planned RFC** — full draft required before Sprint 2 kickoff. Copy [`_template.md`](./_template.md) and replace this stub.

JWT + refresh token auth, RBAC permission model, login/logout flows, SSR-compatible session handling, and matter wall foundation.

---

## Draft Checklist (before In Review)

- [ ] **Platform Readiness Gate passed** — all 10 checks in [`platform-readiness-gate.md`](../14-playbooks/platform-readiness-gate.md)
- [ ] Login, refresh, logout sequence diagrams
- [ ] RBAC matrix — `docs/04-api/authorization-rbac.md` alignment
- [ ] Identity schema — `docs/05-database/identity-schema.md`
- [ ] Security review: threat model STRIDE categories
- [ ] UI: login screen in design system
- [ ] Implementation plan → Sprint 2 stories

---

## References

- [sprint-02-auth-domain.md](../17-sprint-planning/sprint-02-auth-domain.md)
- [authentication.md](../04-api/authentication.md)
- [authorization-rbac.md](../04-api/authorization-rbac.md)
