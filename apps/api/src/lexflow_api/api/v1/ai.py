from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser, get_current_user
from lexflow_api.db.session import get_db
from lexflow_api.schemas.ai import AISummaryResponse, SummarizeRequest, SummaryRejectRequest
from lexflow_api.schemas.common import Envelope, envelope, pagination_meta
from lexflow_api.schemas.jobs import JobAcceptedResponse
from lexflow_api.services.ai_service import AIService

case_ai_router = APIRouter(prefix="/cases/{case_id}/ai", tags=["ai"])
ai_router = APIRouter(prefix="/ai", tags=["ai"])


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


@case_ai_router.post("/summarize", response_model=Envelope[JobAcceptedResponse], status_code=202)
async def request_case_summary(
    request: Request,
    case_id: UUID,
    body: SummarizeRequest,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[JobAcceptedResponse]:
    result = await AIService(session).request_summary(user, case_id, body)
    return envelope(result, _request_id(request))


@case_ai_router.get("/summaries", response_model=Envelope[list[AISummaryResponse]])
async def list_case_summaries(
    request: Request,
    case_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100, alias="pageSize"),
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[AISummaryResponse]]:
    summaries, total = await AIService(session).list_summaries(
        user, case_id, page=page, page_size=page_size
    )
    return envelope(summaries, _request_id(request), pagination_meta(page, page_size, total))


@ai_router.get("/summaries/{summary_id}", response_model=Envelope[AISummaryResponse])
async def get_summary(
    request: Request,
    summary_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[AISummaryResponse]:
    summary = await AIService(session).get_summary(user, summary_id)
    return envelope(summary, _request_id(request))


@ai_router.post("/summaries/{summary_id}/approve", response_model=Envelope[AISummaryResponse])
async def approve_summary(
    request: Request,
    summary_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[AISummaryResponse]:
    summary = await AIService(session).approve_summary(user, summary_id)
    return envelope(summary, _request_id(request))


@ai_router.post("/summaries/{summary_id}/reject", response_model=Envelope[AISummaryResponse])
async def reject_summary(
    request: Request,
    summary_id: UUID,
    body: SummaryRejectRequest,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[AISummaryResponse]:
    summary = await AIService(session).reject_summary(user, summary_id, body)
    return envelope(summary, _request_id(request))
