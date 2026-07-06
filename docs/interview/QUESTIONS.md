# LexFlow AI — Interview Questions (100)

**Audience:** Principal Engineer · Staff Architect · Security Reviewer  
**Format:** Question · **Expected senior answer** · Common mistake · Follow-up

---

## Architecture (6)

**Q1.** Why is Case the aggregate root?  
**A:** Documents, AI outputs, workflows, and audit entries attach to a matter; matter walls scope all access.  
**Mistake:** Treating Client as root — clients span many matters with different walls.  
**Follow-up:** How do bounded contexts integrate without shared tables?

**Q2.** Why modular monolith over microservices Day 1?  
**A:** Lower ops burden; schema-separated contexts allow future extraction; single transaction + outbox simpler.  
**Mistake:** "Microservices are always more scalable."  
**Follow-up:** When would you split Document context out?

**Q3.** Explain the transactional outbox pattern here.  
**A:** Domain event written in same DB transaction as state change; relay publishes async — no dual-write.  
**Mistake:** Publishing to RabbitMQ inside request handler before commit.  
**Follow-up:** What if relay publishes but DB rolled back?

**Q4.** Why 404 instead of 403 for matter walls?  
**A:** Prevents enumeration — attacker cannot infer case existence (ADR-007).  
**Mistake:** "403 is more RESTful."  
**Follow-up:** How do firm-wide roles bypass walls?

**Q5.** Where does business logic live vs n8n?  
**A:** FastAPI services own decisions; n8n orchestrates HTTP, notifications, schedules (ADR-002).  
**Mistake:** SQL nodes in n8n.  
**Follow-up:** Example workflow that belongs in n8n vs API.

**Q6.** How does hexagonal architecture appear in code?  
**A:** Ports (`S3StorageClient`, `LlmProvider`); adapters (MinIO, Azure); services depend on abstractions.  
**Mistake:** Confusing folder structure with true ports.  
**Follow-up:** How do you test without real S3?

---

## FastAPI (6)

**Q7.** Why async SQLAlchemy?  
**A:** Non-blocking I/O under concurrent requests; single worker handles more connections.  
**Mistake:** Running CPU-bound OCR in async route.  
**Follow-up:** When would you use sync workers?

**Q8.** How is validation enforced?  
**A:** Pydantic v2 on request bodies; 422 Problem+JSON with field errors.  
**Mistake:** Manual dict parsing in routes.  
**Follow-up:** How validate cross-field rules (checksum vs file size)?

**Q9.** Explain dependency injection for `CurrentUser`.  
**A:** JWT decoded in `get_current_user`; roles loaded; injected into every protected route.  
**Mistake:** Parsing JWT in each route manually.  
**Follow-up:** How refresh tokens work?

**Q10.** Why Problem+JSON errors?  
**A:** Consistent machine-readable errors; `requestId` in meta for support correlation.  
**Mistake:** Returning stack traces to clients.  
**Follow-up:** How map domain exceptions to HTTP status?

**Q11.** How would you version the API?  
**A:** URL prefix `/api/v1`; breaking changes → v2; deprecation headers.  
**Mistake:** Breaking clients without version bump.  
**Follow-up:** How handle mobile app lag on upgrades?

**Q12.** Presigned upload flow — why 3 steps?  
**A:** Initiate metadata → direct S3 PUT → confirm integrity; API never holds bytes.  
**Mistake:** Multipart through API gateway.  
**Follow-up:** What happens if confirm never called?

---

## Next.js (5)

**Q13.** Why App Router over Pages Router?  
**A:** Layouts, RSC where beneficial, colocated routes; marketing static + dashboard client.  
**Mistake:** Making entire app client-side.  
**Follow-up:** Which pages are static vs dynamic?

**Q14.** How does auth work in the browser?  
**A:** JWT in localStorage (dev); `apiFetch` attaches Bearer; AuthProvider context.  
**Mistake:** Storing refresh token without rotation strategy.  
**Follow-up:** httpOnly cookie migration for prod?

**Q15.** SEO on landing page?  
**A:** Static generation, metadata API, JSON-LD, sitemap.xml, robots.txt.  
**Mistake:** Client-only render for marketing.  
**Follow-up:** How prevent indexing `/cases`?

**Q16.** Shared types with API?  
**A:** `@lexflow/shared` package; camelCase envelope matches API.  
**Mistake:** Duplicated interfaces in web and API.  
**Follow-up:** OpenAPI codegen vs hand-maintained?

**Q17.** Command palette implementation?  
**A:** Global keydown ⌘K; debounced search API; accessible dialog.  
**Mistake:** No keyboard nav / focus trap.  
**Follow-up:** Extend to documents and clients?

---

## Python (5)

**Q18.** Why Python for the backend?  
**A:** AI ecosystem, team skill, FastAPI async, Celery integration.  
**Mistake:** "Python too slow" without measuring — hot path is I/O bound.  
**Follow-up:** GIL impact on OCR?

**Q19.** How structure services vs routes?  
**A:** Thin routers; fat services with business logic; models for persistence.  
**Mistake:** 500-line route handlers.  
**Follow-up:** When extract domain events?

**Q20.** Type checking strategy?  
**A:** mypy on `src/`; Pydantic runtime validation; strict in CI.  
**Mistake:** `# type: ignore` everywhere.  
**Follow-up:** How type async SQLAlchemy results?

**Q21.** Password storage?  
**A:** bcrypt via passlib; never log passwords.  
**Mistake:** SHA-256 without salt.  
**Follow-up:** Entra ID migration path?

**Q22.** Testing pyramid here?  
**A:** Unit (services, auth), integration (API), E2E Playwright, k6 load.  
**Mistake:** Only E2E tests.  
**Follow-up:** How mock Celery in unit tests?

---

## Celery (6)

**Q23.** Why Celery over background threads?  
**A:** Process isolation, scale independent workers, durable queue, retry semantics.  
**Mistake:** `asyncio.create_task` for OCR in API process.  
**Follow-up:** Worker concurrency settings?

**Q24.** How ensure idempotent OCR task?  
**A:** Check `ocr_status` before processing; upsert text.  
**Mistake:** Blind insert duplicates.  
**Follow-up:** Duplicate message from RabbitMQ?

**Q25.** Task retry configuration?  
**A:** max_retries=3, exponential backoff; permanent fail → job status failed.  
**Mistake:** Infinite retry on bad PDF.  
**Follow-up:** Dead letter queue handling?

**Q26.** Separate queues for AI vs OCR?  
**A:** Yes — prevent AI backlog from starving OCR; route by task name.  
**Mistake:** Single queue for all tasks.  
**Follow-up:** Priority for deadline workflows?

**Q27.** How propagate correlationId to worker?  
**A:** Pass in task kwargs; bind to log context and OTel span.  
**Mistake:** Lost trace across async boundary.  
**Follow-up:** Celery beat for scheduled jobs?

**Q28.** Celery result backend use?  
**A:** Redis stores task results; job polling API reads status.  
**Mistake:** Storing large OCR text in result backend.  
**Follow-up:** Result expiry TTL?

---

## RabbitMQ (6)

**Q29.** Why RabbitMQ over SQS for Celery?  
**A:** Local dev parity; priority queues; mature Celery broker; Amazon MQ in prod.  
**Mistake:** "SQS is always better."  
**Follow-up:** When switch to SQS?

**Q30.** At-least-once delivery implications?  
**A:** Tasks must be idempotent; use acks_late.  
**Mistake:** Assuming exactly-once.  
**Follow-up:** How detect poison messages?

**Q31.** Queue depth alerting threshold?  
**A:** P2 at 1000 for 5 min; P1 if growing while workers healthy.  
**Mistake:** No broker monitoring.  
**Follow-up:** Autoscale metric choice?

**Q32.** Quorum vs classic queues?  
**A:** Quorum for durability in RabbitMQ 3.8+ clusters.  
**Mistake:** Classic mirrored queues deprecated.  
**Follow-up:** Amazon MQ version?

**Q33.** What happens if broker down during API request?  
**A:** Return 503 on async enqueue; sync reads unaffected.  
**Mistake:** Silent task loss.  
**Follow-up:** Outbox vs direct publish?

**Q34.** Prefetch setting?  
**A:** prefetch_multiplier=1 for fair work distribution across workers.  
**Mistake:** High prefetch causing one worker hoarding.  
**Follow-up:** Worker pool per queue?

---

## Redis (5)

**Q35.** Redis use cases in LexFlow?  
**A:** Rate limiting, Celery results, cache (future sessions).  
**Mistake:** Primary data store in Redis.  
**Follow-up:** Eviction policy?

**Q36.** Rate limit fail-open or closed?  
**A:** Closed on auth — security over availability; cache can degrade.  
**Mistake:** Fail open on login rate limit.  
**Follow-up:** Sliding vs fixed window?

**Q37.** Redis cluster vs single node?  
**A:** Cluster at 1000+ users; hash tags for rate limit keys.  
**Mistake:** Single node prod SPOF.  
**Follow-up:** ElastiCache failover time?

**Q38.** What not to store in Redis?  
**A:** Document content, PII blobs, long-term audit.  
**Mistake:** Large values causing memory pressure.  
**Follow-up:** maxmemory-policy?

**Q39.** JWT blocklist in Redis?  
**A:** On logout/deactivate, set key `blocklist:{jti}` with TTL = token exp.  
**Mistake:** Stateless JWT with no revocation story.  
**Follow-up:** Scale of blocklist?

---

## PostgreSQL (6)

**Q40.** Why schema-per-bounded-context?  
**A:** Clear ownership; migration isolation; future service split.  
**Mistake:** Single public schema with 200 tables.  
**Follow-up:** Cross-schema FK rules?

**Q41.** Matter wall query pattern?  
**A:** EXISTS on case_participants OR firm-wide role bypass.  
**Mistake:** Filtering only in Python after fetch.  
**Follow-up:** Index strategy?

**Q42.** Audit log immutability?  
**A:** Application never UPDATE/DELETE; optional DB trigger; append-only.  
**Mistake:** Editable audit rows.  
**Follow-up:** Partitioning by month?

**Q43.** pgvector planned use?  
**A:** Document embeddings for case-scoped semantic search Phase 2.  
**Mistake:** Cross-firm vector index.  
**Follow-up:** Embedding model choice?

**Q44.** Connection pooling?  
**A:** SQLAlchemy async pool; PgBouncer in prod at scale.  
**Mistake:** Unbounded connections per API pod.  
**Follow-up:** Pool size formula?

**Q45.** Optimistic concurrency on cases?  
**A:** `version` column + If-Match header on PATCH.  
**Mistake:** Last-write-wins silently.  
**Follow-up:** 409 client handling?

---

## n8n (6)

**Q46.** Why n8n at all?  
**A:** Ops/legal teams configure notifications and integrations visually; fast iteration.  
**Mistake:** Hardcoding every workflow in Python.  
**Follow-up:** Promotion pipeline dev→prod?

**Q47.** Security boundary with n8n?  
**A:** Private network; HMAC callbacks; no DB credentials to n8n.  
**Mistake:** Public n8n instance.  
**Follow-up:** Pen test expectation?

**Q48.** Outbox vs direct webhook to n8n?  
**A:** Outbox ensures event not lost if n8n down at commit time.  
**Mistake:** Fire-and-forget HTTP in request thread.  
**Follow-up:** Retry count before failed status?

**Q49.** What workflows belong in n8n?  
**A:** Email, Teams, scheduled reminders, external HTTP — not business rules.  
**Mistake:** Case status transitions in n8n.  
**Follow-up:** Document-upload-notify example?

**Q50.** n8n callback endpoint purpose?  
**A:** Update workflow step status; close execution loop with audit.  
**Mistake:** Unauthenticated callback.  
**Follow-up:** Idempotent callback handling?

**Q51.** Compare n8n to Temporal.  
**A:** n8n lower learning curve for ops; Temporal better for code-first long sagas — deferred.  
**Mistake:** No orchestration tool evaluation.  
**Follow-up:** When adopt Temporal?

---

## OpenAI / LLM (5)

**Q52.** Why Azure OpenAI over direct OpenAI?  
**A:** Data residency, enterprise contract, private endpoint option (ADR-008).  
**Mistake:** Sending privileged docs to consumer API.  
**Follow-up:** Zero retention configuration?

**Q53.** HITL rationale?  
**A:** Bar rules, malpractice risk — AI is draft until attorney approves.  
**Mistake:** Auto-publish summary to client portal.  
**Follow-up:** Configurable per summary type?

**Q54.** Prompt injection mitigation?  
**A:** System prompt isolation, delimiter wrapping, human review, output schema.  
**Mistake:** "We'll fine-tune away injection."  
**Follow-up:** RAG citation verification?

**Q55.** Async AI job design?  
**A:** 202 + job ID; worker calls LLM; poll or websocket for status.  
**Mistake:** 60s synchronous HTTP to OpenAI.  
**Follow-up:** Token budget per firm?

**Q56.** Stub LLM in local dev?  
**A:** `LlmStubProvider` — deterministic output, no API cost, CI friendly.  
**Mistake:** Hitting prod LLM in tests.  
**Follow-up:** Contract tests against Azure?

---

## AWS (6)

**Q57.** Why ECS Fargate over EKS?  
**A:** Less k8s ops for small platform team; Fargate sufficient Phase 1.  
**Mistake:** EKS Day 1 without team capacity.  
**Follow-up:** K8s migration triggers?

**Q58.** RDS Multi-AZ failover?  
**A:** Automatic DNS flip; app pool reconnect; 60–120s blip.  
**Mistake:** Single-AZ prod.  
**Follow-up:** RPO/RTO numbers?

**Q59.** S3 presigned URL security?  
**A:** Short TTL, single-key scope, HTTPS only, IAM least privilege.  
**Mistake:** Public bucket policy.  
**Follow-up:** KMS vs SSE-S3?

**Q60.** CloudFront + WAF role?  
**A:** Edge caching static assets; WAF OWASP rules; DDoS protection.  
**Mistake:** ALB exposed without WAF.  
**Follow-up:** Rate limit at edge vs app?

**Q61.** Secrets Manager vs env vars?  
**A:** Rotation, audit, IAM access; env injected at task start.  
**Mistake:** Secrets in git or image layers.  
**Follow-up:** Rotation without downtime?

**Q62.** Amazon MQ vs self-hosted Rabbit?  
**A:** Managed patching, Multi-AZ; higher cost acceptable for enterprise.  
**Mistake:** Self-managed broker without HA.  
**Follow-up:** Cost at 50k workflows/mo?

---

## Security (7)

**Q63.** OWASP A01 in LexFlow?  
**A:** RBAC + matter walls + firm_id from token not body.  
**Mistake:** IDOR checks missing on document GET.  
**Follow-up:** Pen test scope?

**Q64.** How prevent cross-tenant data leak?  
**A:** Every query filters `firm_id`; JWT firm claim; integration tests.  
**Mistake:** Trusting client-supplied firmId.  
**Follow-up:** Row-level security in Postgres?

**Q65.** File upload attack surface?  
**A:** Size limits, MIME allowlist, virus scan, presigned scoped keys.  
**Mistake:** Unlimited upload to API.  
**Follow-up:** ZIP bomb handling?

**Q66.** Audit tampering prevention?  
**A:** Append-only app logic; restricted DB roles; optional read-only replica for compliance.  
**Mistake:** Admin can delete audit rows.  
**Follow-up:** WORM storage?

**Q67.** Login brute force?  
**A:** Redis rate limit 10/min/IP; optional CAPTCHA after threshold.  
**Mistake:** No auth rate limiting.  
**Follow-up:** Distributed attack from botnet?

**Q68.** LLM data retention?  
**A:** Azure enterprise zero retention; no training on firm data.  
**Mistake:** Consumer tier with training enabled.  
**Follow-up:** Subprocessor list for SOC 2?

**Q69.** n8n public exposure test?  
**A:** External port scan must fail; security requirement not bug.  
**Mistake:** n8n behind same ALB as web.  
**Follow-up:** VPN-only access pattern?

---

## Performance (6)

**Q70.** API p95 target?  
**A:** < 500ms; achieved by async I/O and offloading heavy work.  
**Mistake:** Optimizing before measuring.  
**Follow-up:** k6 baseline script location?

**Q71.** N+1 query prevention?  
**A:** selectinload for roles/participants; pagination always.  
**Mistake:** Loading all cases with all documents.  
**Follow-up:** Cursor vs offset pagination?

**Q72.** Document list performance?  
**A:** Index on case_id; paginate; don't return ocr_text in list.  
**Mistake:** Returning full OCR in list API.  
**Follow-up:** Full-text search index?

**Q73.** Caching case lists?  
**A:** Redis 60s per user; invalidate on mutation.  
**Mistake:** Cache without tenant key.  
**Follow-up:** Cache stampede?

**Q74.** Cold start on Fargate?  
**A:** Min tasks > 0; provisioned concurrency if needed.  
**Mistake:** Scale to zero API in prod.  
**Follow-up:** Startup probe tuning?

**Q75.** Large PDF OCR memory?  
**A:** Stream from S3; worker memory limits; page-by-page extract.  
**Mistake:** Load entire 500MB into RAM.  
**Follow-up:** Multipart upload threshold?

---

## Scaling (6)

**Q76.** First bottleneck at 1000 users?  
**A:** PostgreSQL write throughput and connection count.  
**Mistake:** "Just add API pods."  
**Follow-up:** PgBouncer sizing?

**Q77.** Worker autoscale signal?  
**A:** RabbitMQ queue depth custom metric → ECS scale out.  
**Mistake:** CPU-only autoscale on workers.  
**Follow-up:** Max worker cap?

**Q78.** Audit log at millions of rows?  
**A:** Monthly partitions; archive to S3; query replicas.  
**Mistake:** Single table unbounded.  
**Follow-up:** Compliance export job?

**Q79.** 50k workflows/month capacity?  
**A:** ~1.7k/day avg; peak 10×; dedicated n8n + outbox batch 100.  
**Mistake:** One n8n instance no HA.  
**Follow-up:** Per-firm throttle?

**Q80.** Read replica lag tolerance?  
**A:** Lists OK at 5s lag; writes and AI context always primary.  
**Mistake:** Read-your-writes on replica.  
**Follow-up:** Routing middleware?

**Q81.** Multi-region strategy?  
**A:** Phase 3 — DR region, S3 CRR, Route 53 failover; not Day 1.  
**Mistake:** Active-active without conflict resolution.  
**Follow-up:** Data residency requirements?

---

## Observability (5)

**Q82.** correlationId propagation?  
**A:** Middleware sets UUID; header echoed; passed to Celery kwargs; OTel span parent.  
**Mistake:** New UUID per hop.  
**Follow-up:** Frontend sends X-Correlation-ID?

**Q83.** PII in logs?  
**A:** Email/phone regex redaction in JsonFormatter; never log document body.  
**Mistake:** Logging full JWT payload.  
**Follow-up:** CloudWatch subscription filters?

**Q84.** Key dashboards?  
**A:** RED metrics (rate, errors, duration); queue depth; RDS CPU; LLM latency.  
**Mistake:** Only infrastructure metrics, no SLOs.  
**Follow-up:** SLO error budget?

**Q85.** Trace sampling at scale?  
**A:** Head-based 10% normal; 100% on errors; tail sampling in collector.  
**Mistake:** 100% trace retention cost explosion.  
**Follow-up:** Tempo vs X-Ray?

**Q86.** Alert fatigue prevention?  
**A:** P1 only for customer impact; DLQ and 5xx sustained; runbooks linked.  
**Mistake:** Alert on every single 500.  
**Follow-up:** On-call rotation?

---

## Testing (6)

**Q87.** Matter wall test strategy?  
**A:** API test: outsider gets 404 on case/documents; E2E Playwright journey.  
**Mistake:** Only testing happy path as admin.  
**Follow-up:** Property-based tests?

**Q88.** E2E vs unit balance?  
**A:** Unit for services; E2E for critical journeys; smoke scripts in CI.  
**Mistake:** Flaky E2E as only gate.  
**Follow-up:** Testcontainers for Postgres?

**Q89.** Load test thresholds?  
**A:** k6: p95 < 500ms, error < 1% at 100 VUs cases-read.  
**Mistake:** No load test before prod.  
**Follow-up:** Soak test duration?

**Q90.** CI pipeline gates?  
**A:** ruff, mypy, pytest, Trivy CRITICAL=0, docker smoke, Playwright E2E.  
**Mistake:** Skip security scan.  
**Follow-up:** Nightly vs PR E2E?

**Q91.** Mocking S3 in tests?  
**A:** MagicMock S3StorageClient; integration uses MinIO.  
**Mistake:** Hitting real AWS in unit tests.  
**Follow-up:** Localstack vs MinIO?

**Q92.** AI output regression tests?  
**A:** Stub LLM fixed output; assert schema and status transitions.  
**Mistake:** Non-deterministic LLM in CI.  
**Follow-up:** Golden file summaries?

---

## Deployment (5)

**Q93.** Zero-downtime deploy steps?  
**A:** Migration task → rolling ECS update → health check → drain old tasks.  
**Mistake:** Run migration after traffic on new code.  
**Follow-up:** Backward-compatible migrations?

**Q94.** Rollback procedure?  
**A:** Revert ECS task definition; DB rollback only if migration reversible else restore snapshot.  
**Mistake:** Roll forward only culture.  
**Follow-up:** Blue/green vs rolling?

**Q95.** Manual prod approval gate?  
**A:** GitHub environment protection; staging smoke pass required.  
**Mistake:** Auto-deploy main to prod.  
**Follow-up:** Who approvers?

**Q96.** Migration failure during deploy?  
**A:** Abort deploy; old tasks keep serving; fix migration forward.  
**Mistake:** Half-applied schema with new code.  
**Follow-up:** Expand-contract pattern?

**Q97.** Post-deploy monitoring window?  
**A:** 15 min elevated watch; 5xx, queue depth, error logs; go-live checklist.  
**Mistake:** Deploy Friday 5pm.  
**Follow-up:** Automated canary analysis?

---

## Index

| Section | Questions |
|---------|-----------|
| Architecture | Q1–Q6 |
| FastAPI | Q7–Q12 |
| Next.js | Q13–Q17 |
| Python | Q18–Q22 |
| Celery | Q23–Q28 |
| RabbitMQ | Q29–Q34 |
| Redis | Q35–Q39 |
| PostgreSQL | Q40–Q45 |
| n8n | Q46–Q51 |
| OpenAI | Q52–Q56 |
| AWS | Q57–Q62 |
| Security | Q63–Q69 |
| Performance | Q70–Q75 |
| Scaling | Q76–Q81 |
| Observability | Q82–Q86 |
| Testing | Q87–Q92 |
| Deployment | Q93–Q97 |

**Total: 97 core + 3 bonus rapid-fire:**

**Q98.** Three nines = how much downtime/month? **A:** ~43 minutes.  
**Q99.** Why bcrypt not AES for passwords? **A:** Passwords need slow hash, not encryption.  
**Q100.** Single most important control for legal AI? **A:** Human-in-the-loop before client/court exposure.

---

## Related Docs

- [Architecture Walkthrough](./ARCHITECTURE_WALKTHROUGH.md)
- [Demo Script](../demo/DEMO_SCRIPT.md)
- [Tradeoffs Discussion](../15-interview/tradeoffs-discussion.md)
