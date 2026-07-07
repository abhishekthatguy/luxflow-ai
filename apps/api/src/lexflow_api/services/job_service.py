from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser
from lexflow_api.exceptions import NotFoundError
from lexflow_api.models.shared import AsyncJob
from lexflow_api.schemas.jobs import JobResponse


class JobService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def to_response(job: AsyncJob) -> JobResponse:
        return JobResponse(
            id=job.id,
            job_type=job.job_type,
            status=job.status,
            progress=job.progress,
            case_id=job.case_id,
            resource_type=job.resource_type,
            resource_id=job.resource_id,
            result=job.result,
            error=job.error,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )

    async def get_job(self, user: CurrentUser, job_id: UUID) -> JobResponse:
        result = await self._session.execute(
            select(AsyncJob).where(
                AsyncJob.id == job_id,
                AsyncJob.firm_id == user.firm_id,
            )
        )
        job = result.scalar_one_or_none()
        if job is None:
            raise NotFoundError("Job not found.")
        if job.user_id != user.id:
            raise NotFoundError("Job not found.")
        return self.to_response(job)

    async def find_for_resource(
        self, resource_type: str, resource_id: UUID
    ) -> AsyncJob | None:
        result = await self._session.execute(
            select(AsyncJob).where(
                AsyncJob.resource_type == resource_type,
                AsyncJob.resource_id == resource_id,
            ).order_by(AsyncJob.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def create_job(
        self,
        *,
        firm_id: UUID,
        user_id: UUID,
        case_id: UUID | None,
        job_type: str,
        resource_type: str,
        resource_id: UUID,
        correlation_id: UUID,
    ) -> AsyncJob:
        job = AsyncJob(
            firm_id=firm_id,
            user_id=user_id,
            case_id=case_id,
            job_type=job_type,
            status="queued",
            resource_type=resource_type,
            resource_id=resource_id,
            correlation_id=correlation_id,
        )
        self._session.add(job)
        await self._session.flush()
        return job

    async def mark_running(self, job_id: UUID, progress: int = 10) -> None:
        result = await self._session.execute(select(AsyncJob).where(AsyncJob.id == job_id))
        job = result.scalar_one()
        job.status = "running"
        job.progress = progress
        job.started_at = datetime.now(UTC)
        job.updated_at = datetime.now(UTC)

    async def mark_completed(
        self, job_id: UUID, *, result: dict[str, object], progress: int = 100
    ) -> None:
        result_row = await self._session.execute(select(AsyncJob).where(AsyncJob.id == job_id))
        job = result_row.scalar_one()
        job.status = "completed"
        job.progress = progress
        job.result = result
        job.completed_at = datetime.now(UTC)
        job.updated_at = datetime.now(UTC)

    async def mark_failed(self, job_id: UUID, *, error: dict[str, object]) -> None:
        result_row = await self._session.execute(select(AsyncJob).where(AsyncJob.id == job_id))
        job = result_row.scalar_one()
        job.status = "failed"
        job.error = error
        job.completed_at = datetime.now(UTC)
        job.updated_at = datetime.now(UTC)
