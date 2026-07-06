# LexFlow AI — Production Failure Scenarios (30)

**Purpose:** Demonstrate production maturity — detection, recovery, user impact, observability.

**Legend:** ✅ Implemented · 🔶 Partial/stub · 📋 Planned (prod)

---

## Infrastructure Failures

### 1. RabbitMQ Unavailable

| Aspect | Detail |
|--------|--------|
| **Detection** | Celery broker connection error; health check fails; queue publish timeout |
| **Recovery** | API returns 503 on async operations; Amazon MQ Multi-AZ failover (prod); restart broker pod |
| **Retries** | Celery reconnect with exponential backoff |
| **DLQ** | Messages not acked return to queue; after max retries → dead letter exchange |
| **User sees** | "Processing temporarily unavailable — try again" on 202 endpoints |
| **Logs** | `ERROR broker_connection_retry` with correlationId |
| **Alerts** | P1: queue unreachable > 2 min |

### 2. Redis Unavailable

| Aspect | Detail |
|--------|--------|
| **Detection** | Cache get/set throws; rate limit check fails |
| **Recovery** | Rate limit: fail open vs closed — **LexFlow fails closed (503)** on auth rate limit path; cache miss falls through to DB |
| **Retries** | Redis client reconnect |
| **User sees** | Login may succeed if rate limit skipped in degraded mode (configurable) |
| **Logs** | `redis_connection_error` |
| **Alerts** | P2: Redis CPU > 80% or evictions spike |

### 3. PostgreSQL Unavailable

| Aspect | Detail |
|--------|--------|
| **Detection** | SQLAlchemy pool timeout; `/health` deep check fails |
| **Recovery** | RDS Multi-AZ automatic failover (60–120s); connection pool retry |
| **Retries** | 3 connection attempts with backoff |
| **User sees** | 503 Service Unavailable |
| **Logs** | `db_connection_failed` — no query params logged |
| **Alerts** | P1: RDS failover event |

### 4. PostgreSQL Read Replica Lag

| Aspect | Detail |
|--------|--------|
| **Detection** | Replica lag metric > 30s |
| **Recovery** | Route critical reads to primary; pause reporting queries |
| **User sees** | Stale list views (rare); strong reads always primary |
| **Alerts** | P2: lag > 60s |

### 5. MinIO / S3 Unavailable

| Aspect | Detail |
|--------|--------|
| **Detection** | Presign/boto3 ClientError; HEAD fails on confirm |
| **Recovery** | Retry 3x; multi-region replication (prod CRRA) |
| **User sees** | Upload initiate fails or confirm returns 409 |
| **Logs** | `s3_operation_failed` with operation, key (no body) |
| **Alerts** | P1: S3 5xx rate > 1% |

---

## Worker & Queue Failures

### 6. Celery Worker Crash Mid-Task

| Aspect | Detail |
|--------|--------|
| **Detection** | Task ack late — message requeued |
| **Recovery** | New worker picks up task; idempotent OCR upsert |
| **Retries** | Celery max_retries=3 |
| **User sees** | Job status `running` longer; eventual `complete` or `failed` |
| **Logs** | Worker stderr + task failure traceback (no PII) |

### 7. Duplicate Celery Messages

| Aspect | Detail |
|--------|--------|
| **Detection** | Same documentId OCR twice |
| **Recovery** | Idempotent UPDATE WHERE ocr_status != complete |
| **User sees** | No duplicate documents |
| **Logs** | `ocr_already_complete` debug |

### 8. Dead Letter Queue Depth > 0

| Aspect | Detail |
|--------|--------|
| **Detection** | RabbitMQ DLQ metric |
| **Recovery** | Manual replay after root cause fix; ops runbook |
| **User sees** | Stuck jobs → `failed` status |
| **Alerts** | P1: DLQ > 0 |

### 9. Long-Running Workflow (> 30 min)

| Aspect | Detail |
|--------|--------|
| **Detection** | Execution `running` beyond SLA |
| **Recovery** | Timeout task marks `failed`; n8n cancel execution |
| **User sees** | Workflow failed — retry button |
| **Alerts** | P2: p95 workflow duration |

### 10. Worker Pool Exhausted

| Aspect | Detail |
|--------|--------|
| **Detection** | Queue depth growing; worker CPU 100% |
| **Recovery** | ECS autoscale workers on queue depth |
| **User sees** | Increased async latency |
| **Alerts** | P2: queue depth > 1000 for 5 min |

---

## AI & External Service Failures

### 11. Azure OpenAI Timeout

| Aspect | Detail |
|--------|--------|
| **Detection** | HTTP timeout 60s; circuit breaker open |
| **Recovery** | Retry 2x; fallback to queued retry job |
| **User sees** | Job `failed` — "Summary generation failed" |
| **Logs** | `llm_request_timeout` with model, token estimate |
| **Alerts** | P2: LLM error rate > 5% |

### 12. OpenAI Rate Limit (429)

| Aspect | Detail |
|--------|--------|
| **Detection** | Provider 429 response |
| **Recovery** | Exponential backoff + jitter; per-firm token bucket |
| **User sees** | Delayed summary |
| **Alerts** | P2: approaching TPM limit |

### 13. n8n Unavailable

| Aspect | Detail |
|--------|--------|
| **Detection** | Outbox relay HTTP connection refused |
| **Recovery** | Outbox retry 5x → status `failed`; alert ops |
| **User sees** | Workflow execution `failed`; core case data intact |
| **Logs** | `n8n_webhook_failed` |

### 14. n8n Callback HMAC Invalid

| Aspect | Detail |
|--------|--------|
| **Detection** | Signature mismatch on `/api/internal/n8n` |
| **Recovery** | Reject 401; log security event |
| **User sees** | Workflow step stuck — manual reconcile |

### 15. LLM Returns Hallucinated Citations

| Aspect | Detail |
|--------|--------|
| **Detection** | Human review (HITL) — attorney rejects |
| **Recovery** | `POST /ai/summaries/{id}/reject` |
| **User sees** | Rejection reason captured |
| **Mitigation** | RAG with pgvector (Phase 2) |

---

## Document Pipeline Failures

### 16. Virus Scan Failed (Infected File)

| Aspect | Detail |
|--------|--------|
| **Detection** | ClamAV returns infected (prod); stub always clean (local) |
| **Recovery** | Confirm returns 409; object quarantined/deleted |
| **User sees** | "Virus scan failed — upload rejected" |
| **Logs** | `virus_scan_failed` with s3Key |

### 17. OCR Failed (Corrupt PDF)

| Aspect | Detail |
|--------|--------|
| **Detection** | pypdf exception |
| **Recovery** | `ocr_status=failed`; optional admin re-process |
| **User sees** | Document shows OCR failed badge |
| **Logs** | `ocr_task_failed` |

### 18. Large Document Upload (> 500 MB)

| Aspect | Detail |
|--------|--------|
| **Detection** | Size validated at initiate |
| **Recovery** | Multipart presigned upload (prod) |
| **User sees** | 422 if exceeds firm limit |
| **Mitigation** | Per-firm upload quota in settings |

### 19. Presigned URL Expired

| Aspect | Detail |
|--------|--------|
| **Detection** | S3 403 on PUT |
| **Recovery** | Client re-initiates upload |
| **User sees** | Upload error — retry |

### 20. Checksum Mismatch on Confirm

| Aspect | Detail |
|--------|--------|
| **Detection** | SHA-256 compare fails |
| **Recovery** | 409 Conflict; object orphaned — lifecycle cleanup |
| **User sees** | "Checksum does not match" |

---

## Auth & Security Failures

### 21. Expired JWT

| Aspect | Detail |
|--------|--------|
| **Detection** | `exp` claim past |
| **Recovery** | Client refresh token flow |
| **User sees** | Redirect to login if refresh fails |

### 22. Revoked User Mid-Session

| Aspect | Detail |
|--------|--------|
| **Detection** | User status != active on next request |
| **Recovery** | 401; token blocklist (prod) |
| **User sees** | Forced logout |

### 23. Rate Limit Exceeded (Login Brute Force)

| Aspect | Detail |
|--------|--------|
| **Detection** | Redis counter > 10/min per IP ✅ |
| **Recovery** | 429 for 60s window |
| **User sees** | "Too many requests" |
| **Logs** | `rate_limit_exceeded` scope=login |

### 24. Matter Wall Violation Attempt

| Aspect | Detail |
|--------|--------|
| **Detection** | Participant query empty |
| **Recovery** | 404 response (no leak) |
| **Logs** | Security audit `matter_wall.deny` |

### 25. Prompt Injection in Document Text

| Aspect | Detail |
|--------|--------|
| **Detection** | LLM guardrails + human review |
| **Recovery** | Summary rejected; incident logged |
| **Mitigation** | System prompt isolation; output filtering |

---

## Application & Data Failures

### 26. Outbox Relay Stuck

| Aspect | Detail |
|--------|--------|
| **Detection** | `outbox_events` pending > 5 min |
| **Recovery** | Relay cron; manual replay script |
| **Alerts** | P2: outbox backlog |

### 27. Database Migration Failure Mid-Deploy

| Aspect | Detail |
|--------|--------|
| **Detection** | Alembic exit code != 0 |
| **Recovery** | Abort deploy; rollback migration; restore snapshot |
| **User sees** | Old version still serving |

### 28. Partial Transaction Failure

| Aspect | Detail |
|--------|--------|
| **Detection** | SQLAlchemy rollback |
| **Recovery** | No partial state — ACID |
| **User sees** | 500 or domain error |

### 29. Notification Delivery Failed (Email)

| Aspect | Detail |
|--------|--------|
| **Detection** | SES bounce/complaint |
| **Recovery** | Status `failed`; retry 3x; in-app still delivered |
| **User sees** | In-app notification works |

### 30. Grafana / Tempo Unavailable

| Aspect | Detail |
|--------|--------|
| **Detection** | Trace export failure |
| **Recovery** | Buffers drop; API continues; async export retry |
| **User sees** | No impact |
| **Mitigation** | CloudWatch fallback metrics |

---

## DLQ & Retry Summary

| Component | Default Retries | DLQ |
|-----------|-----------------|-----|
| Celery OCR/AI | 3 | RabbitMQ DLX |
| Outbox relay | 5 | `outbox_events.status=failed` |
| n8n node | 3 (configurable) | Error workflow branch |
| SES email | 3 | Bounce handler |

---

## Related Docs

- [Operations Runbook](../operations/RUNBOOK.md)
- [E2E Flow](../demo/E2E_FLOW.md)
- [Security Review](./SECURITY.md)
