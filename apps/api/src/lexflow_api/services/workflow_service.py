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
from lexflow_api.auth.rbac import FIRM_WIDE_ACCESS_ROLES, has_any_role
from lexflow_api.auth.workflow_rbac import can_delete_workflow_execution, can_trigger_workflow
from lexflow_api.exceptions import ConflictError, ForbiddenError, NotFoundError
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
    WorkflowTriggerResult,
)
from lexflow_api.services.case_service import CaseService
from lexflow_api.services.job_service import JobService
from lexflow_api.services.outbox import write_outbox_event
from lexflow_api.services.workflow_dedup import (
    case_intake_key,
    document_upload_key,
    workflow_event_key,
    workflow_manual_key,
)

logger = logging.getLogger(__name__)


class WorkflowService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._cases = CaseService(session)
        self._jobs = JobService(session)

    @staticmethod
    def to_execution_response(
        execution: WorkflowExecution,
        *,
        workflow_slug: str | None = None,
        workflow_name: str | None = None,
    ) -> WorkflowExecutionResponse:
        return WorkflowExecutionResponse(
            id=execution.id,
            workflow_definition_id=execution.workflow_definition_id,
            workflow_slug=workflow_slug,
            workflow_name=workflow_name,
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
        self,
        user: CurrentUser,
        case_id: UUID,
        data: WorkflowTriggerRequest,
        *,
        idempotency_key: str | None = None,
    ) -> WorkflowTriggerResult:
        await self._cases._get_accessible_case(user, case_id)
        definition = await self._get_definition(data.workflow_slug, user.firm_id)
        if not can_trigger_workflow(user_roles=user.roles, slug=data.workflow_slug):
            raise ForbiddenError(
                f"Your role cannot trigger workflow '{definition.name}'. "
                f"Required roles are configured in the workflow catalog."
            )

        if data.force and not has_any_role(user.roles, FIRM_WIDE_ACCESS_ROLES):
            raise ForbiddenError("Only Managing Partner or System Administrator can force re-trigger.")

        dedup_key: str | None = None
        if not data.force:
            if idempotency_key:
                dedup_key = workflow_manual_key(
                    slug=data.workflow_slug, case_id=case_id, idempotency_key=idempotency_key
                )
            else:
                dedup_key = workflow_event_key(slug=data.workflow_slug, aggregate_id=case_id)
            existing = await self._find_active_or_completed_execution(dedup_key)
            if existing is not None:
                job = await self._jobs.find_for_resource("workflow_execution", existing.id)
                return WorkflowTriggerResult(
                    job_id=job.id if job else existing.id,
                    status=existing.status,
                    status_url=f"/api/v1/jobs/{job.id}" if job else f"/api/v1/cases/{case_id}/workflows",
                    execution_id=existing.id,
                    deduplicated=True,
                )

        correlation_id = uuid4()
        execution = WorkflowExecution(
            workflow_definition_id=definition.id,
            case_id=case_id,
            firm_id=user.firm_id,
            triggered_by=user.id,
            status=ExecutionStatus.QUEUED,
            input_payload={"workflowSlug": data.workflow_slug, "caseId": str(case_id)},
            correlation_id=correlation_id,
            idempotency_key=dedup_key,
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

        await self._session.commit()
        invoke_n8n_workflow.delay(str(execution.id), str(job.id))

        return WorkflowTriggerResult(
            job_id=job.id,
            status="queued",
            status_url=f"/api/v1/jobs/{job.id}",
            execution_id=execution.id,
            deduplicated=False,
        )

    async def trigger_firm_workflow(
        self,
        user: CurrentUser,
        data: WorkflowTriggerRequest,
        *,
        idempotency_key: str | None = None,
    ) -> WorkflowTriggerResult:
        """Manual/test trigger for firm-scoped workflows (no case context)."""
        definition = await self._get_definition(data.workflow_slug, user.firm_id)
        if not can_trigger_workflow(user_roles=user.roles, slug=data.workflow_slug):
            raise ForbiddenError(
                f"Your role cannot trigger workflow '{definition.name}'."
            )

        if data.force and not has_any_role(user.roles, FIRM_WIDE_ACCESS_ROLES):
            raise ForbiddenError("Only Managing Partner or System Administrator can force re-trigger.")

        dedup_key: str | None = None
        if not data.force:
            if idempotency_key:
                dedup_key = workflow_manual_key(
                    slug=data.workflow_slug, case_id=None, idempotency_key=idempotency_key
                )
            existing = await self._find_active_or_completed_execution(dedup_key)
            if existing is not None:
                job = await self._jobs.find_for_resource("workflow_execution", existing.id)
                return WorkflowTriggerResult(
                    job_id=job.id if job else existing.id,
                    status=existing.status,
                    status_url=f"/api/v1/jobs/{job.id}" if job else "/api/v1/workflows/catalog",
                    execution_id=existing.id,
                    deduplicated=True,
                )

        correlation_id = uuid4()
        execution = WorkflowExecution(
            workflow_definition_id=definition.id,
            case_id=None,
            firm_id=user.firm_id,
            triggered_by=user.id,
            status=ExecutionStatus.QUEUED,
            input_payload={"workflowSlug": data.workflow_slug, "firmId": str(user.firm_id)},
            correlation_id=correlation_id,
            idempotency_key=dedup_key,
        )
        self._session.add(execution)
        await self._session.flush()

        job = await self._jobs.create_job(
            firm_id=user.firm_id,
            user_id=user.id,
            case_id=None,
            job_type="workflow.execution",
            resource_type="workflow_execution",
            resource_id=execution.id,
            correlation_id=correlation_id,
        )
        await self._session.commit()
        from lexflow_api.tasks.workflow_tasks import invoke_n8n_workflow

        invoke_n8n_workflow.delay(str(execution.id), str(job.id))

        return WorkflowTriggerResult(
            job_id=job.id,
            status="queued",
            status_url=f"/api/v1/jobs/{job.id}",
            execution_id=execution.id,
            deduplicated=False,
        )

    async def delete_execution(
        self, user: CurrentUser, case_id: UUID, execution_id: UUID
    ) -> None:
        if not can_delete_workflow_execution(user_roles=user.roles):
            raise ForbiddenError(
                "Only Managing Partner or System Administrator can delete workflow executions."
            )
        await self._cases._get_accessible_case(user, case_id)
        execution = await self._get_accessible_execution(user, execution_id)
        if execution.case_id != case_id:
            raise NotFoundError("Workflow execution not found for this case.")
        await self._session.delete(execution)

    async def list_executions(
        self, user: CurrentUser, case_id: UUID, *, page: int = 1, page_size: int = 25
    ) -> tuple[list[WorkflowExecutionResponse], int]:
        await self._cases._get_accessible_case(user, case_id)
        query = (
            select(WorkflowExecution, WorkflowDefinition.slug, WorkflowDefinition.name)
            .join(
                WorkflowDefinition,
                WorkflowDefinition.id == WorkflowExecution.workflow_definition_id,
            )
            .where(
                WorkflowExecution.case_id == case_id,
                WorkflowExecution.firm_id == user.firm_id,
            )
        )
        count_result = await self._session.execute(
            select(func.count()).select_from(
                select(WorkflowExecution.id).where(
                    WorkflowExecution.case_id == case_id,
                    WorkflowExecution.firm_id == user.firm_id,
                ).subquery()
            )
        )
        total = int(count_result.scalar_one())
        offset = (page - 1) * page_size
        result = await self._session.execute(
            query.order_by(WorkflowExecution.created_at.desc()).offset(offset).limit(page_size)
        )
        rows = [
            self.to_execution_response(execution, workflow_slug=slug, workflow_name=name)
            for execution, slug, name in result.all()
        ]
        return rows, total

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

        if execution.status in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED):
            return

        normalized = payload.status.lower()
        if normalized not in ("queued", "running", "completed", "failed", "cancelled"):
            normalized = "completed" if normalized in ("ok", "success") else "failed"

        execution.status = ExecutionStatus(normalized)
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
                WorkflowDefinition.slug == "document-upload-v1",
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

    async def _find_active_or_completed_execution(
        self, idempotency_key: str | None
    ) -> WorkflowExecution | None:
        if not idempotency_key:
            return None
        result = await self._session.execute(
            select(WorkflowExecution).where(
                WorkflowExecution.idempotency_key == idempotency_key,
                WorkflowExecution.status.in_(
                    (ExecutionStatus.QUEUED, ExecutionStatus.RUNNING, ExecutionStatus.COMPLETED)
                ),
            )
        )
        return result.scalar_one_or_none()

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
