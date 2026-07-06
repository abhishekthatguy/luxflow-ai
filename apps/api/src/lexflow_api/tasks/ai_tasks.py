"""AI summary generation Celery tasks."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import select

from lexflow_api.celery_app import celery_app
from lexflow_api.db.sync_session import SyncSessionLocal
from lexflow_api.models.ai import AISummary, LLMUsage, PromptHistory, PromptTemplate, SummaryStatus
from lexflow_api.models.cases import Case
from lexflow_api.models.documents import Document
from lexflow_api.models.shared import AsyncJob
from lexflow_api.services.llm_stub import generate_stub_summary, redact_pii

logger = logging.getLogger(__name__)


@celery_app.task(name="lexflow_api.tasks.ai_tasks.generate_ai_summary")  # type: ignore[untyped-decorator]
def generate_ai_summary(summary_id: str, job_id: str) -> dict[str, str]:
    summary_uuid = UUID(summary_id)
    job_uuid = UUID(job_id)
    session = SyncSessionLocal()
    try:
        summary = session.execute(
            select(AISummary).where(AISummary.id == summary_uuid)
        ).scalar_one()
        job = session.execute(select(AsyncJob).where(AsyncJob.id == job_uuid)).scalar_one()
        case = session.execute(select(Case).where(Case.id == summary.case_id)).scalar_one()

        job.status = "running"
        job.progress = 20
        job.started_at = datetime.now(UTC)
        session.commit()

        context = case.description or case.title
        if summary.document_id:
            doc = session.execute(
                select(Document).where(Document.id == summary.document_id)
            ).scalar_one_or_none()
            if doc and doc.ocr_text:
                context = doc.ocr_text

        template = session.execute(
            select(PromptTemplate).where(
                PromptTemplate.slug == "document-summary-v1",
                PromptTemplate.is_active.is_(True),
            )
        ).scalar_one()

        rendered = template.template.replace("{{ case_title }}", case.title).replace(
            "{{ context }}", context[:4000]
        )
        llm_result = generate_stub_summary(
            case_title=case.title,
            context=context,
            summary_type=summary.summary_type,
        )

        summary.content = llm_result.content
        summary.status = SummaryStatus.DRAFT
        summary.token_count = llm_result.input_tokens + llm_result.output_tokens
        summary.model = llm_result.model
        summary.updated_at = datetime.now(UTC)

        history = PromptHistory(
            case_id=summary.case_id,
            firm_id=summary.firm_id,
            user_id=summary.requested_by,
            prompt_template_id=template.id,
            rendered_prompt=redact_pii(rendered),
            response=llm_result.content,
            model=llm_result.model,
            provider="azure_openai",
            input_tokens=llm_result.input_tokens,
            output_tokens=llm_result.output_tokens,
            status="success",
            correlation_id=job.correlation_id,
        )
        session.add(history)

        usage = session.execute(
            select(LLMUsage).where(
                LLMUsage.firm_id == summary.firm_id,
                LLMUsage.user_id == summary.requested_by,
                LLMUsage.case_id == summary.case_id,
                LLMUsage.provider == "stub",
                LLMUsage.model == llm_result.model,
                LLMUsage.period_start == date.today(),
            )
        ).scalar_one_or_none()
        if usage is None:
            usage = LLMUsage(
                firm_id=summary.firm_id,
                user_id=summary.requested_by,
                case_id=summary.case_id,
                provider="stub",
                model=llm_result.model,
                input_tokens=llm_result.input_tokens,
                output_tokens=llm_result.output_tokens,
                period_start=date.today(),
            )
            session.add(usage)
        else:
            usage.input_tokens += llm_result.input_tokens
            usage.output_tokens += llm_result.output_tokens

        job.status = "completed"
        job.progress = 100
        job.result = {
            "summaryId": str(summary.id),
            "resultUrl": f"/api/v1/ai/summaries/{summary.id}",
        }
        job.completed_at = datetime.now(UTC)
        session.commit()
        return {"status": "completed", "summaryId": summary_id}
    except Exception as exc:
        session.rollback()
        logger.exception("AI summary failed for %s", summary_id)
        summary = session.execute(
            select(AISummary).where(AISummary.id == summary_uuid)
        ).scalar_one_or_none()
        if summary:
            summary.status = SummaryStatus.FAILED
            session.commit()
        job = session.execute(select(AsyncJob).where(AsyncJob.id == job_uuid)).scalar_one_or_none()
        if job:
            job.status = "failed"
            job.error = {"message": str(exc)}
            job.completed_at = datetime.now(UTC)
            session.commit()
        return {"status": "failed", "error": str(exc)}
    finally:
        session.close()
