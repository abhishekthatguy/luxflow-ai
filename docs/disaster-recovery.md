# Disaster Recovery & High Availability

**LexFlow AI** — HA, Backup, Failover  
**Version:** 1.0  
**Status:** Draft — Pre-Implementation  
**Last Updated:** 2026-07-06

---

## 1. Objectives

| Metric | Target |
|--------|--------|
| **Availability** | 99.9% (8.76 hours downtime/year) |
| **RPO** (Recovery Point Objective) | ≤ 15 minutes |
| **RTO** (Recovery Time Objective) | ≤ 4 hours |
| **Data durability** | 99.999999999% (S3 + RDS) |

---

## 2. High Availability Design

### 2.1 Component HA Matrix

| Component | HA Strategy | Failure Impact |
|-----------|-------------|----------------|
| CloudFront | Global edge — inherently HA | None — automatic failover |
| ALB | Multi-AZ, health-checked targets | Automatic — routes to healthy targets |
| ECS Fargate (web, api) | Min 2 tasks across 2 AZs | Automatic — ALB removes unhealthy tasks |
| ECS Fargate (worker) | Min 2 tasks across 2 AZs | Queue backlog until new tasks start (~60s) |
| ECS Fargate (n8n) | Min 1 task, auto-restart | Workflow executions pause until restart |
| RDS PostgreSQL | Multi-AZ synchronous replication | Automatic failover (~60-120s) |
| ElastiCache Redis | Cluster mode, 2 shards × 2 replicas | Automatic failover per shard |
| Amazon MQ (RabbitMQ) | Active/standby broker | Automatic failover (~30s) |
| S3 | 99.99% availability, cross-region replication | Transparent |

### 2.2 Single Points of Failure Mitigation

| SPOF | Mitigation |
|------|------------|
| Single AZ | All services span ≥ 2 AZs |
| Database | Multi-AZ RDS with automatic failover |
| n8n (single instance) | Acceptable — workflows are async and retry on failure; Phase 3 adds n8n HA |
| Secrets Manager | AWS-managed HA across AZs |
| NAT Gateway | One per AZ (not shared) |

---

## 3. Backup Strategy

### 3.1 Database (RDS PostgreSQL)

| Backup Type | Frequency | Retention | Recovery |
|-------------|-----------|-----------|----------|
| Automated snapshots | Daily | 35 days | Restore to new instance |
| Transaction logs | Continuous | 35 days | Point-in-time recovery (PITR) to 5-min granularity |
| Manual pre-deploy snapshot | Before each production deploy | 7 days | Rollback reference |
| Cross-region snapshot copy | Daily | 35 days | DR region restore |

### 3.2 Object Storage (S3)

| Control | Setting |
|---------|---------|
| Versioning | Enabled |
| Cross-region replication | us-east-1 → us-west-2 |
| Lifecycle — current versions | Indefinite |
| Lifecycle — non-current versions | Standard-IA after 90 days, Glacier after 365 days |
| MFA Delete | Enabled on production bucket |

### 3.3 Message Broker (RabbitMQ)

| Control | Setting |
|---------|---------|
| Durable queues | All queues durable |
| Message persistence | Persistent delivery mode |
| Broker backup | Amazon MQ automatic daily backup, 7-day retention |

### 3.4 Configuration & Code

| Asset | Backup |
|-------|--------|
| Terraform state | S3 with versioning + DynamoDB lock |
| Docker images | ECR with immutable tags |
| n8n workflows | Git repository (source of truth) |
| Secrets | Secrets Manager with automatic rotation |

---

## 4. Disaster Recovery Plan

### 4.1 Failure Scenarios

| Scenario | RTO | Procedure |
|----------|-----|-----------|
| Single ECS task failure | 0 (automatic) | ALB health check removes task; ECS launches replacement |
| Single AZ failure | ~2 min | Remaining AZ serves traffic; ECS scales in surviving AZ |
| RDS primary failure | ~2 min | Multi-AZ automatic failover to standby |
| Full region failure (us-east-1) | ~4 hours | Manual DR failover to us-west-2 |
| Data corruption | ~1 hour | PITR to point before corruption |
| Ransomware / security breach | ~4 hours | Restore from clean cross-region snapshot; rotate all secrets |

### 4.2 Region Failover Procedure (Manual — Phase 3 Automation)

```
1. Confirm primary region is unavailable (Route 53 health checks)
2. Promote RDS cross-region read replica to standalone (us-west-2)
3. Update Terraform to deploy ECS services in us-west-2
4. Update Route 53 DNS to point to us-west-2 ALB
5. Verify health checks pass
6. Notify firm IT and users
7. Monitor for 24 hours before considering failback
```

### 4.3 Failback Procedure

```
1. Restore primary region infrastructure via Terraform
2. Re-establish RDS replication (west → east)
3. Sync any delta data
4. Schedule maintenance window
5. Switch DNS back to primary region
6. Re-establish cross-region replication (east → west)
```

---

## 5. Recovery Testing

| Test | Frequency | Scope |
|------|-----------|-------|
| RDS PITR restore | Quarterly | Restore to staging, verify data integrity |
| ECS task kill | Monthly (automated) | Verify ALB failover and auto-scaling |
| Full DR failover | Annually | Complete region failover in staging |
| Backup integrity check | Monthly | Verify S3 object checksums, RDS snapshot restore |
| n8n workflow recovery | Quarterly | Kill n8n task mid-execution, verify retry |

---

## 6. Zero-Downtime Deployment

Deployments never require downtime:

1. **Database migrations:** Backward-compatible migrations only (add columns, not remove). Destructive changes use expand-contract pattern across two deploys.
2. **API deployment:** Rolling update — new tasks start, pass health checks, old tasks drain.
3. **Frontend deployment:** CloudFront cache invalidation after new ECS tasks are healthy.
4. **Worker deployment:** Rolling update — in-flight tasks complete on old workers before shutdown.

---

## 7. Related Documents

- [deployment-architecture.md](./deployment-architecture.md)
- [observability.md](./observability.md)
- [database-architecture.md](./database-architecture.md)
- [compliance-data-governance.md](./compliance-data-governance.md)
