from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser, get_current_user
from lexflow_api.db.session import get_db
from lexflow_api.schemas.common import Envelope, envelope, pagination_meta
from lexflow_api.schemas.jobs import JobAcceptedResponse
from lexflow_api.schemas.workflows import (
    WorkflowExecutionResponse,
    WorkflowStepResponse,
    WorkflowTriggerRequest,
)
from lexflow_api.services.workflow_service import WorkflowService

router = APIRouter(prefix="/cases/{case_id}/workflows", tags=["workflows"])


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


@router.post("/trigger", response_model=Envelope[JobAcceptedResponse], status_code=202)
async def trigger_workflow(
    request: Request,
    case_id: UUID,
    body: WorkflowTriggerRequest,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[JobAcceptedResponse]:
    result = await WorkflowService(session).trigger_workflow(user, case_id, body)
    return envelope(result, _request_id(request))


@router.get("", response_model=Envelope[list[WorkflowExecutionResponse]])
async def list_workflow_executions(
    request: Request,
    case_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100, alias="pageSize"),
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[WorkflowExecutionResponse]]:
    executions, total = await WorkflowService(session).list_executions(
        user, case_id, page=page, page_size=page_size
    )
    return envelope(executions, _request_id(request), pagination_meta(page, page_size, total))


@router.get("/executions/{execution_id}/steps", response_model=Envelope[list[WorkflowStepResponse]])
async def list_workflow_steps(
    request: Request,
    case_id: UUID,
    execution_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[WorkflowStepResponse]]:
    steps = await WorkflowService(session).list_steps(user, execution_id)
    return envelope(steps, _request_id(request))
