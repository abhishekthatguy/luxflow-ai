# Celery Task Pattern

## Purpose

Async worker entrypoint for long-running or decoupled work (OCR, embeddings, LLM, n8n trigger). Tasks are thin adapters — delegate to application use cases.

## Applies To

`workers/celery/tasks/` — distinct from event handlers when task is API-triggered or scheduled, not purely event-driven.

## Mandatory Reads

- `docs/13-decisions/004-async-ai-processing.md`
- `docs/03-architecture/data-flow.md`
- `.ai/patterns/use-case-pattern.md`
- `.ai/patterns/event-handler-pattern.md` (if event-triggered)

---

## Structure Template

```
workers/celery/
├── app.py
├── config.py                    # broker URL, queues
└── tasks/
    ├── ai_jobs.py               # process_ai_job(job_id)
    ├── document_processing.py   # OCR pipeline
    └── workflow_trigger.py      # n8n HTTP trigger
```

---

## Pseudocode Outline

```
@shared_task(
    name="lexflow.ai.process_job",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
    queue="ai.jobs",
)
def process_ai_job(self, job_id: str) -> None:
    job_uuid = UUID(job_id)

    with trace_context_from_job(job_uuid):
        try:
            with db_session() as db:
                # 1. Load job record — idempotent state check
                job = job_repo.get(job_uuid)
                if job.status in (COMPLETED, FAILED):
                    return  # already terminal

                # 2. Transition to processing (optimistic lock / version)
                job_repo.mark_processing(job_uuid)

                # 3. Delegate — AI use case owns RAG + LLM + validation
                cmd = ExecuteAiJobCommand(job_id=job_uuid)
                result = ExecuteAiJobHandler(db).handle(cmd)

            # 4. Success — handler emits SummaryGenerated via outbox inside txn

        except TransientProviderError as exc:
            raise self.retry(exc=exc)
        except PermanentError as exc:
            with db_session() as db:
                FailAiJobHandler(db).handle(FailAiJobCommand(job_id=job_uuid, reason=str(exc)))
            raise  # no retry — alert
```

---

## Queue Mapping

| Queue | Work Type |
|-------|-----------|
| `document.processing` | OCR, virus scan, embedding |
| `ai.jobs` | LLM inference |
| `workflow.trigger` | n8n HTTP outbound |
| `notification.dispatch` | Email, Teams |
| `*.events` | Domain event handlers |

---

## Invariants

| # | Rule |
|---|------|
| 1 | API enqueues task — returns 202 immediately |
| 2 | Task body ≤ orchestration — logic in use case |
| 3 | Idempotent on job_id / eventId |
| 4 | State machine on job record (pending → processing → done/failed) |
| 5 | Transient vs permanent error classification |
| 6 | No LLM in API process |

---

## Anti-Patterns

- Business rules copy-pasted in task
- Missing job status persistence (unrecoverable on crash)
- Infinite retry on permanent errors
- Calling external APIs without timeout/circuit breaker

---

## Checklist

- [ ] Task registered with explicit queue
- [ ] Retry policy documented
- [ ] Use case handler invoked
- [ ] Job state persisted and idempotent
- [ ] Correlation ID in logs
- [ ] Metrics: duration, success/failure rate
- [ ] Integration test with mocked LLM/S3
