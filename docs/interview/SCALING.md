# LexFlow AI — Scaling Guide

**Targets (from architecture docs):** 1,000+ concurrent users · 50,000 workflow executions/month · millions of documents · 99.9% availability

---

## Scale Tiers

### Tier 1 — 10 Users (Local / PoC)

| Component | Configuration |
|-----------|---------------|
| **Deploy** | Docker Compose single host |
| **API** | 1 uvicorn worker |
| **Workers** | 1 Celery worker (all queues) |
| **PostgreSQL** | Single pgvector container |
| **Redis** | Single instance |
| **RabbitMQ** | Single node |
| **MinIO** | Single node |
| **Cost** | ~$0 local; ~$200/mo small EC2 |

**Bottleneck:** None — demo and dev only.

---

### Tier 2 — 100 Users (Pilot Firm)

| Component | Configuration |
|-----------|---------------|
| **Web** | 2× ECS Fargate (0.5 vCPU, 1 GB) |
| **API** | 2× ECS (1 vCPU, 2 GB) |
| **Workers** | 2× ECS (2 vCPU, 4 GB) |
| **PostgreSQL** | RDS db.r6g.large Single-AZ |
| **Redis** | ElastiCache cache.t3.medium |
| **RabbitMQ** | Amazon MQ mq.t3.micro |
| **S3** | Single region, SSE-S3 |
| **ALB** | 1 ALB, HTTP/2 |
| **Observability** | CloudWatch + Tempo sidecar |

**Horizontal scaling:** Add API tasks behind ALB (stateless).  
**Worker scaling:** Fixed 2 workers; monitor queue depth.  
**Estimated load:** ~10 req/s peak API, ~500 docs/day.

---

### Tier 3 — 1,000 Concurrent Users

| Component | Configuration |
|-----------|---------------|
| **Web** | 4–6× Fargate + CloudFront CDN for static assets |
| **API** | 8–10× Fargate (2 vCPU); autoscale on CPU > 70% |
| **Workers** | 4–8× Fargate; **autoscale on RabbitMQ queue depth** |
| **PostgreSQL** | RDS db.r6g.2xlarge Multi-AZ; connection pooler (PgBouncer) |
| **Read replica** | 1× for reporting + audit export |
| **Redis** | ElastiCache cluster mode (3 shards) |
| **RabbitMQ** | Amazon MQ cluster (3 nodes) |
| **S3** | Versioning + lifecycle (IA after 90 days) |
| **Edge** | CloudFront + WAF |

**Partitioning:** Audit logs partitioned by month (PostgreSQL declarative partitions).  
**Caching:** Case list cached 60s per user (Redis); invalidate on mutation.  
**Estimated load:** ~500 req/s peak, ~5k docs/day, ~2k AI jobs/day.

---

### Tier 4 — 10,000 Users (Large Firm)

| Component | Configuration |
|-----------|---------------|
| **API** | 20–40 pods; regional ALB |
| **Workers** | 20+ workers; **separate pools**: OCR, AI, outbox, workflow |
| **PostgreSQL** | db.r6g.4xlarge Multi-AZ + 2 read replicas |
| **Partitioning** | `audit.audit_logs` by month; archive to S3 Glacier |
| **S3** | Transfer Acceleration for large uploads |
| **LLM** | Per-firm TPM quotas; dedicated Azure deployment |
| **n8n** | Dedicated ECS cluster (4+ tasks) |

**PgBouncer:** 500 API connections → 50 DB connections.  
**CQRS light:** Reporting queries only on replicas.

---

### Tier 5 — 50,000 Concurrent Workflow Executions / Month

| Component | Strategy |
|-----------|----------|
| **Outbox relay** | Batch 100 events; parallel relay workers |
| **n8n** | Horizontal n8n workers; workflow sharding by firm |
| **Idempotency** | `Idempotency-Key` header on all triggers |
| **Rate limits** | Per-firm workflow throttle (Redis token bucket) |
| **DLQ** | Automated replay with max age 24h |

**Math:** 50k/month ≈ 1,700/day ≈ 1.2/min average — peak 10× during business hours → autoscale workers on queue depth > 500.

---

## Component Scaling Patterns

### Horizontal Scaling (Stateless)

| Service | Scale trigger | Max practical |
|---------|---------------|---------------|
| Next.js | CPU, request count | 20+ tasks |
| FastAPI | CPU, latency p95 | 40+ tasks |
| Celery | Queue depth | 50+ workers |

### RabbitMQ Clustering

- **3-node quorum queues** (Amazon MQ)
- Mirror classic queues deprecated — use quorum for Celery broker in prod
- **Prefetch:** `worker_prefetch_multiplier=1` for fair dispatch
- **Priority queues:** AI jobs lower priority than OCR confirm path

### Celery Worker Pools

```python
# Production queue routing
CELERY_TASK_ROUTES = {
    "document_tasks.*": {"queue": "documents"},
    "ai_tasks.*": {"queue": "ai"},
    "workflow_tasks.*": {"queue": "workflows"},
    "outbox_tasks.*": {"queue": "outbox"},
}
```

Separate autoscale policies per queue.

### Redis Clustering

| Use | Scale approach |
|-----|----------------|
| Rate limiting | Hash slot by IP — cluster mode |
| Celery results | TTL 24h; avoid large payloads |
| Cache | Eviction policy `allkeys-lru` |

### PostgreSQL Read Replicas

| Query type | Target |
|------------|--------|
| Case list, audit export | Replica |
| Mutations, confirm upload | Primary |
| AI context load | Primary (consistency) |

**Lag tolerance:** < 5s for lists; 0 for writes.

### S3 Lifecycle

| Age | Action |
|-----|--------|
| 0–90 days | Standard |
| 90–365 days | Infrequent Access |
| > 7 years | Glacier Deep Archive (policy-driven) |

### Autoscaling (ECS)

```yaml
# API service
TargetTrackingScaling:
  - CPUUtilization: 70%
  - ALBRequestCountPerTarget: 1000/min

# Worker service
CustomMetric:
  - RabbitMQ queue depth > 500 for 3 min → +2 tasks
```

### Load Balancing

- **ALB** → API (path `/api/*`)
- **ALB** → Web (path `/*`)
- **Sticky sessions:** Not required (JWT stateless)
- **Health check:** `/health` every 15s

### CloudFront

- Static assets (`/_next/static/*`)
- Marketing pages at edge
- **Not cached:** `/api/*`, authenticated dashboard

### AWS ECS (Production)

| Service | CPU | Memory | Count |
|---------|-----|--------|-------|
| web | 512 | 1024 | 4–6 |
| api | 1024 | 2048 | 8–40 |
| worker | 2048 | 4096 | 4–50 |
| n8n | 1024 | 2048 | 2–4 |

**Deploy:** Blue/green via CodeDeploy; migration task before traffic shift.

---

## Future Kubernetes Migration

| Trigger | Action |
|---------|--------|
| Multi-cloud requirement | EKS with same container images |
| Custom autoscale (KEDA) | Scale workers on RabbitMQ metric |
| Service mesh | Istio for mTLS internal — only if compliance mandates |

**Migration path:** ECS task definitions → K8s Deployments; Amazon MQ unchanged; IRSA for S3/RDS.

**Tradeoff:** K8s ops burden — defer until > 3 platform engineers or multi-region K8s mandate.

---

## Capacity Planning Checklist

- [ ] Load test: `k6 run tests/load/cases-read.js` at 100 VUs
- [ ] Document upload: 50 concurrent presigned PUTs
- [ ] AI job backlog: 500 queued summaries
- [ ] Workflow burst: 200 triggers in 1 min
- [ ] Verify p95 API < 500ms, error rate < 1%

---

## Related Docs

- [Failure Scenarios](./FAILURE_SCENARIOS.md)
- [Architecture Walkthrough](./ARCHITECTURE_WALKTHROUGH.md)
- [Load Testing](../10-testing/load-testing.md)
