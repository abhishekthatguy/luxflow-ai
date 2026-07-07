"""n8n workflow invocation Celery tasks."""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from uuid import UUID

import httpx
from sqlalchemy import select

from sqlalchemy import select

from lexflow_api.celery_app import celery_app
from lexflow_api.config import settings
from lexflow_api.db.sync_session import SyncSessionLocal
from lexflow_api.models.documents import Document
from lexflow_api.models.shared import AsyncJob
from lexflow_api.models.workflows import ExecutionStatus, WorkflowDefinition, WorkflowExecution
from lexflow_api.services.timeline import write_timeline_event_sync
from lexflow_api.services.workflow_dedup import client_created_key, document_upload_key

logger = logging.getLogger(__name__)


def _post_n8n(slug: str, payload: dict[str, object], *, max_attempts: int = 4) -> dict[str, object]:
    import hashlib
    import hmac

    url = f"{settings.n8n_internal_url.rstrip('/')}/webhook/{slug}"
    body = json.dumps(payload).encode()
    signature = hmac.new(
        settings.n8n_webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    last_result: dict[str, object] = {"status": "failed", "message": "no response"}
    for attempt in range(max_attempts):
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    url,
                    content=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-LexFlow-Signature": signature,
                    },
                )
                if response.status_code >= 400:
                    last_result = {
                        "status": "failed",
                        "httpStatus": response.status_code,
                        "message": response.text[:200],
                    }
                    if response.status_code in (404, 502, 503, 504) and attempt < max_attempts - 1:
                        time.sleep(2**attempt)
                        continue
                    return last_result
                return response.json() if response.content else {"status": "accepted"}
        except Exception as exc:
            logger.warning("n8n webhook unavailable (attempt %s): %s", attempt + 1, exc)
            last_result = {"status": "stub", "message": f"n8n unreachable — {exc}"}
            if attempt < max_attempts - 1:
                time.sleep(2**attempt)
                continue
    return last_result


@celery_app.task(name="lexflow_api.tasks.workflow_tasks.invoke_n8n_workflow")  # type: ignore[untyped-decorator]
def invoke_n8n_workflow(execution_id: str, job_id: str | None) -> dict[str, str]:
    exec_uuid = UUID(execution_id)
    session = SyncSessionLocal()
    try:
        execution = session.execute(
            select(WorkflowExecution).where(WorkflowExecution.id == exec_uuid)
        ).scalar_one()
        definition = session.execute(
            select(WorkflowDefinition).where(
                WorkflowDefinition.id == execution.workflow_definition_id
            )
        ).scalar_one()

        if job_id:
            job = session.execute(select(AsyncJob).where(AsyncJob.id == UUID(job_id))).scalar_one()
            job.status = "running"
            job.progress = 30
            job.started_at = datetime.now(UTC)

        execution.status = ExecutionStatus.RUNNING
        execution.started_at = datetime.now(UTC)
        session.commit()

        result = _post_n8n(
            definition.slug,
            {
                "executionId": str(execution.id),
                "caseId": str(execution.case_id) if execution.case_id else None,
                "payload": execution.input_payload,
            },
        )

        execution = session.execute(
            select(WorkflowExecution).where(WorkflowExecution.id == exec_uuid)
        ).scalar_one()
        if result.get("status") in ("failed",):
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(result.get("message") or result)[:500]
        else:
            execution.status = ExecutionStatus.COMPLETED
            execution.output_payload = result
        execution.completed_at = datetime.now(UTC)
        execution.updated_at = datetime.now(UTC)

        if execution.case_id and execution.status == ExecutionStatus.COMPLETED:
            write_timeline_event_sync(
                session,
                case_id=execution.case_id,
                firm_id=execution.firm_id,
                event_type="workflow.completed",
                title="Workflow completed",
                payload={"executionId": str(execution.id)},
            )

        if job_id:
            job = session.execute(select(AsyncJob).where(AsyncJob.id == UUID(job_id))).scalar_one()
            job.status = "completed" if execution.status == ExecutionStatus.COMPLETED else "failed"
            job.progress = 100
            job.result = {"executionId": str(execution.id), **result}
            job.completed_at = datetime.now(UTC)

        session.commit()
        return {"status": execution.status, "executionId": execution_id}
    except Exception as exc:
        session.rollback()
        logger.exception("Workflow invoke failed for %s", execution_id)
        return {"status": "failed", "error": str(exc)}
    finally:
        session.close()


@celery_app.task(name="lexflow_api.tasks.workflow_tasks.trigger_document_upload_workflow")  # type: ignore[untyped-decorator]
def trigger_document_upload_workflow(document_id: str) -> dict[str, str]:
    doc_uuid = UUID(document_id)
    session = SyncSessionLocal()
    try:
        document = session.execute(
            select(Document).where(Document.id == doc_uuid)
        ).scalar_one()
        definition = session.execute(
            select(WorkflowDefinition).where(
                WorkflowDefinition.is_active.is_(True),
                WorkflowDefinition.slug == "document-upload-v1",
            )
        ).scalar_one_or_none()
        if definition is None:
            return {"status": "skipped", "reason": "no workflow definition"}

        dedup_key = document_upload_key(document.id)
        existing = session.execute(
            select(WorkflowExecution).where(
                WorkflowExecution.idempotency_key == dedup_key,
                WorkflowExecution.status.in_(
                    (ExecutionStatus.QUEUED, ExecutionStatus.RUNNING, ExecutionStatus.COMPLETED)
                ),
            )
        ).scalar_one_or_none()
        if existing is not None:
            return {"status": "deduplicated", "executionId": str(existing.id)}

        execution = WorkflowExecution(
            workflow_definition_id=definition.id,
            case_id=document.case_id,
            firm_id=document.firm_id,
            status=ExecutionStatus.QUEUED,
            input_payload={
                "eventType": "DocumentUploaded",
                "documentId": str(document.id),
                "title": document.title,
            },
            correlation_id=document.id,
            idempotency_key=dedup_key,
        )
        session.add(execution)
        session.commit()
        if execution.case_id:
            write_timeline_event_sync(
                session,
                case_id=execution.case_id,
                firm_id=execution.firm_id,
                event_type="workflow.started",
                title="Workflow started",
                payload={"executionId": str(execution.id), "slug": definition.slug},
            )
        invoke_n8n_workflow.delay(str(execution.id), None)
        return {"status": "queued", "executionId": str(execution.id)}
    finally:
        session.close()


@celery_app.task(name="lexflow_api.tasks.workflow_tasks.trigger_client_created_workflow")  # type: ignore[untyped-decorator]
def trigger_client_created_workflow(
    client_id: str,
    firm_id: str,
    actor_id: str,
) -> dict[str, str]:
    """Queue WF-04 client-created-v1 when a portal user adds a client."""
    client_uuid = UUID(client_id)
    firm_uuid = UUID(firm_id)
    session = SyncSessionLocal()
    try:
        definition = session.execute(
            select(WorkflowDefinition).where(
                WorkflowDefinition.is_active.is_(True),
                WorkflowDefinition.slug == "client-created-v1",
            )
        ).scalar_one_or_none()
        if definition is None:
            return {"status": "skipped", "reason": "no workflow definition"}

        dedup_key = client_created_key(client_uuid)
        existing = session.execute(
            select(WorkflowExecution).where(
                WorkflowExecution.idempotency_key == dedup_key,
                WorkflowExecution.status.in_(
                    (ExecutionStatus.QUEUED, ExecutionStatus.RUNNING, ExecutionStatus.COMPLETED)
                ),
            )
        ).scalar_one_or_none()
        if existing is not None:
            return {"status": "deduplicated", "executionId": str(existing.id)}

        execution = WorkflowExecution(
            workflow_definition_id=definition.id,
            case_id=None,
            firm_id=firm_uuid,
            triggered_by=UUID(actor_id),
            status=ExecutionStatus.QUEUED,
            input_payload={
                "eventType": "ClientCreated",
                "clientId": client_id,
                "firmId": firm_id,
                "actorId": actor_id,
            },
            correlation_id=client_uuid,
            idempotency_key=dedup_key,
        )
        session.add(execution)
        session.commit()
        invoke_n8n_workflow.delay(str(execution.id), None)
        return {"status": "queued", "executionId": str(execution.id)}
    finally:
        session.close()
