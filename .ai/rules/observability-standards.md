# Observability Standards — LexFlow AI

**Applies to:** All deployable containers, CI, on-call runbooks  
**Docs:** `docs/11-observability/`

---

## Purpose

Three pillars — **logs, metrics, traces** — are mandatory for every container. Observability must be correlation-linked, PII-safe, and actionable with runbooks.

---

## Three Pillars

| Pillar | Tool | Storage |
|--------|------|---------|
| Logs | structlog → Fluent Bit | CloudWatch Logs (90d) → S3 (7y) |
| Metrics | OpenTelemetry → ADOT | CloudWatch Metrics |
| Traces | OpenTelemetry → X-Ray | AWS X-Ray |

---

## Core Principles

| Principle | Detail |
|-----------|--------|
| Correlation everywhere | `correlationId` in logs; W3C `traceparent` in traces |
| PII-safe by default | Redaction processor before emit |
| Actionable alerts | Every P1–P4 alert has runbook + owner |
| Tenant-aware | `firmId`, `caseId`, `userId` labels where applicable |
| Error-biased sampling | 10% traces in prod; 100% on errors and staging |

---

## Distributed Tracing

### Propagation

```
Browser → ALB → FastAPI → RabbitMQ → Worker → n8n → Callback
         traceparent header throughout
```

| Component | Instrumentation |
|-----------|-----------------|
| FastAPI | OTel auto-instrument + manual spans on use cases |
| Celery | Extract trace context from AMQP headers |
| Next.js | Browser OTel SDK; forward headers on BFF |
| n8n | Log `correlationId`; trace ID in webhook payload |

### Span Naming

| Pattern | Example |
|---------|---------|
| `{service}.{operation}` | `api.create_case`, `worker.process_ai_job` |
| HTTP | `HTTP GET /api/v1/cases/{id}` |

**Ref:** `docs/11-observability/distributed-tracing.md`

---

## Metrics

### Required Application Metrics

| Metric | Type | Labels |
|--------|------|--------|
| `http_requests_total` | Counter | `method`, `path`, `status` |
| `http_request_duration_seconds` | Histogram | `method`, `path` |
| `celery_tasks_total` | Counter | `task_name`, `status` |
| `ai_tokens_total` | Counter | `firm_id`, `provider`, `model` |
| `workflow_executions_total` | Counter | `slug`, `status` |
| `matter_wall_denies_total` | Counter | `firm_id`, `endpoint` |

### RED Method (API Services)

| Metric | Description |
|--------|-------------|
| **Rate** | Requests per second |
| **Errors** | 5xx rate |
| **Duration** | p50, p95, p99 latency |

**Ref:** `docs/11-observability/metrics-alerting.md`

---

## Alert Severity

| Severity | Response | Example |
|----------|----------|---------|
| P1 | 15 min — page on-call | API down, DB unreachable |
| P2 | 1 hour | Worker queue backlog > threshold |
| P3 | Next business day | Elevated 5xx on single endpoint |
| P4 | Informational | Deprecation usage spike |

| Rule | Detail |
|------|--------|
| Every alert has runbook | `docs/11-observability/runbooks.md` |
| No alert without owner | Team + escalation path |
| Flapping alerts tuned | Adjust thresholds, not silence |

---

## Dashboards

| Dashboard | Audience | Key Panels |
|-----------|----------|------------|
| Operational | SRE | Request rate, error rate, latency, queue depth |
| Business | Product/Legal Ops | Cases created, AI jobs, workflow completions |
| Security | Security team | Matter wall denies, auth failures, rate limits |

**Ref:** `docs/11-observability/dashboards.md`

---

## Do / Don't

| Do | Don't |
|----|-------|
| Export metrics from shared OTel helpers | Invent per-service metric formats |
| Include `firmId` label on business metrics | Include client names in labels |
| Sample traces; always record errors | Trace 100% of health checks |
| Link runbook in alert annotation | Page without remediation steps |
| Monitor outbox lag | Ignore event publishing delays |

---

## Async Job Observability

| Signal | What to Track |
|--------|---------------|
| Queue depth | RabbitMQ per-queue message count |
| Job duration | p95 `process_ai_job` latency |
| DLQ size | Failed jobs awaiting review |
| Token usage | Per-firm AI cost dashboard |

---

## n8n Observability

| Signal | Method |
|--------|--------|
| Execution success/fail | Callback status to FastAPI → metric |
| Duration | `executionId` span from trigger to callback |
| Correlation | `correlationId` in all webhook payloads |

n8n UI logs are **supplemental** — FastAPI execution record is system of record.

---

## On-Call Runbooks

Before adding new failure modes, add runbook section:

1. **Symptoms** — what alert fires
2. **Impact** — user-facing effect
3. **Diagnosis** — CloudWatch queries, trace lookup by `correlationId`
4. **Mitigation** — steps to restore service
5. **Escalation** — when to page security/compliance

**Ref:** `docs/11-observability/runbooks.md`, `docs/14-playbooks/incident-triage.md`

---

## Observability PR Checklist

- [ ] New endpoints have HTTP metrics (auto via middleware)
- [ ] New worker tasks have task metrics
- [ ] Spans on critical path operations
- [ ] `correlationId` propagated across new integrations
- [ ] No PII in metrics labels or span attributes
- [ ] Alert + runbook if new failure mode is user-visible
- [ ] Dashboard panel if new business-critical metric

---

## References

- [docs/11-observability/README.md](../../docs/11-observability/README.md)
- [docs/11-observability/distributed-tracing.md](../../docs/11-observability/distributed-tracing.md)
- [docs/11-observability/metrics-alerting.md](../../docs/11-observability/metrics-alerting.md)
- [docs/03-architecture/cross-cutting-concerns.md](../../docs/03-architecture/cross-cutting-concerns.md)
- [logging-standards.md](./logging-standards.md)
