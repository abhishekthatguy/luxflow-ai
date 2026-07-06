# Authentication

**LexFlow AI** — JWT, Refresh Tokens & Login Flows  
**Version:** 1.0  
**Status:** Draft — Pre-Implementation  
**Last Updated:** 2026-07-06

---

## Purpose

Specify how clients authenticate to the LexFlow AI REST API using **JWT access tokens** and **rotating refresh tokens**. This document defines token structure, login/logout flows, session lifecycle, and the roadmap to Microsoft Entra ID SSO.

---

## Scope

| In Scope | Out of Scope |
|----------|--------------|
| `/auth/*` public endpoints | RBAC permission checks (see [authorization-rbac.md](./authorization-rbac.md)) |
| JWT access token format and validation | User provisioning admin APIs |
| Refresh token rotation and revocation | Client portal invitation flow (detailed in security docs) |
| Login, logout, password reset flows | n8n HMAC authentication (see [webhooks-internal.md](./webhooks-internal.md)) |
| Brute-force protection and session policy | Entra ID full implementation (Phase 3 roadmap) |

**Phase 1–2:** Email + password authentication  
**Phase 3:** Microsoft Entra ID OIDC as alternative login

---

## Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **FastAPI auth middleware** | Validate JWT on every protected request |
| **Identity service** (`services/identity_access/`) | User lookup, password verify, token issuance |
| **PostgreSQL** | Store refresh token hashes, user credentials |
| **Redis** | Cache resolved permission sets (5-minute TTL) |
| **AWS Secrets Manager** | JWT signing keys (RS256 private key) |
| **Next.js frontend** | Store access token in memory; refresh via httpOnly cookie |
| **Client applications** | Never store refresh tokens in localStorage |

Authorization (what the user *may do*) is handled separately — see [authorization-rbac.md](./authorization-rbac.md).

---

## Architecture

```mermaid
flowchart TB
    subgraph Client["Client (Browser / App)"]
        MEM[Access Token — Memory]
        COOKIE[Refresh Token — httpOnly Cookie]
    end

    subgraph API["FastAPI"]
        AUTH_R["/auth/* Routes"]
        MW[Auth Middleware]
        ID[Identity Service]
    end

    subgraph Storage["Storage"]
        PG[(PostgreSQL — users, refresh_tokens)]
        REDIS[(Redis — permission cache)]
        SM[Secrets Manager — JWT keys]
    end

    Client -->|POST /auth/login| AUTH_R
    AUTH_R --> ID
    ID --> PG
    ID --> REDIS
    ID --> SM
    AUTH_R -->|Set-Cookie| COOKIE
    AUTH_R -->|accessToken JSON| MEM

    Client -->|Bearer token| MW
    MW --> SM
    MW --> REDIS
```

### Token Model

| Token | Format | Lifetime | Storage | Transport |
|-------|--------|----------|---------|-----------|
| Access token | JWT (RS256) | 15 minutes | Client memory / secure session | `Authorization: Bearer` header |
| Refresh token | Opaque UUID | 7 days | httpOnly, Secure, SameSite=Strict cookie | Cookie only — never in JSON body on login response |

**Design decision:** Permissions are **not embedded** in the JWT. The server resolves permissions on each request from PostgreSQL/Redis cache. See [ADR-005](../13-decisions/005-jwt-authentication.md).

---

## Flow Diagrams

### Login (Email + Password)

```mermaid
sequenceDiagram
    participant C as Client (Browser)
    participant API as FastAPI
    participant ID as Identity Service
    participant DB as PostgreSQL
    participant Redis as Redis
    participant SM as Secrets Manager

    C->>API: POST /api/v1/auth/login<br/>{ email, password }
    API->>ID: authenticate(email, password)
    ID->>DB: SELECT user WHERE email = ?
    ID->>ID: Verify bcrypt hash (cost 12)
    alt Invalid credentials
        ID->>DB: Increment failed_attempts
        ID-->>API: AuthenticationError
        API-->>C: 401 Unauthorized
    else Account locked
        API-->>C: 401 + account locked message
    else Valid credentials
        ID->>SM: Load JWT signing key
        ID->>ID: Generate access JWT (15 min, RS256)
        ID->>ID: Generate opaque refresh token
        ID->>DB: INSERT refresh_token (hash, user_id, expires_at)
        ID->>Redis: Cache user permissions (TTL 5 min)
        API-->>C: 200 { accessToken, expiresIn, tokenType }<br/>Set-Cookie: refreshToken (httpOnly, Secure, SameSite=Strict)
    end
```

### Token Refresh (Rotation)

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant ID as Identity Service
    participant DB as PostgreSQL

    C->>API: POST /api/v1/auth/refresh<br/>Cookie: refreshToken=...
    API->>ID: refresh(refresh_token)
    ID->>DB: SELECT refresh_token WHERE hash = ?
    alt Token not found / expired / revoked
        ID-->>API: InvalidRefreshToken
        API-->>C: 401 Unauthorized (clear cookie)
    else Valid token
        ID->>DB: REVOKE old refresh token
        ID->>ID: Issue new access JWT + new refresh token
        ID->>DB: INSERT new refresh_token
        API-->>C: 200 { accessToken, expiresIn }<br/>Set-Cookie: new refreshToken
    end
```

### Logout

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant ID as Identity Service
    participant DB as PostgreSQL

    C->>API: POST /api/v1/auth/logout<br/>Authorization: Bearer {access}<br/>Cookie: refreshToken
    API->>ID: logout(refresh_token, user_id)
    ID->>DB: REVOKE refresh token
    API-->>C: 204 No Content<br/>Set-Cookie: refreshToken=; Max-Age=0
```

### Password Reset

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant ID as Identity Service
    participant DB as PostgreSQL
    participant Email as Email Service (async)

    C->>API: POST /api/v1/auth/forgot-password<br/>{ email }
    API->>ID: initiate_reset(email)
    ID->>DB: Create reset token (hash, 1h expiry)
    ID->>Email: Queue reset email (async)
    API-->>C: 202 Accepted (always — no email enumeration)

    Note over C,Email: User clicks link with reset token

    C->>API: POST /api/v1/auth/reset-password<br/>{ token, newPassword }
    API->>ID: complete_reset(token, newPassword)
    ID->>DB: Validate token, update password hash
    ID->>DB: Revoke ALL refresh tokens for user
    API-->>C: 200 { message: "Password updated" }
```

### Microsoft Entra ID (Phase 3 — Roadmap)

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant Entra as Microsoft Entra ID
    participant DB as PostgreSQL

    C->>API: GET /api/v1/auth/entra/login
    API-->>C: 302 Redirect to Entra authorize URL
    C->>Entra: Authenticate (MFA via conditional access)
    Entra-->>C: 302 Redirect with authorization code
    C->>API: GET /api/v1/auth/entra/callback?code=...
    API->>Entra: Exchange code for ID token
    API->>DB: Map Entra OID → LexFlow user (JIT create if first login)
    API->>API: Issue LexFlow JWT + refresh token
    API-->>C: 200 { accessToken } + refresh cookie
```

---

## Endpoints

### POST `/auth/login`

Authenticate with email and password.

**Request:**

```json
{
  "email": "attorney@firm.com",
  "password": "SecurePassword123!"
}
```

**Response (200):**

```json
{
  "data": {
    "accessToken": "eyJhbGciOiJSUzI1NiIs...",
    "tokenType": "Bearer",
    "expiresIn": 900
  },
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-07-06T08:00:00Z"
  }
}
```

**Response headers:**

```http
Set-Cookie: refreshToken=<opaque>; HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth; Max-Age=604800
```

### POST `/auth/refresh`

Exchange refresh cookie for new access token. Requires refresh cookie; access token optional.

**Response (200):** Same shape as login (new access token + rotated refresh cookie).

### POST `/auth/logout`

Revoke current refresh token. Requires valid access token.

**Response:** `204 No Content`

### POST `/auth/forgot-password`

Initiate password reset. Always returns `202 Accepted` regardless of whether email exists.

**Request:**

```json
{
  "email": "attorney@firm.com"
}
```

### POST `/auth/reset-password`

Complete password reset with token from email link.

**Request:**

```json
{
  "token": "reset-token-from-email",
  "newPassword": "NewSecurePassword456!"
}
```

---

## Access Token Structure (JWT)

```json
{
  "sub": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "firmId": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
  "email": "attorney@firm.com",
  "roles": ["Attorney"],
  "iat": 1717660800,
  "exp": 1717661700,
  "jti": "token-uuid-for-revocation-blocklist"
}
```

| Claim | Description |
|-------|-------------|
| `sub` | User UUID |
| `firmId` | Firm tenant UUID |
| `email` | User email (display only — not authoritative for auth) |
| `roles` | Role names for UX hints only — **permissions resolved server-side** |
| `jti` | Token ID for optional blocklist on logout/revocation |
| `iat` / `exp` | Issued at / expiry (Unix timestamp) |

### Cryptographic Properties

| Property | Value |
|----------|-------|
| Algorithm | RS256 (asymmetric) |
| Signing key | AWS Secrets Manager; rotated quarterly |
| Verification | Public key distributed to API instances at startup |
| Clock skew tolerance | 30 seconds |

---

## Session Management

| Control | Implementation |
|---------|----------------|
| Concurrent sessions | Allowed (multiple devices) |
| Session revocation | Admin action or password change revokes all refresh tokens |
| Idle timeout | Frontend prompts re-auth after 30 minutes inactivity |
| Absolute timeout | Refresh token expires after 7 days regardless of activity |
| Brute force protection | 5 failed attempts → account locked 15 minutes |
| Password policy | Min 12 chars, complexity requirements, bcrypt cost 12 |
| MFA (Phase 1–2) | Optional TOTP (Google Authenticator / Authy) |

---

## Authenticated Request Format

All protected endpoints require:

```http
GET /api/v1/cases HTTP/1.1
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
X-Correlation-Id: 550e8400-e29b-41d4-a716-446655440000
```

Missing or expired access token → **401 Unauthorized**  
Valid token but insufficient permission → **403 Forbidden** or **404** (matter walls)

---

## Best Practices

1. **Store access tokens in memory only** — not localStorage or sessionStorage (XSS risk).
2. **Use httpOnly cookies for refresh tokens** — JavaScript cannot read them.
3. **Implement silent refresh** in the frontend before access token expiry (e.g., at 14 minutes).
4. **Revoke all sessions on password change** — prevents stolen refresh token reuse.
5. **Never log tokens** — structured logs must redact `Authorization` headers.
6. **Validate JWT on every request** — no "trust the frontend" shortcuts.
7. **Use short access token lifetime** (15 min) to limit exposure if leaked.

---

## Tradeoffs

| Decision | Benefit | Cost |
|----------|---------|------|
| JWT access + refresh (not server sessions) | Stateless API scaling, SSR-friendly | Refresh rotation complexity |
| Permissions not in JWT | Immediate permission changes without re-login | DB/Redis lookup every request |
| RS256 asymmetric | Public key verification without shared secret | Key rotation ceremony required |
| Refresh in httpOnly cookie | XSS-resistant refresh | Cross-domain cookie config for subdomains |
| Email/password first | Unblocks Phase 1 without Entra dependency | Firm must manage password policy initially |
| 202 on forgot-password | Prevents email enumeration | Less immediate UX feedback |

---

## Future Improvements

| Phase | Enhancement |
|-------|-------------|
| Phase 2 | Optional TOTP MFA enrollment API (`POST /auth/mfa/enroll`) |
| Phase 3 | Microsoft Entra ID OIDC (`/auth/entra/*`) |
| Phase 3 | Entra security group → LexFlow role mapping |
| Phase 3+ | Firm admin can enforce Entra-only (disable password login) |
| Phase 4 | FIDO2/WebAuthn hardware key support |
| Phase 4 | OAuth 2.0 device flow for CLI tools |

---

## References

- [authorization-rbac.md](./authorization-rbac.md) — Post-authentication permission checks
- [rest-standards.md](./rest-standards.md) — Request headers and error format
- [error-handling.md](./error-handling.md) — 401/403 responses
- [../08-security/authentication-authorization.md](../authentication-authorization.md) — Full auth architecture
- [../08-security/security-architecture.md](../security-architecture.md) — Threat model
- [ADR-005](../13-decisions/005-jwt-authentication.md) — JWT + refresh token decision
- [RFC 7519 — JSON Web Token](https://datatracker.ietf.org/doc/html/rfc7519)
- [OAuth 2.0 Bearer Token Usage (RFC 6750)](https://datatracker.ietf.org/doc/html/rfc6750)
