import hashlib
import hmac
import json
import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser
from lexflow_api.config import settings
from lexflow_api.exceptions import NotFoundError
from lexflow_api.models.workflows import (
    ExecutionStatus,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStep,
)
from lexflow_api.schemas.jobs import JobAcceptedResponse
from lexflow_api.schemas.workflows import (
    N8nCallbackPayload,
    WorkflowExecutionResponse,
    WorkflowStepResponse,
    WorkflowTriggerRequest,
)
from lexflow_api.services.case_service import CaseService
from lexflow_api.services.job_service import JobService
from lexflow_api.services.outbox import write_outbox_event

logger = logging.getLogger(__name__)


class WorkflowService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._cases = CaseService(session)
        self._jobs = JobService(session)

    @staticmethod
    def to_execution_response(execution: WorkflowExecution) -> WorkflowExecutionResponse:
        return WorkflowExecutionResponse(
            id=execution.id,
            workflow_definition_id=execution.workflow_definition_id,
            case_id=execution.case_id,
            status=execution.status,
            correlation_id=execution.correlation_id,
            n8n_execution_id=execution.n8n_execution_id,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            error_message=execution.error_message,
            created_at=execution.created_at,
        )

    @staticmethod
    def to_step_response(step: WorkflowStep) -> WorkflowStepResponse:
        return WorkflowStepResponse(
            id=step.id,
            step_name=step.step_name,
            step_order=step.step_order,
            status=step.status,
            started_at=step.started_at,
            completed_at=step.completed_at,
        )

    async def trigger_workflow(
        self, user: CurrentUser, case_id: UUID, data: WorkflowTriggerRequest
    ) -> JobAcceptedResponse:
        await self._cases._get_accessible_case(user, case_id)
        definition = await self._get_definition(data.workflow_slug, user.firm_id)
        correlation_id = uuid4()

        execution = WorkflowExecution(
            workflow_definition_id=definition.id,
            case_id=case_id,
            firm_id=user.firm_id,
            triggered_by=user.id,
            status=ExecutionStatus.QUEUED,
            input_payload={"workflowSlug": data.workflow_slug, "caseId": str(case_id)},
            correlation_id=correlation_id,
        )
        self._session.add(execution)
        await self._session.flush()

        job = await self._jobs.create_job(
            firm_id=user.firm_id,
            user_id=user.id,
            case_id=case_id,
            job_type="workflow.execution",
            resource_type="workflow_execution",
            resource_id=execution.id,
            correlation_id=correlation_id,
        )
        await write_outbox_event(
            self._session,
            firm_id=user.firm_id,
            aggregate_type="workflow_execution",
            aggregate_id=execution.id,
            event_type="WorkflowTriggered",
            payload={"caseId": str(case_id), "slug": data.workflow_slug},
        )

        from lexflow_api.tasks.workflow_tasks import invoke_n8n_workflow

        invoke_n8n_workflow.delay(str(execution.id), str(job.id))

        return JobAcceptedResponse(
            job_id=job.id,
            status="queued",
            status_url=f"/api/v1/jobs/{job.id}",
        )

    async def list_executions(
        self, user: CurrentUser, case_id: UUID, *, page: int = 1, page_size: int = 25
    ) -> tuple[list[WorkflowExecutionResponse], int]:
        await self._cases._get_accessible_case(user, case_id)
        query = select(WorkflowExecution).where(
            WorkflowExecution.case_id == case_id,
            WorkflowExecution.firm_id == user.firm_id,
        )
        count_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = int(count_result.scalar_one())
        offset = (page - 1) * page_size
        result = await self._session.execute(
            query.order_by(WorkflowExecution.created_at.desc()).offset(offset).limit(page_size)
        )
        return [self.to_execution_response(e) for e in result.scalars().all()], total

    async def list_steps(self, user: CurrentUser, execution_id: UUID) -> list[WorkflowStepResponse]:
        execution = await self._get_accessible_execution(user, execution_id)
        result = await self._session.execute(
            select(WorkflowStep)
            .where(WorkflowStep.execution_id == execution.id)
            .order_by(WorkflowStep.step_order)
        )
        return [self.to_step_response(s) for s in result.scalars().all()]

    async def handle_n8n_callback(self, slug: str, payload: N8nCallbackPayload) -> None:
        result = await self._session.execute(
            select(WorkflowExecution).where(WorkflowExecution.id == payload.execution_id)
        )
        execution = result.scalar_one_or_none()
        if execution is None:
            raise NotFoundError("Workflow execution not found.")

        execution.status = payload.status
        execution.n8n_execution_id = payload.n8n_execution_id
        execution.output_payload = payload.output
        execution.error_message = payload.error_message
        execution.completed_at = datetime.now(UTC) if payload.status in ("completed", "failed") else None
        execution.updated_at = datetime.now(UTC)

        step = WorkflowStep(
            execution_id=execution.id,
            step_name=f"n8n:{slug}",
            step_order=1,
            status="completed" if payload.status == "completed" else "failed",
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            metadata_=payload.output or {},
            error_message=payload.error_message,
        )
        self._session.add(step)

    async def trigger_event_workflow(
        self,
        *,
        firm_id: UUID,
        case_id: UUID,
        event_type: str,
        payload: dict[str, object],
    ) -> None:
        result = await self._session.execute(
            select(WorkflowDefinition).where(
                WorkflowDefinition.is_active.is_(True),
                WorkflowDefinition.trigger_type == "event",
                WorkflowDefinition.slug == "document-upload-notify-v1",
            )
        )
        definition = result.scalar_one_or_none()
        if definition is None:
            logger.info("No workflow definition for event %s", event_type)
            return

        correlation_id = uuid4()
        execution = WorkflowExecution(
            workflow_definition_id=definition.id,
            case_id=case_id,
            firm_id=firm_id,
            status=ExecutionStatus.QUEUED,
            input_payload={"eventType": event_type, **payload},
            correlation_id=correlation_id,
        )
        self._session.add(execution)
        await self._session.flush()

        from lexflow_api.tasks.workflow_tasks import invoke_n8n_workflow

        invoke_n8n_workflow.delay(str(execution.id), None)

    @staticmethod
    def verify_hmac(body: bytes, signature: str | None) -> bool:
        if not signature:
            return False
        expected = hmac.new(
            settings.n8n_webhook_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(signature, expected)

    @staticmethod
    async def call_n8n_webhook(slug: str, payload: dict[str, object]) -> dict[str, object]:
        url = f"{settings.n8n_internal_url.rstrip('/')}/webhook/{slug}"
        body = json.dumps(payload).encode()
        signature = hmac.new(
            settings.n8n_webhook_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    content=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-LexFlow-Signature": signature,
                    },
                )
                if response.status_code >= 400:
                    logger.warning("n8n webhook %s returned %s", slug, response.status_code)
                    return {"status": "failed", "httpStatus": response.status_code}
                return response.json() if response.content else {"status": "accepted"}
        except Exception as exc:
            logger.exception("n8n webhook call failed")
            return {"status": "failed", "error": str(exc)}

    async def _get_definition(self, slug: str, firm_id: UUID) -> WorkflowDefinition:
        result = await self._session.execute(
            select(WorkflowDefinition).where(
                WorkflowDefinition.slug == slug,
                WorkflowDefinition.is_active.is_(True),
                (WorkflowDefinition.firm_id == firm_id) | (WorkflowDefinition.firm_id.is_(None)),
            )
        )
        definition = result.scalar_one_or_none()
        if definition is None:
            raise NotFoundError(f"Workflow '{slug}' not found.")
        return definition

    async def _get_accessible_execution(
        self, user: CurrentUser, execution_id: UUID
    ) -> WorkflowExecution:
        result = await self._session.execute(
            select(WorkflowExecution).where(
                WorkflowExecution.id == execution_id,
                WorkflowExecution.firm_id == user.firm_id,
            )
        )
        execution = result.scalar_one_or_none()
        if execution is None:
            raise NotFoundError("Workflow execution not found.")
        if execution.case_id:
            await self._cases._get_accessible_case(user, execution.case_id)
        return execution
