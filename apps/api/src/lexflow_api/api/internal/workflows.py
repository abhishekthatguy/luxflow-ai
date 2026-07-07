from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.internal_hmac import verify_n8n_request
from lexflow_api.db.session import get_db
from lexflow_api.schemas.common import Envelope, envelope
from lexflow_api.schemas.internal_workflows import (
    WorkflowActionResult,
    WorkflowCaseContext,
    WorkflowInitializeRequest,
    WorkflowInitializeResponse,
    WorkflowOcrStatus,
)
from lexflow_api.services.internal_workflow_service import InternalWorkflowService

router = APIRouter(prefix="/internal/workflows", tags=["internal-workflows"])


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


def _require_n8n_auth(
    *,
    signature: str | None,
    token: str | None,
    raw: bytes = b"",
) -> None:
    if not verify_n8n_request(signature=signature, token=token, raw=raw):
        raise HTTPException(status_code=401, detail="Invalid workflow authorization.")


@router.get("/heartbeat", response_model=Envelope[dict[str, object]])
async def workflow_heartbeat(
    request: Request,
    x_lexflow_signature: str | None = Header(default=None, alias="X-LexFlow-Signature"),
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> Envelope[dict[str, object]]:
    """n8n connectivity + auth probe before running workflow steps."""
    _require_n8n_auth(signature=x_lexflow_signature, token=x_internal_token, raw=b"")
    from lexflow_api.auth.workflow_rbac import WORKFLOW_ACCESS

    return envelope(
        {
            "status": "ok",
            "service": "workflow-orchestrator",
            "authorized": True,
            "workflowsRegistered": len(WORKFLOW_ACCESS),
        },
        _request_id(request),
    )


@router.post("/{slug}/initialize", response_model=Envelope[WorkflowInitializeResponse])
async def workflow_initialize(
    request: Request,
    slug: str,
    session: AsyncSession = Depends(get_db),
    x_lexflow_signature: str | None = Header(default=None, alias="X-LexFlow-Signature"),
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> Envelope[WorkflowInitializeResponse]:
    raw = await request.body()
    _require_n8n_auth(signature=x_lexflow_signature, token=x_internal_token, raw=raw)
    body = WorkflowInitializeRequest.model_validate_json(raw)
    data = await InternalWorkflowService(session).initialize(slug, body)
    await session.commit()
    return envelope(data, _request_id(request))


@router.get(
    "/executions/{execution_id}/case-context",
    response_model=Envelope[WorkflowCaseContext],
)
async def workflow_case_context(
    request: Request,
    execution_id: UUID,
    session: AsyncSession = Depends(get_db),
    x_lexflow_signature: str | None = Header(default=None, alias="X-LexFlow-Signature"),
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> Envelope[WorkflowCaseContext]:
    _require_n8n_auth(signature=x_lexflow_signature, token=x_internal_token)
    data = await InternalWorkflowService(session).case_context(execution_id)
    return envelope(data, _request_id(request))


@router.get(
    "/documents/{document_id}/ocr-status",
    response_model=Envelope[WorkflowOcrStatus],
)
async def workflow_ocr_status(
    request: Request,
    document_id: UUID,
    attempt: int = Query(1, ge=1, le=30),
    session: AsyncSession = Depends(get_db),
    x_lexflow_signature: str | None = Header(default=None, alias="X-LexFlow-Signature"),
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> Envelope[WorkflowOcrStatus]:
    _require_n8n_auth(signature=x_lexflow_signature, token=x_internal_token)
    data = await InternalWorkflowService(session).ocr_status(document_id, attempt=attempt)
    return envelope(data, _request_id(request))


@router.post(
    "/{slug}/actions/ai-summary",
    response_model=Envelope[WorkflowActionResult],
)
async def workflow_action_ai_summary(
    request: Request,
    slug: str,
    execution_id: UUID,
    session: AsyncSession = Depends(get_db),
    x_lexflow_signature: str | None = Header(default=None, alias="X-LexFlow-Signature"),
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> Envelope[WorkflowActionResult]:
    _require_n8n_auth(signature=x_lexflow_signature, token=x_internal_token)
    data = await InternalWorkflowService(session).action_ai_summary(slug, execution_id)
    await session.commit()
    return envelope(data, _request_id(request))


@router.post(
    "/{slug}/actions/notify",
    response_model=Envelope[WorkflowActionResult],
)
async def workflow_action_notify(
    request: Request,
    slug: str,
    execution_id: UUID,
    session: AsyncSession = Depends(get_db),
    x_lexflow_signature: str | None = Header(default=None, alias="X-LexFlow-Signature"),
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> Envelope[WorkflowActionResult]:
    _require_n8n_auth(signature=x_lexflow_signature, token=x_internal_token)
    data = await InternalWorkflowService(session).action_notify(slug, execution_id)
    await session.commit()
    return envelope(data, _request_id(request))


@router.post(
    "/{slug}/actions/audit",
    response_model=Envelope[WorkflowActionResult],
)
async def workflow_action_audit(
    request: Request,
    slug: str,
    execution_id: UUID,
    session: AsyncSession = Depends(get_db),
    x_lexflow_signature: str | None = Header(default=None, alias="X-LexFlow-Signature"),
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> Envelope[WorkflowActionResult]:
    _require_n8n_auth(signature=x_lexflow_signature, token=x_internal_token)
    data = await InternalWorkflowService(session).action_audit(slug, execution_id)
    await session.commit()
    return envelope(data, _request_id(request))


@router.post(
    "/{slug}/actions/alert",
    response_model=Envelope[WorkflowActionResult],
)
async def workflow_action_alert(
    request: Request,
    slug: str,
    execution_id: UUID,
    reason: str = Query("workflow step failed"),
    session: AsyncSession = Depends(get_db),
    x_lexflow_signature: str | None = Header(default=None, alias="X-LexFlow-Signature"),
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> Envelope[WorkflowActionResult]:
    _require_n8n_auth(signature=x_lexflow_signature, token=x_internal_token)
    data = await InternalWorkflowService(session).action_alert(slug, execution_id, reason)
    await session.commit()
    return envelope(data, _request_id(request))
