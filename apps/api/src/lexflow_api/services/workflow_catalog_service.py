from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser
from lexflow_api.auth.workflow_rbac import enrich_catalog_item
from lexflow_api.models.workflows import WorkflowDefinition, WorkflowExecution
from lexflow_api.schemas.workflows import (
    WorkflowCatalogExecutionItem,
    WorkflowCatalogItem,
    WorkflowExecutionDetailResponse,
)


class WorkflowCatalogService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_catalog(self, user: CurrentUser) -> list[WorkflowCatalogItem]:
        since = datetime.now(UTC) - timedelta(hours=24)
        result = await self._session.execute(
            select(WorkflowDefinition)
            .where(
                WorkflowDefinition.is_active.is_(True),
                or_(
                    WorkflowDefinition.firm_id.is_(None),
                    WorkflowDefinition.firm_id == user.firm_id,
                ),
            )
            .order_by(WorkflowDefinition.name)
        )
        definitions = result.scalars().all()
        items: list[WorkflowCatalogItem] = []

        for definition in definitions:
            meta: dict[str, object] = definition.config_schema or {}
            rbac = enrich_catalog_item(slug=definition.slug, meta=meta, user_roles=user.roles)
            tags_raw = meta.get("tags", [])
            tags = [str(t) for t in tags_raw] if isinstance(tags_raw, list) else []
            input_raw = meta.get("input", {})
            output_raw = meta.get("output", {})
            input_schema = dict(input_raw) if isinstance(input_raw, dict) else {}
            output_schema = dict(output_raw) if isinstance(output_raw, dict) else {}
            retries_raw = meta.get("retries", 3)
            retries = int(retries_raw) if isinstance(retries_raw, int) else 3
            last_result = await self._session.execute(
                select(WorkflowExecution)
                .where(
                    WorkflowExecution.workflow_definition_id == definition.id,
                    WorkflowExecution.firm_id == user.firm_id,
                )
                .order_by(WorkflowExecution.created_at.desc())
                .limit(1)
            )
            last_exec = last_result.scalar_one_or_none()

            count_result = await self._session.execute(
                select(func.count())
                .select_from(WorkflowExecution)
                .where(
                    WorkflowExecution.workflow_definition_id == definition.id,
                    WorkflowExecution.firm_id == user.firm_id,
                    WorkflowExecution.created_at >= since,
                )
            )
            count_24h = int(count_result.scalar_one())

            duration_ms: int | None = None
            if last_exec and last_exec.started_at and last_exec.completed_at:
                duration_ms = int(
                    (last_exec.completed_at - last_exec.started_at).total_seconds() * 1000
                )

            items.append(
                WorkflowCatalogItem(
                    slug=definition.slug,
                    name=definition.name,
                    description=definition.description,
                    trigger_type=definition.trigger_type,
                    category=str(meta.get("category", "")),
                    group=str(meta.get("group", "")),
                    tags=tags,
                    purpose=str(meta.get("purpose", "")),
                    summary=str(rbac["summary"]),
                    trigger=str(meta.get("trigger", definition.trigger_type)),
                    serial=int(rbac["serial"]),
                    scope=str(rbac["scope"]),
                    allowed_roles=list(rbac["allowed_roles"]),
                    automation_steps=list(rbac["automation_steps"]),
                    automated_by=str(rbac["automated_by"]),
                    can_trigger=bool(rbac["can_trigger"]),
                    is_test_trigger=bool(rbac["is_test_trigger"]),
                    input_schema=input_schema,
                    output_schema=output_schema,
                    retries=retries,
                    failure=str(meta.get("failure", "")),
                    owner=str(meta.get("owner", "")),
                    version=definition.version,
                    is_active=definition.is_active,
                    last_status=last_exec.status if last_exec else None,
                    last_executed_at=last_exec.created_at if last_exec else None,
                    executions_24h=count_24h,
                    last_duration_ms=duration_ms,
                    last_retry_count=last_exec.retry_count if last_exec else 0,
                )
            )
        items.sort(key=lambda item: item.serial or 999)
        return items

    async def list_for_case(self, user: CurrentUser, case_id: UUID) -> list[WorkflowCatalogItem]:
        """Catalog entries relevant to a case view (case-scoped + firm automations)."""
        from lexflow_api.services.case_service import CaseService

        await CaseService(self._session)._get_accessible_case(user, case_id)
        all_items = await self.list_catalog(user)
        return [item for item in all_items if item.scope in ("case", "firm")]

    async def list_executions(
        self, user: CurrentUser, slug: str, *, limit: int = 20
    ) -> list[WorkflowCatalogExecutionItem]:
        definition = await self._get_definition(slug)
        result = await self._session.execute(
            select(WorkflowExecution)
            .where(
                WorkflowExecution.workflow_definition_id == definition.id,
                WorkflowExecution.firm_id == user.firm_id,
            )
            .order_by(WorkflowExecution.created_at.desc())
            .limit(limit)
        )
        executions = result.scalars().all()
        items: list[WorkflowCatalogExecutionItem] = []
        for ex in executions:
            duration_ms: int | None = None
            if ex.started_at and ex.completed_at:
                duration_ms = int((ex.completed_at - ex.started_at).total_seconds() * 1000)
            items.append(
                WorkflowCatalogExecutionItem(
                    id=ex.id,
                    case_id=ex.case_id,
                    status=ex.status,
                    input_payload=ex.input_payload,
                    output_payload=ex.output_payload,
                    error_message=ex.error_message,
                    retry_count=ex.retry_count,
                    n8n_execution_id=ex.n8n_execution_id,
                    started_at=ex.started_at,
                    completed_at=ex.completed_at,
                    created_at=ex.created_at,
                    duration_ms=duration_ms,
                )
            )
        return items

    async def get_execution(
        self, user: CurrentUser, execution_id: UUID
    ) -> WorkflowExecutionDetailResponse:
        result = await self._session.execute(
            select(WorkflowExecution).where(
                WorkflowExecution.id == execution_id,
                WorkflowExecution.firm_id == user.firm_id,
            )
        )
        ex = result.scalar_one_or_none()
        if ex is None:
            from lexflow_api.exceptions import NotFoundError

            raise NotFoundError("Workflow execution not found.")

        duration_ms: int | None = None
        if ex.started_at and ex.completed_at:
            duration_ms = int((ex.completed_at - ex.started_at).total_seconds() * 1000)

        return WorkflowExecutionDetailResponse(
            id=ex.id,
            workflow_definition_id=ex.workflow_definition_id,
            case_id=ex.case_id,
            status=ex.status,
            input_payload=ex.input_payload,
            output_payload=ex.output_payload,
            error_message=ex.error_message,
            retry_count=ex.retry_count,
            max_retries=ex.max_retries,
            n8n_execution_id=ex.n8n_execution_id,
            correlation_id=ex.correlation_id,
            started_at=ex.started_at,
            completed_at=ex.completed_at,
            created_at=ex.created_at,
            duration_ms=duration_ms,
        )

    async def _get_definition(self, slug: str) -> WorkflowDefinition:
        result = await self._session.execute(
            select(WorkflowDefinition).where(
                WorkflowDefinition.slug == slug,
                WorkflowDefinition.is_active.is_(True),
            )
        )
        definition = result.scalar_one_or_none()
        if definition is None:
            from lexflow_api.exceptions import NotFoundError

            raise NotFoundError("Workflow definition not found.")
        return definition
