# ADR-005: JWT + Refresh Token Authentication

**Status:** Accepted  
**Date:** 2026-07-06  
**Deciders:** Architecture Team

## Context

LexFlow AI needs authentication for a web application with multiple user roles, plus future SSO integration with Microsoft Entra ID. The auth mechanism must work with SPA/SSR (Next.js), support RBAC, and be stateless enough for horizontal scaling.

## Options Considered

1. **Server-side sessions (Redis)** — Session ID in cookie, session data in Redis.
   - Pros: Easy revocation, familiar pattern
   - Cons: Redis dependency for every request, harder with SSR/hydration

2. **JWT access + refresh tokens** — Short-lived JWT, long-lived refresh token in httpOnly cookie.
   - Pros: Stateless verification, works with SSR and API, standard pattern
   - Cons: Token revocation requires blocklist or refresh token rotation

3. **OAuth 2.0 only (Entra ID from day one)** — No local auth, Entra only.
   - Pros: Enterprise SSO immediately
   - Cons: Blocks Phase 1 development before Entra integration; not all firms ready

## Decision

**JWT access tokens (15 min) + refresh tokens (7 days, rotated, httpOnly cookie)** for Phase 1–2. Microsoft Entra ID OIDC added as alternative login in Phase 3. Permissions are resolved server-side on each request — not embedded in JWT claims.

## Consequences

- **Easier:** Stateless API scaling, standard pattern, Entra ID is additive
- **Easier:** Works for both web and future mobile clients
- **Harder:** Refresh token rotation logic, token revocation on password change
- **Security:** Short access token lifetime limits exposure; refresh token rotation detects theft
