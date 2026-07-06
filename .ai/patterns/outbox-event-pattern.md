# Outbox Event Pattern

## Purpose

Reliably persist domain events in the same database transaction as aggregate changes, for async publication to RabbitMQ.

## Applies To

- Command handlers (emit)
- `services/shared/outbox/` (writer + publisher)
- Table: `shared.outbox_events` per `docs/05-database/audit-schema.md`

## Mandatory Reads

- `docs/13-decisions/006-transactional-outbox.md`
- `docs/03-architecture/event-driven-design.md`
- `docs/02-domain/domain-events.md`

---

## Structure Template

```
services/shared/
├── outbox/
│   ├── writer.py          # OutboxWriter.append(event)
│   ├── publisher.py       # Background poll + RabbitMQ publish
│   └── models.py          # OutboxEvent ORM
└── messaging/
    └── routing.py         # eventType → routing_key map
```

---

## Pseudocode Outline

```
# --- In Command Handler (same transaction as aggregate save) ---
for domain_event in aggregate.pull_domain_events():
    outbox_writer.append(
        event_id=domain_event.id,
        event_type=domain_event.event_type,       # e.g. "CaseCreated"
        aggregate_type=domain_event.aggregate_type,
        aggregate_id=domain_event.aggregate_id,
        firm_id=cmd.firm_id,
        payload=domain_event.payload,
        correlation_id=cmd.correlation_id,
        causation_id=cmd.causation_id,
        actor_id=cmd.actor_id,
        actor_type="user",
    )
# commit transaction — aggregate + outbox rows atomic


# --- OutboxWriter.append ---
def append(self, ...) -> None:
    row = OutboxEventModel(
        id=event_id,
        status="pending",
        event_type=event_type,
        payload=build_envelope(...),   # full envelope per domain-events.md
        created_at=utcnow(),
    )
    self.session.add(row)


# --- Publisher (separate process / thread) ---
def publish_pending_batch():
    rows = repo.fetch_pending(limit=100, for_update_skip_locked=True)
    for row in rows:
        routing_key = ROUTING_MAP[row.event_type]
        broker.publish(exchange="lexflow.events", routing_key=routing_key, body=row.payload)
        repo.mark_published(row.id, published_at=utcnow())
```

---

## Envelope Fields (Required)

Per `docs/02-domain/domain-events.md`: `eventId`, `eventType`, `aggregateType`, `aggregateId`, `firmId`, `occurredAt`, `correlationId`, `causationId`, `version`, `actorId`, `actorType`, `payload`.

---

## Invariants

| # | Rule |
|---|------|
| 1 | Outbox insert in **same transaction** as aggregate persist |
| 2 | Never publish to RabbitMQ before commit |
| 3 | Publisher idempotent — safe to republish pending |
| 4 | `eventType` PascalCase past tense |
| 5 | Failed publish retries with backoff; `failed` after threshold |
| 6 | Audit context may also consume events (conformist) |

---

## Anti-Patterns

- Dual write: DB commit then fire-and-forget publish
- Outbox row outside transaction
- Missing correlationId/causationId chain
- Publishing before marking (race on crash)

---

## Checklist

- [ ] Envelope matches domain-events.md schema
- [ ] Routing key registered in event-driven-design.md
- [ ] Writer called from command handler only
- [ ] Publisher uses SKIP LOCKED for concurrency
- [ ] Monitoring on pending backlog age
- [ ] Manual replay procedure documented in runbook
