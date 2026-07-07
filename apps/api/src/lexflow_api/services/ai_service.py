from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser
from lexflow_api.auth.permissions import PERM_APPROVE_AI, PERM_REQUEST_AI, has_permission
from lexflow_api.exceptions import ConflictError, ForbiddenError, NotFoundError
from lexflow_api.models.ai import AISummary, PromptTemplate, SummaryStatus, SummaryType
from lexflow_api.models.cases import Case, CaseParticipant
from lexflow_api.models.documents import Document
from lexflow_api.schemas.ai import (
    AISummaryResponse,
    SummarizeRequest,
    SummaryRejectRequest,
    SummaryUpdateRequest,
)
from lexflow_api.schemas.jobs import JobAcceptedResponse
from lexflow_api.services.audit import write_audit_log
from lexflow_api.services.case_service import CaseService
from lexflow_api.services.job_service import JobService
from lexflow_api.services.outbox import write_outbox_event
from lexflow_api.services.timeline import write_timeline_event

def _can_approve(user_roles: set[str]) -> bool:
    return has_permission(user_roles, PERM_APPROVE_AI)


class AIService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._cases = CaseService(session)
        self._jobs = JobService(session)

    @staticmethod
    def to_response(summary: AISummary) -> AISummaryResponse:
        return AISummaryResponse(
            id=summary.id,
            case_id=summary.case_id,
            document_id=summary.document_id,
            summary_type=summary.summary_type,  # type: ignore[arg-type]
            content=summary.content,
            model=summary.model,
            prompt_version=summary.prompt_version,
            status=summary.status,
            approved_by=summary.approved_by,
            approved_at=summary.approved_at,
            rejection_reason=summary.rejection_reason,
            token_count=summary.token_count,
            requested_by=summary.requested_by,
            created_at=summary.created_at,
            updated_at=summary.updated_at,
        )

    async def request_summary(
        self, user: CurrentUser, case_id: UUID, data: SummarizeRequest
    ) -> JobAcceptedResponse:
        if not has_permission(user.roles, PERM_REQUEST_AI):
            raise ForbiddenError("Your role is not permitted to request AI summaries.")
        case = await self._cases._get_accessible_case(user, case_id)

        docs_result = await self._session.execute(
            select(Document).where(
                Document.case_id == case_id,
                Document.firm_id == user.firm_id,
                Document.deleted_at.is_(None),
            )
        )
        case_docs = docs_result.scalars().all()
        if not case_docs:
            raise ConflictError("Upload at least one document before generating a summary.")
        pending_ocr = [
            d.title
            for d in case_docs
            if d.ocr_status not in ("completed", "skipped")
        ]
        if pending_ocr:
            raise ConflictError(
                "All documents must finish OCR before generating a summary. "
                f"Still processing: {', '.join(pending_ocr)}"
            )

        if data.document_id:
            doc_result = await self._session.execute(
                select(Document).where(
                    Document.id == data.document_id,
                    Document.case_id == case_id,
                    Document.firm_id == user.firm_id,
                    Document.deleted_at.is_(None),
                )
            )
            if doc_result.scalar_one_or_none() is None:
                raise NotFoundError("Document not found.")

        template = await self._get_active_template("document-summary-v1")
        correlation_id = uuid4()

        summary = AISummary(
            case_id=case_id,
            document_id=data.document_id,
            firm_id=user.firm_id,
            summary_type=data.summary_type,
            model=str(template.llm_config.get("model", "stub-gpt-4o")),
            prompt_version=f"{template.slug}-v{template.version}",
            status=SummaryStatus.GENERATING,
            requested_by=user.id,
        )
        self._session.add(summary)
        await self._session.flush()

        job = await self._jobs.create_job(
            firm_id=user.firm_id,
            user_id=user.id,
            case_id=case_id,
            job_type="ai.summary",
            resource_type="ai_summary",
            resource_id=summary.id,
            correlation_id=correlation_id,
        )
        await write_outbox_event(
            self._session,
            firm_id=user.firm_id,
            aggregate_type="ai_summary",
            aggregate_id=summary.id,
            event_type="AiSummaryRequested",
            payload={"caseId": str(case_id), "summaryId": str(summary.id)},
        )
        await write_audit_log(
            self._session,
            firm_id=user.firm_id,
            actor_id=user.id,
            action="ai.summary.requested",
            resource_type="ai_summary",
            resource_id=summary.id,
            details={"caseTitle": case.title},
        )

        from lexflow_api.tasks.ai_tasks import generate_ai_summary

        await self._session.commit()
        generate_ai_summary.delay(str(summary.id), str(job.id))

        return JobAcceptedResponse(
            job_id=job.id,
            status="queued",
            status_url=f"/api/v1/jobs/{job.id}",
        )

    async def get_summary(self, user: CurrentUser, summary_id: UUID) -> AISummaryResponse:
        summary = await self._get_accessible_summary(user, summary_id)
        return self.to_response(summary)

    async def list_summaries(
        self, user: CurrentUser, case_id: UUID, *, page: int = 1, page_size: int = 25
    ) -> tuple[list[AISummaryResponse], int]:
        await self._cases._get_accessible_case(user, case_id)
        query = select(AISummary).where(
            AISummary.case_id == case_id,
            AISummary.firm_id == user.firm_id,
        )
        if not _can_approve(user.roles):
            query = query.where(
                (AISummary.status == SummaryStatus.APPROVED)
                | (AISummary.requested_by == user.id)
            )
        count_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = int(count_result.scalar_one())
        offset = (page - 1) * page_size
        result = await self._session.execute(
            query.order_by(AISummary.created_at.desc()).offset(offset).limit(page_size)
        )
        return [self.to_response(s) for s in result.scalars().all()], total

    async def update_draft_summary(
        self, user: CurrentUser, summary_id: UUID, data: SummaryUpdateRequest
    ) -> AISummaryResponse:
        if not _can_approve(user.roles):
            raise ForbiddenError("Your role is not permitted to approve AI summaries.")
        summary = await self._get_accessible_summary(user, summary_id)
        if summary.status != SummaryStatus.DRAFT:
            raise ConflictError("Only draft summaries can be edited.")
        summary.content = data.content
        summary.updated_at = datetime.now(UTC)
        await write_audit_log(
            self._session,
            firm_id=user.firm_id,
            actor_id=user.id,
            action="ai.summary.updated",
            resource_type="ai_summary",
            resource_id=summary.id,
            details={"caseId": str(summary.case_id)},
        )
        return self.to_response(summary)

    async def approve_summary(self, user: CurrentUser, summary_id: UUID) -> AISummaryResponse:
        if not _can_approve(user.roles):
            raise ForbiddenError("Your role is not permitted to approve AI summaries.")
        summary = await self._get_accessible_summary(user, summary_id)
        if summary.status != SummaryStatus.DRAFT:
            raise ConflictError("Only draft summaries can be approved.")
        summary.status = SummaryStatus.APPROVED
        summary.approved_by = user.id
        summary.approved_at = datetime.now(UTC)
        summary.updated_at = datetime.now(UTC)

        case = await self._cases._get_accessible_case(user, summary.case_id)

        await write_outbox_event(
            self._session,
            firm_id=user.firm_id,
            aggregate_type="ai_summary",
            aggregate_id=summary.id,
            event_type="AiSummaryApproved",
            payload={"caseId": str(summary.case_id), "summaryId": str(summary.id)},
        )
        await write_timeline_event(
            self._session,
            case_id=summary.case_id,
            firm_id=user.firm_id,
            event_type="AiSummaryApproved",
            title="Attorney approved AI summary",
            actor_id=user.id,
            payload={"summaryId": str(summary.id), "caseNumber": case.case_number},
        )
        await write_audit_log(
            self._session,
            firm_id=user.firm_id,
            actor_id=user.id,
            action="ai.summary.approved",
            resource_type="ai_summary",
            resource_id=summary.id,
            details={"caseId": str(summary.case_id), "caseNumber": case.case_number},
        )
        dispatch = await self._notify_summary_approved(summary, case, approver_id=user.id)
        await write_timeline_event(
            self._session,
            case_id=summary.case_id,
            firm_id=user.firm_id,
            event_type="notification.sent",
            title="Team notifications queued",
            actor_id=user.id,
            payload={
                "summaryId": str(summary.id),
                "emailQueued": dispatch["emailQueued"],
                "slackQueued": dispatch["slackQueued"],
                "teamsQueued": dispatch["teamsQueued"],
            },
        )
        from lexflow_api.schemas.ai import NotificationDispatchSummary

        response = self.to_response(summary)
        response.notification_dispatch = NotificationDispatchSummary(
            email_queued=dispatch["emailQueued"],
            slack_queued=dispatch["slackQueued"],
            teams_queued=dispatch["teamsQueued"],
            in_app_count=dispatch["inAppCount"],
            correlation_id=dispatch.get("correlationId"),
        )
        return response

    async def reject_summary(
        self, user: CurrentUser, summary_id: UUID, data: SummaryRejectRequest
    ) -> AISummaryResponse:
        if not _can_approve(user.roles):
            raise ForbiddenError("Your role is not permitted to approve AI summaries.")
        summary = await self._get_accessible_summary(user, summary_id)
        if summary.status != SummaryStatus.DRAFT:
            raise ConflictError("Only draft summaries can be rejected.")
        summary.status = SummaryStatus.REJECTED
        summary.rejection_reason = data.reason
        summary.updated_at = datetime.now(UTC)
        await write_audit_log(
            self._session,
            firm_id=user.firm_id,
            actor_id=user.id,
            action="ai.summary.rejected",
            resource_type="ai_summary",
            resource_id=summary.id,
        )
        return self.to_response(summary)

    async def _notify_summary_approved(
        self, summary: AISummary, case: Case, *, approver_id: UUID
    ) -> dict[str, int | str | None]:
        from lexflow_api.domain.notification_events import NotificationEventType
        from lexflow_api.services.notifications.helpers import emit_case_notification

        result = await emit_case_notification(
            self._session,
            event_type=NotificationEventType.AI_SUMMARY_APPROVED,
            firm_id=summary.firm_id,
            case_id=case.id,
            title="AI summary approved",
            description=f"Case {case.case_number}: attorney-approved summary is ready for the team.",
            status_badge="Approved",
            actor_id=approver_id,
            include_admin_emails=True,
            context={
                "current_stage": "Approved",
                "workflow_name": "AI Summary Approved",
                "recent_activity": ["AI summary approved by attorney"],
            },
        )
        return {
            "correlationId": str(result.correlation_id),
            "inAppCount": result.in_app_count,
            "emailQueued": result.email_queued,
            "teamsQueued": result.teams_queued,
            "slackQueued": result.slack_queued,
        }

    async def _get_active_template(self, slug: str) -> PromptTemplate:
        result = await self._session.execute(
            select(PromptTemplate).where(
                PromptTemplate.slug == slug,
                PromptTemplate.is_active.is_(True),
            )
        )
        template = result.scalar_one_or_none()
        if template is None:
            raise NotFoundError(f"Prompt template '{slug}' not found.")
        return template

    async def _get_accessible_summary(self, user: CurrentUser, summary_id: UUID) -> AISummary:
        result = await self._session.execute(
            select(AISummary).where(
                AISummary.id == summary_id,
                AISummary.firm_id == user.firm_id,
            )
        )
        summary = result.scalar_one_or_none()
        if summary is None:
            raise NotFoundError("Summary not found.")
        await self._cases._get_accessible_case(user, summary.case_id)
        if summary.status in (SummaryStatus.DRAFT, SummaryStatus.GENERATING):
            if summary.requested_by != user.id and not _can_approve(user.roles):
                raise NotFoundError("Summary not found.")
        elif summary.status != SummaryStatus.APPROVED:
            if summary.requested_by != user.id and not _can_approve(user.roles):
                raise NotFoundError("Summary not found.")
        return summary
