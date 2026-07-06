from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser, get_current_user
from lexflow_api.db.session import get_db
from lexflow_api.schemas.common import Envelope, envelope
from lexflow_api.schemas.jobs import JobResponse
from lexflow_api.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


@router.get("/{job_id}", response_model=Envelope[JobResponse])
async def get_job(
    request: Request,
    job_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[JobResponse]:
    job = await JobService(session).get_job(user, job_id)
    return envelope(job, _request_id(request))
