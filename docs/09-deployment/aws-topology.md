# AWS Topology

**LexFlow AI** — VPC, Compute, Data Layer & Edge Infrastructure  
**Version:** 1.0  
**Status:** Draft — Pre-Implementation  
**Last Updated:** 2026-07-06

---

## Purpose

This document defines the **AWS infrastructure topology** for LexFlow AI — VPC layout, subnet design, ECS Fargate services, managed data stores, edge delivery, and network security zones. It is the infrastructure companion to [../03-architecture/container-architecture.md](../03-architecture/container-architecture.md).

Primary region: **us-east-1**. DR standby: **us-west-2**. Target availability: **99.9%**.

---

## Scope

| In Scope | Out of Scope |
|----------|--------------|
| VPC, subnets, NAT, IGW, VPC endpoints | Terraform module variable definitions (see [terraform.md](./terraform.md)) |
| ECS Fargate cluster and service topology | Application business logic |
| RDS, ElastiCache, Amazon MQ, S3 configuration | Column-level database schema |
| ALB, CloudFront, Route 53, WAF | Firm DNS registrar configuration |
| Security group rules and network zones | Penetration test procedures |
| Multi-AZ and cross-region replication layout | Cost modeling |

---

## Responsibilities

| Role | Responsibility |
|------|----------------|
| **DevOps / SRE** | Provision and maintain all AWS resources via Terraform |
| **Security Architect** | Approve security group rules, WAF policies, VPC endpoint scope |
| **DBA / SRE** | RDS instance sizing, parameter groups, backup windows |
| **Network Engineer** | VPN/bastion access for n8n admin; Route 53 failover |
| **On-Call Engineer** | Respond to CloudWatch alarms; execute AZ/region failover |

---

## Architecture

### C4 Deployment Diagram

```mermaid
C4Deployment
    title Deployment Diagram — LexFlow AI (us-east-1 Primary)

    Deployment_Node(aws, "AWS Cloud", "us-east-1") {
        Deployment_Node(vpc, "VPC 10.0.0.0/16", "Multi-AZ") {
            Deployment_Node(public, "Public Subnets", "10.0.1.0/24, 10.0.2.0/24") {
                Container(alb, "Public ALB", "Application Load Balancer", "HTTPS termination, health checks")
                Container(nat, "NAT Gateway", "Per-AZ", "Outbound internet for private subnets")
            }
            Deployment_Node(private, "Private Subnets", "10.0.10.0/24, 10.0.11.0/24") {
                Container(ecs_web, "web-service", "ECS Fargate", "Next.js — min 2 tasks")
                Container(ecs_api, "api-service", "ECS Fargate", "FastAPI — min 2 tasks")
                Container(ecs_worker, "worker-service", "ECS Fargate", "Celery — scale on queue")
                Container(ecs_n8n, "n8n-service", "ECS Fargate", "Private orchestrator")
                Container(ialb, "Internal ALB", "Private ALB", "n8n ingress only")
            }
            Deployment_Node(data, "Data Subnets", "10.0.20.0/24, 10.0.21.0/24") {
                ContainerDb(rds, "PostgreSQL", "RDS Multi-AZ", "db.r6g.xlarge + pgvector")
                ContainerDb(redis, "Redis", "ElastiCache Cluster", "2 shards × 2 replicas")
                Container(mq, "RabbitMQ", "Amazon MQ", "Active/standby broker")
            }
        }
        Deployment_Node(edge, "Edge Services") {
            Container(cf, "CloudFront", "CDN + WAF", "Static assets, DDoS protection")
            Container(r53, "Route 53", "DNS", "Health-checked failover")
            ContainerDb(s3, "S3", "SSE-KMS", "Documents, artifacts, log archive")
            Container(ecr, "ECR", "Container Registry", "Immutable image tags")
            Container(sm, "Secrets Manager", "Secrets", "DB creds, API keys, JWT keys")
        }
    }

    Rel(r53, cf, "DNS")
    Rel(cf, alb, "Origin")
    Rel(alb, ecs_web, "HTTPS")
    Rel(alb, ecs_api, "HTTPS")
    Rel(ecs_api, rds, "SQL/TLS")
    Rel(ecs_api, redis, "TLS")
    Rel(ecs_api, mq, "AMQP/TLS")
    Rel(ecs_api, s3, "Presigned URLs")
    Rel(mq, ecs_worker, "AMQP/TLS")
    Rel(ecs_worker, rds, "SQL/TLS")
    Rel(ecs_worker, s3, "HTTPS")
    Rel(ecs_worker, ialb, "HTTP")
    Rel(ialb, ecs_n8n, "HTTP")
    Rel(ecs_n8n, ecs_api, "HMAC callback")
```

### Full AWS Topology

```mermaid
flowchart TB
    subgraph Internet["Public Internet"]
        USERS["Firm Users"]
        EXT["External APIs<br/>MS365, LLM, Court, DMS"]
    end

    subgraph Global["Global Edge"]
        R53["Route 53<br/>Health Checks"]
        CF["CloudFront<br/>+ AWS WAF"]
        ACM_CF["ACM Cert<br/>(us-east-1)"]
    end

    subgraph VPC["VPC — 10.0.0.0/16 — us-east-1"]
        subgraph PubA["Public Subnet AZ-a — 10.0.1.0/24"]
            NAT_A["NAT Gateway"]
            ALB["Public ALB"]
        end
        subgraph PubB["Public Subnet AZ-b — 10.0.2.0/24"]
            NAT_B["NAT Gateway"]
        end

        subgraph PrivA["Private Subnet AZ-a — 10.0.10.0/24"]
            WEB_A["web-service"]
            API_A["api-service"]
            WRK_A["worker-service"]
            N8N_A["n8n-service"]
            IALB["Internal ALB"]
        end

        subgraph PrivB["Private Subnet AZ-b — 10.0.11.0/24"]
            WEB_B["web-service"]
            API_B["api-service"]
            WRK_B["worker-service"]
        end

        subgraph DataA["Data Subnet AZ-a — 10.0.20.0/24"]
            RDS_P["RDS Primary"]
            REDIS["ElastiCache<br/>Redis Cluster"]
            MQ["Amazon MQ<br/>Active Broker"]
        end

        subgraph DataB["Data Subnet AZ-b — 10.0.21.0/24"]
            RDS_S["RDS Standby"]
            MQ_S["Amazon MQ<br/>Standby Broker"]
        end

        subgraph Endpoints["VPC Endpoints"]
            VPCE_S3["S3 Gateway"]
            VPCE_SM["Secrets Manager"]
            VPCE_ECR["ECR API + DKR"]
            VPCE_LOGS["CloudWatch Logs"]
        end
    end

    subgraph Storage["Object Storage"]
        S3_DOC["S3 — Documents<br/>Versioned + SSE-KMS"]
        S3_LOG["S3 — Log Archive<br/>7-year retention"]
        S3_TF["S3 — Terraform State"]
    end

    subgraph DR["us-west-2 — DR Standby"]
        S3_DR["S3 CRR Replica"]
        SNAP_DR["RDS Cross-Region<br/>Snapshots"]
    end

    USERS --> R53 --> CF --> ALB
    ALB --> WEB_A & WEB_B & API_A & API_B
    API_A & API_B --> RDS_P
    API_A & API_B --> REDIS
    API_A & API_B --> MQ
    API_A & API_B --> S3_DOC
    MQ --> WRK_A & WRK_B
    WRK_A & WRK_B --> RDS_P
    WRK_A & WRK_B --> S3_DOC
    WRK_A & WRK_B --> IALB --> N8N_A
    N8N_A --> EXT
    N8N_A --> API_A
    WRK_A & WRK_B --> EXT
    RDS_P <-->|Sync replication| RDS_S
    MQ <-->|Active/standby| MQ_S
    S3_DOC -->|CRR| S3_DR
    RDS_P -->|Daily snapshot| SNAP_DR
```

---

## VPC Design

### CIDR Allocation

| Subnet Tier | CIDR | AZ | Purpose |
|-------------|------|-----|---------|
| Public — AZ-a | 10.0.1.0/24 | us-east-1a | ALB, NAT Gateway |
| Public — AZ-b | 10.0.2.0/24 | us-east-1b | NAT Gateway (redundant) |
| Private — AZ-a | 10.0.10.0/24 | us-east-1a | ECS Fargate tasks |
| Private — AZ-b | 10.0.11.0/24 | us-east-1b | ECS Fargate tasks |
| Data — AZ-a | 10.0.20.0/24 | us-east-1a | RDS primary, Redis, MQ active |
| Data — AZ-b | 10.0.21.0/24 | us-east-1b | RDS standby, MQ standby |

### Network Security Zones

```mermaid
flowchart LR
    subgraph Z0["Zone 0 — Internet"]
        U["Users"]
    end

    subgraph Z1["Zone 1 — DMZ / Edge"]
        WAF["WAF"]
        CF["CloudFront"]
        ALB_P["Public ALB"]
    end

    subgraph Z2["Zone 2 — Application"]
        WEB["Next.js"]
        API["FastAPI"]
        WRK["Celery Workers"]
    end

    subgraph Z3["Zone 3 — Orchestration"]
        IALB["Internal ALB"]
        N8N["n8n"]
    end

    subgraph Z4["Zone 4 — Data"]
        PG["PostgreSQL"]
        REDIS["Redis"]
        RMQ["RabbitMQ"]
        S3["S3"]
    end

    U --> WAF --> CF --> ALB_P
    ALB_P --> WEB & API
    API --> Z4
    WRK --> Z4
    WRK --> IALB --> N8N
    N8N -.->|"No public ingress"| X["✗ Internet"]

    style Z3 fill:#fff3cd
    style Z4 fill:#d1ecf1
```

See [../08-security/network-security.md](../08-security/network-security.md) for security group rule details.

---

## ECS Fargate Services

### Service Matrix

| Service | Image | Min Tasks | Max Tasks | CPU | Memory | Port | Scale Trigger |
|---------|-------|-----------|-----------|-----|--------|------|---------------|
| `web` | Next.js | 2 | 10 | 512 (0.5 vCPU) | 1024 MB | 3000 | CPU > 70% or requests > 1,000/min |
| `api` | FastAPI | 2 | 20 | 1024 (1 vCPU) | 2048 MB | 8000 | CPU > 70% or p95 > 500ms |
| `worker` | Celery | 2 | 50 | 1024 (1 vCPU) | 2048 MB | — | RabbitMQ queue depth > 100 |
| `n8n` | n8n official | 1 | 2 | 512 (0.5 vCPU) | 1024 MB | 5678 | CPU > 80% |
| `outbox-publisher` | Celery Beat | 1 | 1 | 256 (0.25 vCPU) | 512 MB | — | — |
| `migration` | Alembic (one-off) | 0 | 1 | 512 | 1024 MB | — | Manual / CI trigger |

### ECS Task Placement

```mermaid
flowchart TB
    subgraph Cluster["ECS Fargate Cluster — lexflow-prod"]
        subgraph AZa["us-east-1a"]
            T1["web-1"]
            T2["api-1"]
            T3["worker-1"]
            T4["n8n-1"]
        end
        subgraph AZb["us-east-1b"]
            T5["web-2"]
            T6["api-2"]
            T7["worker-2"]
        end
    end

    ALB["Public ALB"] --> T1 & T5 & T2 & T6
    IALB["Internal ALB"] --> T4
    MQ["RabbitMQ"] --> T3 & T7
```

**Placement strategy:** `spread` across AZs for web, api, worker. n8n pinned to single AZ (Phase 1); Phase 3 adds HA with 2+ tasks.

### ECS Service Discovery

| Pattern | Implementation |
|---------|----------------|
| Public services | Registered as ALB target groups |
| n8n internal access | Internal ALB DNS name in private hosted zone |
| Inter-service (api ↔ worker) | RabbitMQ broker endpoint from Secrets Manager |
| Database | RDS endpoint via Secrets Manager; PgBouncer sidecar optional |

---

## Data Layer

### RDS PostgreSQL

| Setting | Production Value |
|---------|-----------------|
| Engine | PostgreSQL 16 + pgvector extension |
| Instance class | db.r6g.xlarge (initial) → db.r6g.2xlarge (Phase 2) |
| Storage | gp3, 500 GB initial, autoscaling to 2 TB |
| Multi-AZ | Enabled — synchronous standby |
| Encryption | AES-256 KMS |
| Backup retention | 35 days |
| Performance Insights | Enabled |
| Parameter group | `shared_preload_libraries = pg_stat_statements, vector` |

See [../05-database/retention-backup.md](../05-database/retention-backup.md) for backup and PITR configuration.

### ElastiCache Redis

| Setting | Production Value |
|---------|-----------------|
| Engine | Redis 7.x |
| Node type | cache.r6g.large |
| Topology | Cluster mode — 2 shards × 2 replicas |
| Encryption | At rest + in transit (TLS) |
| Use cases | Permission cache, rate limits, Celery result backend, distributed locks |
| Eviction policy | `allkeys-lru` |

### Amazon MQ (RabbitMQ)

| Setting | Production Value |
|---------|-----------------|
| Broker type | RabbitMQ 3.13 |
| Instance | mq.m5.large |
| Deployment | Active/standby (Multi-AZ) |
| Encryption | TLS in transit |
| Maintenance window | Sunday 04:00–05:00 UTC |
| Backup | Daily automatic, 7-day retention |

**Queue topology:** Domain event queues per bounded context; DLQ per primary queue. See [../03-architecture/event-driven-design.md](../03-architecture/event-driven-design.md).

### S3 Buckets

| Bucket | Purpose | Key Settings |
|--------|---------|--------------|
| `lexflow-{env}-documents` | Document binaries, exports | Versioning, SSE-KMS, CRR to us-west-2 |
| `lexflow-{env}-artifacts` | Build artifacts, n8n exports | Versioning, lifecycle 90 days |
| `lexflow-{env}-logs` | Compliance log archive | Lifecycle → Glacier after 90 days; 7-year retention |
| `lexflow-{env}-terraform-state` | Terraform remote state | Versioning, MFA delete (prod), DynamoDB lock |

---

## Edge Layer

### CloudFront + WAF

```mermaid
sequenceDiagram
    actor User
    participant R53 as Route 53
    participant CF as CloudFront + WAF
    participant ALB as Public ALB
    participant Web as Next.js
    participant S3 as S3 (static)

    User->>R53: DNS lookup app.lexflow.{domain}
    R53-->>User: CloudFront distribution
    User->>CF: HTTPS request
    CF->>CF: WAF rule evaluation
    alt Static asset (_next/static/*)
        CF->>S3: Origin fetch (OAC)
        S3-->>CF: Asset
    else Dynamic request
        CF->>ALB: Origin fetch
        ALB->>Web: Forward
        Web-->>User: SSR response
    end
    CF-->>User: Response (cached or fresh)
```

| Component | Configuration |
|-----------|--------------|
| CloudFront | HTTP/2 + HTTP/3; compress; cache static assets 1 year |
| WAF | AWS Managed Rules (Core, Known Bad Inputs); rate limit 2,000 req/5 min/IP |
| Origin | ALB (dynamic); S3 (static `_next/static`) |
| Certificate | ACM in us-east-1 (CloudFront requirement) |
| Geo restriction | None (US firm with remote workers) |

### Application Load Balancer

| ALB | Type | Listeners | Target Groups |
|-----|------|-----------|---------------|
| Public ALB | Internet-facing | HTTPS:443 → web:3000, api:8000 | `web-tg`, `api-tg` |
| Internal ALB | Internal | HTTP:5678 → n8n:5678 | `n8n-tg` |

| Health Check | Path | Interval | Healthy Threshold |
|--------------|------|----------|-------------------|
| web | `GET /api/health` | 30s | 2 |
| api | `GET /health` | 15s | 2 |
| n8n | `GET /healthz` | 30s | 2 |

**TLS policy:** `ELBSecurityPolicy-TLS13-1-2-2021-06` (TLS 1.2 minimum).

### Route 53

| Record | Type | Target | Failover |
|--------|------|--------|----------|
| `app.lexflow.{domain}` | A (alias) | CloudFront distribution | Primary: us-east-1 |
| `app-dr.lexflow.{domain}` | A (alias) | CloudFront (DR) | Secondary: us-west-2 |
| `internal.lexflow.{domain}` | Private zone | Internal ALB | VPC-only |

Health checks monitor ALB target group health; secondary record used during region failover. See [disaster-recovery.md](./disaster-recovery.md).

---

## VPC Endpoints

Private subnet tasks reach AWS services without traversing NAT:

| Endpoint | Type | Services |
|----------|------|----------|
| S3 | Gateway | Document upload/download |
| ECR (api + dkr) | Interface | Image pull |
| Secrets Manager | Interface | Secret retrieval at task start |
| CloudWatch Logs | Interface | Log shipping |
| SSM | Interface | ECS Exec (break-glass debugging) |

---

## Cross-Region DR Layout (us-west-2)

| Resource | DR State | Activation |
|----------|----------|------------|
| S3 documents | CRR replica — live | Automatic read during failover |
| RDS snapshots | Daily cross-region copy | Manual promote on failover |
| ECS cluster | Cold — Terraform module ready | `terraform apply` during DR |
| ElastiCache | Not replicated (cache rebuild) | Provision fresh cluster |
| Amazon MQ | Not replicated (durable queues drain) | Provision fresh broker; replay from outbox |
| CloudFront | Secondary distribution | DNS switch |
| ECR | Cross-region replication | Images available |

---

## Environment Sizing

| Resource | Dev | Staging | Production |
|----------|-----|---------|------------|
| ECS web min/max | 1/2 | 1/3 | 2/10 |
| ECS api min/max | 1/3 | 1/5 | 2/20 |
| ECS worker min/max | 1/5 | 1/10 | 2/50 |
| RDS instance | db.t4g.medium | db.r6g.large | db.r6g.xlarge |
| Redis shards | 1 | 1 | 2 |
| MQ instance | mq.t3.micro | mq.m5.large | mq.m5.large |

See [environment-strategy.md](./environment-strategy.md) for environment purpose and data policies.

---

## Monitoring Integration

All AWS resources emit metrics to CloudWatch. Key infrastructure alarms:

| Resource | Metric | Warning | Critical |
|----------|--------|---------|----------|
| ALB | UnHealthyHostCount | > 0 for 5 min | > 1 for 2 min |
| ECS | CPUUtilization | > 70% | > 85% |
| RDS | CPUUtilization | > 70% | > 85% |
| RDS | FreeStorageSpace | < 30% | < 15% |
| ElastiCache | DatabaseMemoryUsagePercentage | > 70% | > 85% |
| Amazon MQ | MessageCount | > 5,000 | > 20,000 |
| NAT Gateway | ErrorPortAllocation | > 0 | > 10/min |

See [../11-observability/alerting.md](../11-observability/alerting.md) for full alerting configuration.

---

## Best Practices

1. **One NAT Gateway per AZ** — Avoid cross-AZ NAT traffic charges and single-NAT SPOF.
2. **Data subnets have no internet route** — RDS, Redis, MQ accessible only from private subnets.
3. **n8n behind internal ALB only** — Security group denies all inbound from 0.0.0.0/0 on n8n tasks.
4. **PgBouncer between app tier and RDS** — Connection pooling; max 100 connections per API task.
5. **VPC endpoints for AWS APIs** — Reduce NAT costs and improve security posture.
6. **Immutable ECR tags** — Image tags are Git SHA; never overwrite `latest` in production.
7. **Separate KMS keys per environment** — Dev/staging/prod encryption key isolation.

---

## Tradeoffs

| Decision | Benefit | Cost |
|----------|---------|------|
| ECS Fargate over EC2 | No host patching; per-task billing | ~15% premium over EC2 reserved |
| Multi-AZ everything | 99.9% availability within region | 2× NAT Gateway, 2× data layer cost |
| Amazon MQ over SQS | Native DLQ, priority, topic routing | Higher cost; broker management |
| CloudFront for dynamic + static | Single edge entry; WAF integration | Cache invalidation on deploy |
| No Redis cross-region replication | Simpler DR; cache rebuild acceptable | Cold-cache latency spike on DR |
| n8n single instance (Phase 1) | Sufficient for 50K workflows/month | Brief automation pause on restart |

---

## Future Improvements

| Phase | Enhancement |
|-------|-------------|
| Phase 2 | RDS read replica for search and dashboard queries |
| Phase 2 | Dedicated worker pools per queue domain |
| Phase 3 | n8n HA — 2+ tasks behind internal ALB |
| Phase 3 | AWS Global Accelerator for edge optimization |
| Phase 4 | Multi-region active-passive with automated DNS failover |

---

## References

| Document | Description |
|----------|-------------|
| [../03-architecture/container-architecture.md](../03-architecture/container-architecture.md) | Container responsibilities and communication |
| [../03-architecture/nfr-requirements.md](../03-architecture/nfr-requirements.md) | Scale and availability targets |
| [terraform.md](./terraform.md) | Module structure provisioning this topology |
| [environment-strategy.md](./environment-strategy.md) | Per-environment sizing and isolation |
| [disaster-recovery.md](./disaster-recovery.md) | Failover and cross-region procedures |
| [../05-database/retention-backup.md](../05-database/retention-backup.md) | RDS backup configuration |
| [../08-security/network-security.md](../08-security/network-security.md) | Security groups and WAF rules |
| [../11-observability/](../11-observability/) | Metrics, logs, traces |
