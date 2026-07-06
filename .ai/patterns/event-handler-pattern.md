# Event Handler Pattern

## Purpose

Idempotent Celery consumer that reacts to domain events from RabbitMQ and invokes application use cases — never embeds business rules inline.

## Applies To

`workers/celery/tasks/{context}_handlers.py` and handler registration in `workers/celery/app.py`

## Mandatory Reads

- `docs/03-architecture/event-driven-design.md`
- `docs/02-domain/domain-events.md`
- `docs/06-workflows/retry-dlq.md`
- `.ai/patterns/use-case-pattern.md`
- `.ai/patterns/celery-task-pattern.md`

---

## Structure Template

```
workers/celery/
├── app.py                         # Celery app, queue bindings
├── tasks/
│   ├── document_handlers.py       # @shared_task for DocumentUploaded, etc.
│   ├── workflow_handlers.py       # WorkflowTriggered → n8n bridge
│   └── ai_handlers.py             # SummaryRequested → AI pipeline
└── middleware/
    └── idempotency.py             # Processed event store check
```

---

## Pseudocode Outline

```
@shared_task(
    name="lexflow.handlers.document.on_document_uploaded",
    bind=True,
    max_retries=5,
    acks_late=True,
)
def on_document_uploaded(self, envelope: dict) -> None:
    event_id = envelope["eventId"]
    correlation_id = envelope["correlationId"]

    with trace_context(correlation_id):
        # 1. Idempotency — skip if already processed
        if already_processed(event_id):
            logger.info("duplicate_event_skipped", event_id=event_id)
            return

        # 2. Parse payload
        payload = envelope["payload"]
        document_id = UUID(payload["documentId"])
        case_id = UUID(payload["caseId"])

        # 3. Build command — NO inline business logic
        cmd = ProcessDocumentCommand(
            document_id=document_id,
            case_id=case_id,
            correlation_id=correlation_id,
        )

        # 4. Delegate to application handler
        with db_session() as db:
            ProcessDocumentHandler(db).handle(cmd)

        # 5. Mark processed
        mark_processed(event_id)

        # 6. ACK implicit on success; retry on transient errors
```

---

## Invariants

| # | Rule |
|---|------|
| 1 | Idempotent on `eventId` |
| 2 | `acks_late=True` — process then ack |
| 3 | Correlation ID propagated to logs/traces |
| 4 | Handler calls use case — no domain logic in task |
| 5 | Poison messages → DLQ after max retries |
| 6 | No direct n8n calls except via workflow use case |

---

## Anti-Patterns

- Different business path on retry without idempotency
- Commit before successful side effect with early ack
- Subscribing handler to wrong routing key
- Parsing envelope without schema validation

---

## Checklist

- [ ] Task name matches consumer mapping in event-driven-design.md
- [ ] Idempotency store keyed on eventId
- [ ] Uses application command handler
- [ ] Retry policy matches retry-dlq.md
- [ ] Structured logging with correlation_id
- [ ] Integration test with test RabbitMQ or in-memory bus
