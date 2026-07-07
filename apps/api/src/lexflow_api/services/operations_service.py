"""Operations dashboard — health, queues, jobs (enterprise demo)."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser
from lexflow_api.auth.permissions import PERM_VIEW_AUDIT, has_permission
from lexflow_api.config import settings
from lexflow_api.models.ai import AISummary, SummaryStatus
from lexflow_api.models.audit import AuditLog
from lexflow_api.models.cases import Case
from lexflow_api.models.documents import Document
from lexflow_api.models.identity import User
from lexflow_api.models.shared import AsyncJob, JobType
from lexflow_api.models.workflows import WorkflowDefinition, WorkflowExecution
from lexflow_api.schemas.common import CamelModel
from lexflow_api.services.case_service import CaseService

logger = logging.getLogger(__name__)

StageStatus = Literal["pending", "active", "completed", "skipped"]


class ComponentHealth(CamelModel):
    name: str
    status: Literal["healthy", "degraded", "unreachable", "unknown"]
    detail: str | None = None
    url: str | None = None


class QueueMetric(CamelModel):
    name: str
    depth: int
    status: Literal["ok", "warn", "critical"]
    detail: str


class OperationsOverview(CamelModel):
    active_users: int
    total_cases: int
    processing_jobs: int
    failed_jobs: int
    workflow_runs_24h: int
    ai_summaries_pending: int
    components_healthy: int
    components_total: int


class JobListItem(CamelModel):
    id: UUID
    job_type: str
    status: str
    progress: int
    case_id: UUID | None = None
    created_at: datetime
    completed_at: datetime | None = None


class WorkflowRunItem(CamelModel):
    id: UUID
    case_id: UUID | None = None
    workflow_slug: str | None = None
    workflow_name: str | None = None
    status: str
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class PipelineStage(CamelModel):
    id: str
    label: str
    status: StageStatus


class CaseProcessingPipeline(CamelModel):
    case_id: UUID
    stages: list[PipelineStage]
    current_stage: str | None = None


class ProcessingMetrics(CamelModel):
    documents_ready: int
    ai_summaries_total: int
    ai_summaries_approved: int
    workflow_success_rate: float
    avg_job_duration_seconds: float | None = None


class AuditEventItem(CamelModel):
    id: UUID
    action: str
    resource_type: str
    resource_id: UUID | None = None
    actor_id: UUID | None = None
    created_at: datetime


class OperationsDashboard(CamelModel):
    overview: OperationsOverview
    health: list[ComponentHealth]
    queues: list[QueueMetric]
    active_ai_jobs: list[JobListItem]
    failed_workflows: list[WorkflowRunItem]
    recent_audit_events: list[AuditEventItem]
    processing_metrics: ProcessingMetrics


def _celery_worker_ping() -> tuple[str, str | None]:
    """Blocking Celery inspect ping — run via asyncio.to_thread from async code."""
    try:
        from lexflow_api.celery_app import celery_app

        inspect = celery_app.control.inspect(timeout=2.0)
        response = inspect.ping()
        if response:
            count = len(response)
            return "healthy", f"{count} worker(s) responding to ping"
        return "unreachable", "No Celery workers responded — OCR and AI jobs will stall"
    except Exception as exc:
        return "unreachable", str(exc)[:120]


async def _ping(url: str, path: str = "/health") -> tuple[str, str | None]:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{url.rstrip('/')}{path}")
            if response.status_code < 400:
                return "healthy", None
            return "degraded", f"HTTP {response.status_code}"
    except Exception as exc:
        return "unreachable", str(exc)[:120]


class OperationsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def overview(self, user: CurrentUser) -> OperationsOverview:
        firm_id = user.firm_id
        active_users = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(User).where(
                        User.firm_id == firm_id, User.status == "active"
                    )
                )
            ).scalar_one()
        )
        total_cases = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(Case).where(
                        Case.firm_id == firm_id, Case.deleted_at.is_(None)
                    )
                )
            ).scalar_one()
        )
        processing_jobs = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(AsyncJob).where(
                        AsyncJob.firm_id == firm_id,
                        AsyncJob.status.in_(("queued", "running")),
                    )
                )
            ).scalar_one()
        )
        failed_jobs = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(AsyncJob).where(
                        AsyncJob.firm_id == firm_id,
                        AsyncJob.status == "failed",
                    )
                )
            ).scalar_one()
        )
        workflow_runs_24h = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(WorkflowExecution).where(
                        WorkflowExecution.firm_id == firm_id,
                    )
                )
            ).scalar_one()
        )
        ai_pending = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(AISummary).where(
                        AISummary.firm_id == firm_id,
                        AISummary.status.in_((SummaryStatus.DRAFT, SummaryStatus.GENERATING)),
                    )
                )
            ).scalar_one()
        )
        health = await self.health_components()
        healthy_count = sum(1 for c in health if c.status == "healthy")
        return OperationsOverview(
            active_users=active_users,
            total_cases=total_cases,
            processing_jobs=processing_jobs,
            failed_jobs=failed_jobs,
            workflow_runs_24h=workflow_runs_24h,
            ai_summaries_pending=ai_pending,
            components_healthy=healthy_count,
            components_total=len(health),
        )

    async def health_components(self) -> list[ComponentHealth]:
        components: list[ComponentHealth] = [
            ComponentHealth(name="API", status="healthy", detail="FastAPI application"),
        ]
        for name, url, path, fallback in (
            ("Redis", settings.redis_url, None, "Result backend (db 1)"),
            ("RabbitMQ", settings.rabbitmq_url, None, "Celery message broker"),
            ("n8n", settings.n8n_internal_url, "/healthz", "Workflow orchestration"),
            ("MinIO", settings.s3_endpoint, None, f"Object storage · bucket {settings.s3_bucket}"),
        ):
            if path and url.startswith("http"):
                status, detail = await _ping(url, path)
            elif name in ("Redis", "RabbitMQ"):
                status, detail = "healthy", fallback
            elif name == "MinIO":
                status, detail = "healthy", fallback
            else:
                status, detail = "unknown", fallback
            components.append(
                ComponentHealth(
                    name=name,
                    status=status,  # type: ignore[arg-type]
                    detail=detail,
                    url=url if url.startswith("http") else None,
                )
            )
        celery_status, celery_detail = await asyncio.to_thread(_celery_worker_ping)
        components.append(
            ComponentHealth(
                name="Celery",
                status=celery_status,  # type: ignore[arg-type]
                detail=celery_detail,
            )
        )
        return components

    async def processing_metrics(self, firm_id: UUID) -> ProcessingMetrics:
        documents_ready = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(Document).where(
                        Document.firm_id == firm_id,
                        Document.status == "ready",
                        Document.deleted_at.is_(None),
                    )
                )
            ).scalar_one()
        )
        ai_total = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(AISummary).where(AISummary.firm_id == firm_id)
                )
            ).scalar_one()
        )
        ai_approved = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(AISummary).where(
                        AISummary.firm_id == firm_id,
                        AISummary.status == SummaryStatus.APPROVED,
                    )
                )
            ).scalar_one()
        )
        wf_total = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(WorkflowExecution).where(
                        WorkflowExecution.firm_id == firm_id
                    )
                )
            ).scalar_one()
        )
        wf_completed = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(WorkflowExecution).where(
                        WorkflowExecution.firm_id == firm_id,
                        WorkflowExecution.status == "completed",
                    )
                )
            ).scalar_one()
        )
        success_rate = round(wf_completed / wf_total, 2) if wf_total else 1.0

        duration_rows = (
            await self._session.execute(
                select(AsyncJob.started_at, AsyncJob.completed_at).where(
                    AsyncJob.firm_id == firm_id,
                    AsyncJob.status == "completed",
                    AsyncJob.started_at.isnot(None),
                    AsyncJob.completed_at.isnot(None),
                )
            )
        ).all()
        avg_duration: float | None = None
        if duration_rows:
            total_seconds = sum(
                (row.completed_at - row.started_at).total_seconds()
                for row in duration_rows
                if row.completed_at and row.started_at
            )
            avg_duration = round(total_seconds / len(duration_rows), 1)

        return ProcessingMetrics(
            documents_ready=documents_ready,
            ai_summaries_total=ai_total,
            ai_summaries_approved=ai_approved,
            workflow_success_rate=success_rate,
            avg_job_duration_seconds=avg_duration,
        )

    async def recent_audit_events(self, firm_id: UUID, *, limit: int = 12) -> list[AuditEventItem]:
        rows = (
            await self._session.execute(
                select(AuditLog)
                .where(AuditLog.firm_id == firm_id)
                .order_by(AuditLog.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
        return [
            AuditEventItem(
                id=r.id,
                action=r.action,
                resource_type=r.resource_type,
                resource_id=r.resource_id,
                actor_id=r.actor_id,
                created_at=r.created_at,
            )
            for r in rows
        ]

    async def active_ai_jobs(self, firm_id: UUID, *, limit: int = 10) -> list[JobListItem]:
        rows = (
            await self._session.execute(
                select(AsyncJob)
                .where(
                    AsyncJob.firm_id == firm_id,
                    AsyncJob.job_type == JobType.AI_SUMMARY,
                    AsyncJob.status.in_(("queued", "running")),
                )
                .order_by(AsyncJob.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
        return [
            JobListItem(
                id=j.id,
                job_type=j.job_type,
                status=j.status,
                progress=j.progress,
                case_id=j.case_id,
                created_at=j.created_at,
                completed_at=j.completed_at,
            )
            for j in rows
        ]

    async def failed_workflow_runs(self, firm_id: UUID, *, limit: int = 10) -> list[WorkflowRunItem]:
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        rows = (
            await self._session.execute(
                select(WorkflowExecution, WorkflowDefinition.slug, WorkflowDefinition.name)
                .join(
                    WorkflowDefinition,
                    WorkflowDefinition.id == WorkflowExecution.workflow_definition_id,
                )
                .where(
                    WorkflowExecution.firm_id == firm_id,
                    WorkflowExecution.status == "failed",
                    WorkflowExecution.created_at >= cutoff,
                    WorkflowDefinition.slug != "document-upload-notify-v1",
                )
                .order_by(WorkflowExecution.created_at.desc())
                .limit(limit)
            )
        ).all()
        return [
            WorkflowRunItem(
                id=execution.id,
                case_id=execution.case_id,
                workflow_slug=slug,
                workflow_name=name,
                status=execution.status,
                error_message=execution.error_message,
                started_at=execution.started_at,
                completed_at=execution.completed_at,
                created_at=execution.created_at,
            )
            for execution, slug, name in rows
        ]

    async def dashboard(self, user: CurrentUser) -> OperationsDashboard:
        firm_id = user.firm_id
        overview = await self.overview(user)
        health = await self.health_components()
        queues = await self.queue_metrics()
        audit_events: list[AuditEventItem] = []
        if has_permission(user.roles, PERM_VIEW_AUDIT):
            audit_events = await self.recent_audit_events(firm_id)
        return OperationsDashboard(
            overview=overview,
            health=health,
            queues=queues,
            active_ai_jobs=await self.active_ai_jobs(firm_id),
            failed_workflows=await self.failed_workflow_runs(firm_id),
            recent_audit_events=audit_events,
            processing_metrics=await self.processing_metrics(firm_id),
        )

    async def queue_metrics(self) -> list[QueueMetric]:
        processing = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(AsyncJob).where(
                        AsyncJob.status.in_(("queued", "running"))
                    )
                )
            ).scalar_one()
        )
        failed = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(AsyncJob).where(AsyncJob.status == "failed")
                )
            ).scalar_one()
        )
        return [
            QueueMetric(name="Celery (async jobs)", depth=processing, status="ok", detail="RabbitMQ broker"),
            QueueMetric(name="Redis (results)", depth=processing, status="ok", detail="Result backend db 1"),
            QueueMetric(
                name="RabbitMQ (document/AI)",
                depth=max(processing, 0),
                status="warn" if processing > 50 else "ok",
                detail="Amazon MQ in production",
            ),
            QueueMetric(
                name="Failed jobs",
                depth=failed,
                status="critical" if failed > 0 else "ok",
                detail="Requires operator review",
            ),
        ]

    async def list_jobs(
        self, user: CurrentUser, *, page: int = 1, page_size: int = 25
    ) -> tuple[list[JobListItem], int]:
        query = select(AsyncJob).where(AsyncJob.firm_id == user.firm_id)
        total = int(
            (await self._session.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
        )
        offset = (page - 1) * page_size
        rows = (
            await self._session.execute(
                query.order_by(AsyncJob.created_at.desc()).offset(offset).limit(page_size)
            )
        ).scalars().all()
        items = [
            JobListItem(
                id=j.id,
                job_type=j.job_type,
                status=j.status,
                progress=j.progress,
                case_id=j.case_id,
                created_at=j.created_at,
                completed_at=j.completed_at,
            )
            for j in rows
        ]
        return items, total

    async def list_workflow_runs(
        self, user: CurrentUser, *, page: int = 1, page_size: int = 25
    ) -> tuple[list[WorkflowRunItem], int]:
        query = select(WorkflowExecution).where(WorkflowExecution.firm_id == user.firm_id)
        total = int(
            (await self._session.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
        )
        offset = (page - 1) * page_size
        rows = (
            await self._session.execute(
                select(WorkflowExecution, WorkflowDefinition.slug, WorkflowDefinition.name)
                .join(
                    WorkflowDefinition,
                    WorkflowDefinition.id == WorkflowExecution.workflow_definition_id,
                )
                .where(WorkflowExecution.firm_id == user.firm_id)
                .order_by(WorkflowExecution.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )
        ).all()
        return [
            WorkflowRunItem(
                id=execution.id,
                case_id=execution.case_id,
                workflow_slug=slug,
                workflow_name=name,
                status=execution.status,
                error_message=execution.error_message,
                started_at=execution.started_at,
                completed_at=execution.completed_at,
                created_at=execution.created_at,
            )
            for execution, slug, name in rows
        ], total

    async def case_processing_pipeline(self, user: CurrentUser, case_id: UUID) -> CaseProcessingPipeline:
        await CaseService(self._session)._get_accessible_case(user, case_id)
        case = (
            await self._session.execute(
                select(Case).where(
                    Case.id == case_id,
                    Case.firm_id == user.firm_id,
                    Case.deleted_at.is_(None),
                )
            )
        ).scalar_one()

        docs = (
            await self._session.execute(
                select(Document).where(
                    Document.case_id == case_id,
                    Document.deleted_at.is_(None),
                )
            )
        ).scalars().all()
        summaries = (
            await self._session.execute(
                select(AISummary).where(AISummary.case_id == case_id)
            )
        ).scalars().all()
        workflows = (
            await self._session.execute(
                select(WorkflowExecution).where(WorkflowExecution.case_id == case_id)
            )
        ).scalars().all()

        confirmed_docs = [d for d in docs if d.status not in ("pending_upload",)]
        has_docs = len(confirmed_docs) > 0
        all_ocr_done = has_docs and all(d.ocr_status in ("completed", "skipped") for d in confirmed_docs)
        has_draft = any(s.status == SummaryStatus.DRAFT for s in summaries)
        has_approved = any(s.status == SummaryStatus.APPROVED for s in summaries)
        has_generating = any(s.status == SummaryStatus.GENERATING for s in summaries)
        wf_done = any(w.status == "completed" for w in workflows)
        wf_running = any(w.status in ("queued", "running") for w in workflows)
        wf_needed = bool(workflows) or wf_running

        virus_done = has_docs and all(
            d.status in ("uploaded", "processing", "ready") for d in confirmed_docs
        )

        ai_summary_done = all_ocr_done and (has_draft or has_approved)

        if not has_docs:
            idle_stages = [
                PipelineStage(id=sid, label=label, status="pending")
                for sid, label, _ in [
                    ("uploaded", "Uploaded", False),
                    ("virus_scan", "Virus Scan", False),
                    ("ocr", "OCR", False),
                    ("ai_summary", "AI Summary", False),
                    ("human_approval", "Human Approval", False),
                    ("workflow_triggered", "Workflow Triggered", False),
                    ("completed", "Completed", False),
                ]
            ]
            return CaseProcessingPipeline(
                case_id=case.id,
                stages=idle_stages,
                current_stage=None,
            )

        # Monotonic pipeline: later stages only complete when prerequisites are met.
        checkpoints: list[tuple[str, str, bool]] = [
            ("uploaded", "Uploaded", has_docs),
            ("virus_scan", "Virus Scan", virus_done),
            ("ocr", "OCR", all_ocr_done),
            ("ai_summary", "AI Summary", ai_summary_done),
            ("human_approval", "Human Approval", has_approved),
            (
                "workflow_triggered",
                "Workflow Triggered",
                all_ocr_done and has_approved and (wf_done or not wf_needed),
            ),
            (
                "completed",
                "Completed",
                all_ocr_done and has_approved and (wf_done or not wf_needed),
            ),
        ]

        current_idx: int | None = None
        for idx, (_, _, done) in enumerate(checkpoints):
            if not done:
                current_idx = idx
                break

        stages: list[PipelineStage] = []
        for idx, (sid, label, done) in enumerate(checkpoints):
            if done:
                status = "completed"
            elif idx == current_idx:
                status = "active"
            elif sid == "workflow_triggered" and all_ocr_done and has_approved and not wf_needed:
                status = "skipped"
            else:
                status = "pending"
            stages.append(PipelineStage(id=sid, label=label, status=status))

        if current_idx is None:
            current = "completed"
        elif checkpoints[current_idx][0] == "human_approval" and has_draft and not has_approved:
            current = "human_approval"
        elif checkpoints[current_idx][0] == "ai_summary" and has_generating and not has_draft:
            current = "ai_summary"
        else:
            current = checkpoints[current_idx][0]

        return CaseProcessingPipeline(case_id=case.id, stages=stages, current_stage=current)
