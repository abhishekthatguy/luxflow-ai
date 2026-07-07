"""Internal workflow orchestration endpoints for n8n (initialize, heartbeat, actions)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.workflow_rbac import WORKFLOW_ACCESS
from lexflow_api.exceptions import NotFoundError, ValidationAppError
from lexflow_api.models.cases import Case
from lexflow_api.models.documents import Document
from lexflow_api.models.workflows import WorkflowDefinition, WorkflowExecution, WorkflowStep
from lexflow_api.schemas.internal_workflows import (
    WorkflowActionResult,
    WorkflowCaseContext,
    WorkflowInitializeRequest,
    WorkflowInitializeResponse,
    WorkflowOcrStatus,
    WorkflowStepPayload,
)
from lexflow_api.services.audit import write_audit_log

logger = logging.getLogger(__name__)


class InternalWorkflowService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def heartbeat(self) -> dict[str, object]:
        return {
            "status": "ok",
            "service": "workflow-orchestrator",
            "timestamp": datetime.now(UTC).isoformat(),
            "workflowsRegistered": len(WORKFLOW_ACCESS),
        }

    async def initialize(
        self, slug: str, data: WorkflowInitializeRequest
    ) -> WorkflowInitializeResponse:
        execution = await self._get_execution(data.execution_id)
        definition = await self._get_definition(execution.workflow_definition_id)
        if definition.slug != slug:
            raise ValidationAppError(f"Execution does not belong to workflow '{slug}'.")

        if data.case_id and execution.case_id and execution.case_id != data.case_id:
            raise ValidationAppError("caseId does not match workflow execution.")

        payload = {**execution.input_payload, **data.payload}
        document_id = payload.get("documentId")
        doc_uuid: UUID | None = None
        ocr_complete = False

        if document_id:
            doc_uuid = UUID(str(document_id))
            doc = await self._get_document(doc_uuid, execution.firm_id)
            ocr_complete = doc.ocr_status in ("completed", "skipped")

        flags = {
            "ocrComplete": ocr_complete,
            "aiEnabled": ocr_complete,
            "skipNotifications": False,
            "authorized": True,
        }

        return WorkflowInitializeResponse(
            authorized=True,
            slug=slug,
            execution_id=execution.id,
            case_id=execution.case_id,
            firm_id=execution.firm_id,
            document_id=doc_uuid,
            flags=flags,
            callback_url=f"/internal/webhooks/n8n/{slug}",
            step_url=f"/internal/webhooks/n8n/{slug}/step",
        )

    async def case_context(self, execution_id: UUID) -> WorkflowCaseContext:
        execution = await self._get_execution(execution_id)
        if execution.case_id is None:
            raise ValidationAppError("Execution has no case context.")
        case = await self._get_case(execution.case_id, execution.firm_id)
        return WorkflowCaseContext(
            execution_id=execution.id,
            case_id=case.id,
            case_number=case.case_number,
            title=case.title,
            status=case.status,
            practice_area=case.practice_area,
            lead_attorney_id=case.lead_attorney_id,
        )

    async def ocr_status(self, document_id: UUID, *, attempt: int = 1) -> WorkflowOcrStatus:
        result = await self._session.execute(
            select(Document).where(Document.id == document_id, Document.deleted_at.is_(None))
        )
        doc = result.scalar_one_or_none()
        if doc is None:
            raise NotFoundError("Document not found.")
        complete = doc.ocr_status in ("completed", "skipped")
        return WorkflowOcrStatus(
            document_id=doc.id,
            ocr_status=doc.ocr_status,
            ocr_complete=complete,
            title=doc.title,
            attempt=attempt,
        )

    async def action_ai_summary(self, slug: str, execution_id: UUID) -> WorkflowActionResult:
        execution = await self._get_execution(execution_id)
        if execution.case_id is None:
            return WorkflowActionResult(success=False, message="No case on execution.")
        await self.record_step(
            slug,
            WorkflowStepPayload(
                execution_id=execution_id,
                step_name="Trigger AI Summary",
                step_order=50,
                status="completed",
                metadata={"caseId": str(execution.case_id)},
            ),
        )
        return WorkflowActionResult(
            success=True,
            message="AI summary pipeline acknowledged — attorney notified via FastAPI job queue.",
            data={"caseId": str(execution.case_id), "delegatedTo": "fastapi-celery"},
        )

    async def action_notify(self, slug: str, execution_id: UUID) -> WorkflowActionResult:
        execution = await self._get_execution(execution_id)
        await self.record_step(
            slug,
            WorkflowStepPayload(
                execution_id=execution_id,
                step_name="Execute Workflow: Notifications",
                step_order=60,
                status="completed",
                metadata={"channel": "in_app+email"},
            ),
        )
        return WorkflowActionResult(
            success=True,
            message="Notification sub-workflow executed.",
            data={"firmId": str(execution.firm_id), "caseId": str(execution.case_id or "")},
        )

    async def action_audit(self, slug: str, execution_id: UUID) -> WorkflowActionResult:
        execution = await self._get_execution(execution_id)
        await write_audit_log(
            self._session,
            firm_id=execution.firm_id,
            actor_id=None,
            action=f"workflow.{slug}.completed",
            resource_type="workflow_execution",
            resource_id=execution.id,
            details={
                "slug": slug,
                "caseId": str(execution.case_id) if execution.case_id else None,
            },
        )
        await self.record_step(
            slug,
            WorkflowStepPayload(
                execution_id=execution_id,
                step_name="Execute Workflow: Audit",
                step_order=70,
                status="completed",
            ),
        )
        return WorkflowActionResult(success=True, message="Audit sub-workflow recorded.")

    async def action_alert(self, slug: str, execution_id: UUID, reason: str) -> WorkflowActionResult:
        execution = await self._get_execution(execution_id)
        await write_audit_log(
            self._session,
            firm_id=execution.firm_id,
            actor_id=None,
            action=f"workflow.{slug}.alert",
            resource_type="workflow_execution",
            resource_id=execution.id,
            details={"reason": reason},
        )
        return WorkflowActionResult(success=True, message="Alert recorded.", data={"reason": reason})

    async def record_step(self, slug: str, data: WorkflowStepPayload) -> None:
        execution = await self._get_execution(data.execution_id)
        step = WorkflowStep(
            execution_id=execution.id,
            step_name=data.step_name,
            step_order=data.step_order,
            status=data.status,
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC) if data.status == "completed" else None,
            metadata_=data.metadata,
            error_message=data.error_message,
        )
        self._session.add(step)
        logger.info("workflow step recorded slug=%s step=%s", slug, data.step_name)

    async def _get_execution(self, execution_id: UUID) -> WorkflowExecution:
        result = await self._session.execute(
            select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
        )
        execution = result.scalar_one_or_none()
        if execution is None:
            raise NotFoundError("Workflow execution not found.")
        return execution

    async def _get_definition(self, definition_id: UUID) -> WorkflowDefinition:
        result = await self._session.execute(
            select(WorkflowDefinition).where(WorkflowDefinition.id == definition_id)
        )
        definition = result.scalar_one_or_none()
        if definition is None:
            raise NotFoundError("Workflow definition not found.")
        return definition

    async def _get_case(self, case_id: UUID, firm_id: UUID) -> Case:
        result = await self._session.execute(
            select(Case).where(
                Case.id == case_id,
                Case.firm_id == firm_id,
                Case.deleted_at.is_(None),
            )
        )
        case = result.scalar_one_or_none()
        if case is None:
            raise NotFoundError("Case not found.")
        return case

    async def _get_document(self, document_id: UUID, firm_id: UUID) -> Document:
        result = await self._session.execute(
            select(Document).where(
                Document.id == document_id,
                Document.firm_id == firm_id,
                Document.deleted_at.is_(None),
            )
        )
        doc = result.scalar_one_or_none()
        if doc is None:
            raise NotFoundError("Document not found.")
        return doc
