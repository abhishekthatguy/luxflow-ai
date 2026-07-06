# ADR-006: Transactional Outbox for Event Publishing

**Status:** Accepted  
**Date:** 2026-07-06  
**Deciders:** Architecture Team

## Context

LexFlow AI uses domain events for cross-context communication (CaseCreated → trigger workflow, DocumentProcessed → generate embeddings). Events must be published reliably — if the database transaction commits but the message fails to publish, the system is inconsistent.

## Options Considered

1. **Direct publish after commit** — Write to DB, then publish to RabbitMQ.
   - Pros: Simple
   - Cons: Crash between commit and publish loses event (dual-write problem)

2. **Transactional outbox** — Write event to outbox table in same transaction; background publisher reads and publishes.
   - Pros: Guaranteed at-least-once delivery, no dual-write problem
   - Cons: Slight latency (publisher poll interval), outbox table to manage

3. **Change Data Capture (CDC)** — Debezium reads PostgreSQL WAL, publishes changes.
   - Pros: No application code for publishing
   - Cons: Additional infrastructure (Kafka/Debezium), operational complexity

## Decision

Use the **transactional outbox pattern**: domain events are written to `shared.outbox_events` in the same database transaction as the domain change. A Celery beat task polls pending events and publishes to RabbitMQ.

## Consequences

- **Easier:** Guaranteed event delivery aligned with database state
- **Easier:** No additional infrastructure (CDC)
- **Easier:** Events are inspectable in the database for debugging
- **Harder:** Consumers must be idempotent (at-least-once delivery)
- **Harder:** Publisher lag of ~1 second (poll interval) — acceptable for all current use cases
