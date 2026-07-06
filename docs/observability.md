# Observability

**LexFlow AI** — Logging, Tracing, Metrics & Alerting  
**Version:** 1.0  
**Status:** Draft — Pre-Implementation  
**Last Updated:** 2026-07-06

---

## 1. Overview

LexFlow AI implements the three pillars of observability — **logs**, **metrics**, and **traces** — with structured JSON logging, OpenTelemetry distributed tracing, and CloudWatch metrics/alarms.

---

## 2. Structured Logging

### 2.1 Log Format

All services emit JSON logs:

```json
{
  "timestamp": "2026-07-06T08:00:00.123Z",
  "level": "INFO",
  "service": "api",
  "message": "Case created successfully",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000",
  "userId": "user-uuid",
  "firmId": "firm-uuid",
  "caseId": "case-uuid",
  "requestId": "req-uuid",
  "duration_ms": 45,
  "http": {
    "method": "POST",
    "path": "/api/v1/cases",
    "status": 201
  }
}
```

### 2.2 Log Levels

| Level | Usage |
|-------|-------|
| DEBUG | Development only — verbose internal state |
| INFO | Normal operations — requests, events, workflow steps |
| WARNING | Recoverable issues — retry triggered, rate limit approached |
| ERROR | Failures requiring attention — unhandled exceptions, external API failures |
| CRITICAL | System-level failures — database unreachable, auth system down |

### 2.3 PII Redaction

Logs automatically redact:
- Passwords, tokens, API keys
- SSN, credit card numbers
- Full document content (log document ID only)
- LLM prompt/response content (log token counts and model only)

Redaction applied via structured logging processor before emission.

### 2.4 Log Destinations

| Destination | Retention | Purpose |
|-------------|-----------|---------|
| CloudWatch Logs | 90 days | Operational debugging |
| S3 (via subscription filter) | 7 years | Compliance archive |
| CloudWatch Insights | — | Ad-hoc querying |

---

## 3. Distributed Tracing

### 3.1 OpenTelemetry Setup

```
Frontend (traceparent header)
  → ALB (X-Amzn-Trace-Id)
  → FastAPI (OTel SDK — auto-instrument FastAPI, SQLAlchemy, httpx)
  → RabbitMQ (trace context in message headers)
  → Celery Worker (OTel SDK — extract context from message)
  → n8n callback (correlationId propagated)
  → FastAPI internal endpoint
```

### 3.2 Trace Context Propagation

| Header | Purpose |
|--------|---------|
| `traceparent` | W3C Trace Context |
| `X-Correlation-Id` | Business correlation (case, workflow) |
| `X-Request-Id` | Single request identifier |

Every span includes: `service.name`, `correlationId`, `userId`, `firmId`, `caseId` (when applicable).

### 3.3 Backend

- **Collector:** AWS Distro for OpenTelemetry (ADOT) sidecar on ECS tasks
- **Export:** AWS X-Ray + CloudWatch Application Signals
- **Sampling:** 10% in production (100% for errors); 100% in staging/dev

---

## 4. Metrics

### 4.1 Application Metrics

| Metric | Type | Labels |
|--------|------|--------|
| `http_requests_total` | Counter | method, path, status, service |
| `http_request_duration_seconds` | Histogram | method, path, service |
| `workflow_executions_total` | Counter | workflow_slug, status |
| `workflow_execution_duration_seconds` | Histogram | workflow_slug |
| `ai_requests_total` | Counter | provider, model, summary_type |
| `ai_tokens_total` | Counter | provider, model, direction (input/output) |
| `ai_request_duration_seconds` | Histogram | provider, model |
| `queue_depth` | Gauge | queue_name |
| `outbox_pending_events` | Gauge | — |
| `active_users` | Gauge | — |
| `document_uploads_total` | Counter | document_type, status |

### 4.2 Infrastructure Metrics (CloudWatch)

| Metric | Source | Alert |
|--------|--------|-------|
| ECS CPU/Memory utilization | Container Insights | > 80% for 5 min |
| RDS CPU/Connections/Storage | RDS Enhanced Monitoring | CPU > 80%, storage < 20% free |
| Redis CPU/Memory/Evictions | ElastiCache | Memory > 80% |
| RabbitMQ queue depth | Amazon MQ | > 1,000 messages |
| ALB 5xx count | ALB | > 10 in 5 min |
| ALB target response time | ALB | p99 > 2 seconds |

---

## 5. Alerting

### 5.1 Alert Severity

| Severity | Response Time | Channel |
|----------|--------------|---------|
| P1 — Critical | 15 minutes | PagerDuty + Teams |
| P2 — High | 1 hour | Teams + Email |
| P3 — Medium | 4 hours | Email |
| P4 — Low | Next business day | Dashboard only |

### 5.2 Alert Rules

| Alert | Severity | Condition |
|-------|----------|-----------|
| API down | P1 | Health check failing > 2 min |
| Database unreachable | P1 | Connection errors > 5 in 1 min |
| Error rate spike | P1 | 5xx rate > 5% for 5 min |
| DLQ messages | P2 | Any DLQ depth > 0 |
| Workflow failure rate | P2 | Failed > 10% in 15 min |
| AI budget threshold | P2 | 80% of monthly budget consumed |
| Disk space low | P2 | RDS storage < 20% free |
| High latency | P3 | p99 response time > 3s for 10 min |
| Outbox lag | P3 | Pending events > 30 seconds old |
| Certificate expiry | P3 | SSL cert expires in < 30 days |

---

## 6. Dashboards

### 6.1 Operational Dashboard

- Request rate, error rate, latency (p50, p95, p99)
- Active ECS tasks per service
- Queue depths
- Workflow execution success/failure rate
- Database connection pool utilization

### 6.2 Business Dashboard

- Cases created/closed per day
- Documents uploaded per day
- AI summaries generated/approved per day
- Active users per day
- Workflow executions per day
- LLM token usage and cost

### 6.3 Security Dashboard

- Failed login attempts
- Matter wall denial count
- API rate limit hits
- Unusual access patterns (geo, time)

---

## 7. Related Documents

- [deployment-architecture.md](./deployment-architecture.md)
- [disaster-recovery.md](./disaster-recovery.md)
- [security-architecture.md](./security-architecture.md)
- [event-driven-architecture.md](./event-driven-architecture.md)
