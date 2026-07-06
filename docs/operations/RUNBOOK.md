# LexFlow AI — Operations Runbook

**Audience:** Platform Engineering, On-Call  
**Environment:** Local Docker Compose + AWS ECS Production  
**SLA Target:** 99.9% availability · P1 response 15 min · P2 response 1 hr

---

## Service Startup

### Local (Development)

```bash
cp .env.example .env
make dev                    # docker compose up -d --build
make migrate                # alembic upgrade head
make seed && make seed-sprint4 && make seed-sprint5
make verify-platform        # health + integration smoke
```

**Expected:** All containers `healthy` within 2 min.

| Service | Port | Health |
|---------|------|--------|
| API | 8000 | `GET /health` |
| Web | 3000 | HTTP 200 |
| PostgreSQL | 5432 | `pg_isready` |
| Redis | 6379 | `PING` |
| RabbitMQ | 5672, 15672 | Management UI |
| MinIO | 9000, 9001 | Console |
| Grafana | 3001 | Login admin/admin |
| n8n | 5678 (internal) | Container health |

### Production (ECS)

1. Verify Secrets Manager values current
2. Run **migration task** (one-off ECS task)
3. Deploy API + worker (blue/green)
4. Deploy web
5. Run smoke: `verify-sprint5.sh` against staging URL
6. Monitor 15 min (see Post-Deploy)

---

## Service Shutdown

### Local

```bash
make down                   # docker compose down
make down && docker volume prune  # full reset (destructive)
```

### Production

1. Scale workers to 0 (drain queues first)
2. Scale API to 0
3. Web last (maintenance page via CloudFront)
4. **Never** stop RDS during rolling ops

---

## Backup

| Asset | Method | Frequency | Retention |
|-------|--------|-----------|-----------|
| PostgreSQL | RDS automated snapshots | Daily | 35 days |
| PostgreSQL | Manual snapshot pre-deploy | Per deploy | 7 days |
| S3 documents | Cross-region replication | Continuous | Policy-driven |
| Redis | Not backed up (ephemeral) | — | — |
| RabbitMQ | Definition export | Weekly | 90 days |
| Secrets | Secrets Manager versioning | On change | 30 versions |

```bash
# Manual RDS snapshot (AWS CLI)
aws rds create-db-snapshot \
  --db-instance-identifier lexflow-prod \
  --db-snapshot-identifier lexflow-pre-deploy-$(date +%Y%m%d)
```

---

## Restore

### Database Point-in-Time Recovery

1. Identify recovery timestamp (RPO ≤ 15 min)
2. Restore to **new** RDS instance from snapshot/PITR
3. Update Secrets Manager `DATABASE_URL`
4. Run `alembic upgrade head` if needed
5. Smoke test on restored instance before cutover
6. Update ECS task env → restart services

### S3 Object Restore

```bash
aws s3 cp s3://lexflow-docs-backup/firms/{firmId}/... s3://lexflow-docs/firms/{firmId}/...
```

---

## Incident Response

| Severity | Definition | Response |
|----------|------------|----------|
| **P1** | Platform down; data breach suspected | Page on-call; war room in 15 min |
| **P2** | Degraded (AI down, queue backlog) | Ticket + Slack; fix in 4 hr |
| **P3** | Minor (single user, UI bug) | Next business day |

**Steps:**
1. Acknowledge alert
2. Check Grafana/CloudWatch dashboards
3. Correlate `correlationId` across API + worker logs
4. Mitigate (scale, rollback, disable feature flag)
5. Post-incident review within 48 hr

---

## Queue Stuck

**Symptoms:** RabbitMQ depth growing; jobs `running` forever

```bash
# Local — inspect queues
open http://localhost:15672
docker compose logs worker --tail 100

# Recovery
docker compose restart worker
# Purge only after DLQ export (destructive):
# docker compose exec rabbitmq rabbitmqctl purge_queue celery
```

**Production:** Scale workers +2; if poison message → move to DLQ → fix → replay.

---

## Redis Full / Eviction Storm

**Symptoms:** Rate limit failures; cache misses; high `evicted_keys`

```bash
redis-cli INFO memory
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

**Recovery:** Scale ElastiCache node; flush non-critical keys (`ratelimit:*` TTL already set).

---

## Database Restore Verification

Monthly drill:

1. Restore latest snapshot to `lexflow-dr-test`
2. Run `pytest tests/test_auth.py tests/test_cases.py`
3. Document RTO achieved
4. Delete test instance

---

## Rotate JWT Secret

1. Generate new secret in Secrets Manager
2. Deploy API with **dual validation** window (old + new) — 24 hr
3. Force refresh all sessions (optional: invalidate refresh tokens)
4. Remove old secret
5. Verify login/logout flows

---

## Rotate Secrets (General)

| Secret | Rotation |
|--------|----------|
| DB password | RDS rotate + rolling ECS restart |
| S3 | IAM role preferred over keys |
| n8n webhook | Update n8n + API simultaneously |
| Azure OpenAI | Azure portal key regen |

---

## Deploy

```bash
# CI pipeline (see .github/workflows/deploy-staging.yml)
1. lint + test + Trivy
2. build & push ECR images
3. manual approval gate (production)
4. migration task
5. ECS service update
6. post-deploy smoke
```

**Zero-downtime:** Rolling update min healthy 100%, max 200%.

---

## Rollback

1. **ECS:** Revert task definition to previous revision
2. **Database:** If migration irreversible — restore snapshot (last resort)
3. **Verify:** `/health` + sprint5 smoke
4. **Communicate:** Status page update

```bash
aws ecs update-service --cluster lexflow-prod \
  --service api --task-definition lexflow-api:PREVIOUS_REV
```

---

## Restart Workers

```bash
# Local
docker compose restart worker

# ECS
aws ecs update-service --cluster lexflow-prod \
  --service worker --force-new-deployment
```

Drain: set `worker_concurrency` finish in flight tasks (~5 min).

---

## Clear Queues (Emergency Only)

⚠️ **Data loss risk** — export messages first.

```bash
rabbitmqadmin get queue=celery count=1000 > dlq-backup.json
rabbitmqctl purge_queue celery
```

Replay from outbox table for domain events.

---

## Disaster Recovery

| Scenario | RTO | RPO | Procedure |
|----------|-----|-----|-----------|
| AZ failure | 4 hr | 15 min | RDS Multi-AZ failover automatic |
| Region loss | 24 hr | 1 hr | Restore snapshot in DR region; Route 53 failover |
| Ransomware | 48 hr | 24 hr | Immutable S3 backups; clean rebuild |

---

## Health Checks

| Endpoint | Expected | Interval |
|----------|----------|----------|
| `GET /health` | `{"status":"ok"}` | 15s ALB |
| Deep health 📋 | DB + Redis + broker ping | 60s |
| Worker heartbeat | Celery inspect ping | 60s |

---

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.9% (43 min/month downtime) |
| API p95 latency | < 500 ms |
| OCR job p95 | < 120 s |
| AI summary p95 | < 90 s |
| Support P1 ack | 15 min |

---

## Monitoring Dashboards

| Dashboard | URL (local) | Metrics |
|-----------|-------------|---------|
| Grafana | `:3001` | Traces, RED metrics |
| RabbitMQ | `:15672` | Queue depth, publish rate |
| CloudWatch 📋 | AWS Console | ECS CPU, RDS, ALB 5xx |

**Key alarms:**
- API 5xx > 5% for 5 min → P1
- DLQ depth > 0 → P1
- RDS CPU > 80% → P2
- Queue depth > 1000 → P2

---

## Related Docs

- [Go-Live Checklist](../14-playbooks/go-live-checklist.md)
- [Failure Scenarios](../interview/FAILURE_SCENARIOS.md)
- [Deploy Production](../14-playbooks/deploy-production.md)
