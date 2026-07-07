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
    WorkflowSessionResponse,
)
from lexflow_api.services.internal_workflow_service import InternalWorkflowService
from lexflow_api.services.workflow_session_service import WorkflowSessionService

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


def _session_headers(
    x_session_token: str | None,
) -> str | None:
    return x_session_token


@router.post("/session/initialize", response_model=Envelope[WorkflowSessionResponse])
async def session_initialize(
    request: Request,
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> Envelope[WorkflowSessionResponse]:
    """Create orchestrator session — run once (WF-11) or when heartbeat detects expiry."""
    _require_n8n_auth(signature=None, token=x_internal_token)
    data = WorkflowSessionService().initialize()
    return envelope(
        WorkflowSessionResponse(
            session_token=str(data["sessionToken"]),
            session_valid=True,
            authorized=True,
            requires_initialize=False,
            expires_at=str(data.get("expiresAt")),
            message="Orchestrator session initialized.",
        ),
        _request_id(request),
    )


@router.get("/session/heartbeat", response_model=Envelope[WorkflowSessionResponse])
async def session_heartbeat(
    request: Request,
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
) -> Envelope[WorkflowSessionResponse]:
    """Refresh session TTL — scheduled every 5 min (WF-12). Re-init if expired."""
    _require_n8n_auth(signature=None, token=x_internal_token)
    data = WorkflowSessionService().heartbeat(x_session_token)
    return envelope(
        WorkflowSessionResponse(
            session_token=str(data["sessionToken"]) if data.get("sessionToken") else x_session_token,
            session_valid=bool(data.get("sessionValid")),
            authorized=bool(data.get("sessionValid")),
            requires_initialize=bool(data.get("requiresInitialize")),
            expires_at=str(data.get("expiresAt")) if data.get("expiresAt") else None,
            refreshed_at=str(data.get("refreshedAt")) if data.get("refreshedAt") else None,
            message=str(data.get("message")) if data.get("message") else None,
        ),
        _request_id(request),
    )


@router.get("/session/verify", response_model=Envelope[WorkflowSessionResponse])
async def session_verify(
    request: Request,
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
) -> Envelope[WorkflowSessionResponse]:
    """Gate every business workflow — verify token + active session before steps run."""
    _require_n8n_auth(signature=None, token=x_internal_token)
    data = WorkflowSessionService().verify(x_session_token)
    if not data.get("authorized"):
        raise HTTPException(status_code=401, detail=str(data.get("message", "Session invalid.")))
    return envelope(
        WorkflowSessionResponse(
            session_valid=True,
            authorized=True,
            expires_at=str(data.get("expiresAt")) if data.get("expiresAt") else None,
            message="Session verified.",
        ),
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
    """Per-execution context (case flags) — not the orchestrator session."""
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
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> Envelope[WorkflowCaseContext]:
    _require_n8n_auth(signature=None, token=x_internal_token)
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
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> Envelope[WorkflowOcrStatus]:
    _require_n8n_auth(signature=None, token=x_internal_token)
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
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> Envelope[WorkflowActionResult]:
    _require_n8n_auth(signature=None, token=x_internal_token)
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
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> Envelope[WorkflowActionResult]:
    _require_n8n_auth(signature=None, token=x_internal_token)
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
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> Envelope[WorkflowActionResult]:
    _require_n8n_auth(signature=None, token=x_internal_token)
    data = await InternalWorkflowService(session).action_audit(slug, execution_id)
    await session.commit()
    return envelope(data, _request_id(request))


@router.post(
    "/{slug}/actions/step",
    response_model=Envelope[WorkflowActionResult],
)
async def workflow_action_step(
    request: Request,
    slug: str,
    execution_id: UUID,
    step_name: str = Query(..., min_length=1, max_length=200),
    step_order: int = Query(10, ge=1, le=1000),
    session: AsyncSession = Depends(get_db),
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> Envelope[WorkflowActionResult]:
    _require_n8n_auth(signature=None, token=x_internal_token)
    data = await InternalWorkflowService(session).action_step(
        slug,
        execution_id,
        step_name,
        step_order=step_order,
    )
    await session.commit()
    return envelope(data, _request_id(request))


@router.post("/scheduled/{slug}/run", response_model=Envelope[dict[str, object]])
async def scheduled_workflow_run(
    request: Request,
    slug: str,
    session: AsyncSession = Depends(get_db),
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> Envelope[dict[str, object]]:
    _require_n8n_auth(signature=None, token=x_internal_token)
    from lexflow_api.services.scheduled_workflow_service import ScheduledWorkflowService

    data = await ScheduledWorkflowService(session).run(slug)
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
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> Envelope[WorkflowActionResult]:
    _require_n8n_auth(signature=None, token=x_internal_token)
    data = await InternalWorkflowService(session).action_alert(slug, execution_id, reason)
    await session.commit()
    return envelope(data, _request_id(request))
