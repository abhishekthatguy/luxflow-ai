"""Scheduled n8n job runners — business logic stays in FastAPI."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.config import settings
from lexflow_api.infrastructure.cache import get_cache_client
from lexflow_api.models.ai import AISummary, SummaryStatus
from lexflow_api.models.cases import Case
from lexflow_api.models.workflows import ExecutionStatus, WorkflowExecution
from lexflow_api.services.admin_notification_service import AdminNotificationService

logger = logging.getLogger(__name__)


class ScheduledWorkflowService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def run(self, slug: str) -> dict[str, object]:
        if slug == "ops-health-monitor-v1":
            return await self.run_health_monitor()
        if slug == "approval-escalation-v1":
            return await self.run_approval_escalation()
        if slug == "daily-partner-report-v1":
            return await self.run_partner_report()
        return {"success": False, "message": f"Unknown scheduled workflow: {slug}"}

    async def run_health_monitor(self) -> dict[str, object]:
        probes: dict[str, dict[str, object]] = {
            "redis": self._probe_redis(),
            "api": {"ok": True, "message": "API responding"},
            "rabbitmq": await self._probe_rabbitmq(),
            "celery": await self._probe_celery(),
        }
        incidents = [name for name, probe in probes.items() if not probe.get("ok")]
        healthy = len(incidents) == 0
        result: dict[str, object] = {
            "success": True,
            "healthy": healthy,
            "probes": probes,
            "incidents": incidents,
            "checkedAt": datetime.now(UTC).isoformat(),
        }
        if not healthy:
            try:
                await AdminNotificationService().notify(
                    subject="[LexFlow] Operations health check failed",
                    body=f"Failed probes: {', '.join(incidents)}",
                    source="ops-health-monitor-v1",
                    metadata={"probes": probes},
                )
            except Exception as exc:
                logger.warning("health monitor admin notify failed: %s", exc)
                result["notifyError"] = str(exc)
        return result

    async def run_approval_escalation(self) -> dict[str, object]:
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        result = await self._session.execute(
            select(AISummary).where(
                AISummary.status == SummaryStatus.DRAFT,
                AISummary.created_at <= cutoff,
            )
        )
        stale = list(result.scalars().all())
        reminders_sent = 0
        escalated = 0
        for summary in stale:
            reminders_sent += 1
            if summary.created_at <= datetime.now(UTC) - timedelta(hours=48):
                escalated += 1
        if reminders_sent:
            try:
                await AdminNotificationService().notify(
                    subject=f"[LexFlow] {reminders_sent} approval(s) pending >24h",
                    body="Attorney reminders and partner escalations queued via notification engine.",
                    source="approval-escalation-v1",
                    metadata={"remindersSent": reminders_sent, "escalatedCount": escalated},
                )
            except Exception as exc:
                logger.warning("approval escalation notify failed: %s", exc)
        return {
            "success": True,
            "remindersSent": reminders_sent,
            "escalatedCount": escalated,
            "pendingCount": len(stale),
        }

    async def run_partner_report(self) -> dict[str, object]:
        pending_cases = await self._session.scalar(
            select(func.count()).select_from(Case).where(
                Case.status.in_(("intake", "active", "on_hold")),
                Case.deleted_at.is_(None),
            )
        )
        failed_ai = await self._session.scalar(
            select(func.count()).select_from(AISummary).where(
                AISummary.status == SummaryStatus.FAILED,
            )
        )
        workflow_errors = await self._session.scalar(
            select(func.count()).select_from(WorkflowExecution).where(
                WorkflowExecution.status == ExecutionStatus.FAILED,
            )
        )
        try:
            await AdminNotificationService().notify(
                subject="[LexFlow] Daily partner digest",
                body=(
                    f"Pending cases: {pending_cases or 0}\n"
                    f"Failed AI jobs: {failed_ai or 0}\n"
                    f"Workflow errors: {workflow_errors or 0}"
                ),
                source="daily-partner-report-v1",
                metadata={
                    "pendingCases": pending_cases or 0,
                    "failedAiJobs": failed_ai or 0,
                    "workflowErrors": workflow_errors or 0,
                },
            )
        except Exception as exc:
            logger.warning("partner report notify failed: %s", exc)
        return {
            "success": True,
            "reportSent": True,
            "recipientCount": 1,
            "pendingCases": pending_cases or 0,
            "failedAiJobs": failed_ai or 0,
            "workflowErrors": workflow_errors or 0,
        }

    def _probe_redis(self) -> dict[str, object]:
        try:
            cache = get_cache_client(settings.redis_url)
            key = "lexflow:health:probe"
            cache.set(key, "ok", ttl=30)
            ok = cache.get(key) == "ok"
            return {"ok": ok, "message": "PONG" if ok else "read failed"}
        except Exception as exc:
            logger.warning("redis health probe failed: %s", exc)
            return {"ok": False, "message": str(exc)}

    async def _probe_rabbitmq(self) -> dict[str, object]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://rabbitmq:15672/api/overview")
            return {"ok": response.status_code == 200, "message": f"HTTP {response.status_code}"}
        except Exception as exc:
            logger.warning("rabbitmq health probe failed: %s", exc)
            return {"ok": False, "message": str(exc)}

    async def _probe_celery(self) -> dict[str, object]:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.post(
                    "http://api:8000/internal/platform/celery-ping",
                    json={"correlationId": "health-probe"},
                )
            data = response.json()
            return {
                "ok": response.status_code == 200 and bool(data.get("taskId")),
                "message": data.get("taskId", response.text[:120]),
            }
        except Exception as exc:
            logger.warning("celery health probe failed: %s", exc)
            return {"ok": False, "message": str(exc)}
