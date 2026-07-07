from datetime import datetime
from uuid import UUID

from lexflow_api.schemas.common import CamelModel


class WorkflowTriggerRequest(CamelModel):
    workflow_slug: str
    force: bool = False


class WorkflowTriggerResult(CamelModel):
    job_id: UUID
    status: str
    status_url: str
    execution_id: UUID | None = None
    deduplicated: bool = False


class WorkflowExecutionResponse(CamelModel):
    id: UUID
    workflow_definition_id: UUID
    workflow_slug: str | None = None
    workflow_name: str | None = None
    case_id: UUID | None = None
    status: str
    correlation_id: UUID
    n8n_execution_id: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime


class WorkflowStepResponse(CamelModel):
    id: UUID
    step_name: str
    step_order: int
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None


class N8nCallbackPayload(CamelModel):
    execution_id: UUID
    status: str
    n8n_execution_id: str | None = None
    output: dict[str, object] | None = None
    error_message: str | None = None


class WorkflowCatalogItem(CamelModel):
    slug: str
    name: str
    description: str | None = None
    trigger_type: str
    category: str = ""
    group: str = ""
    tags: list[str] = []
    purpose: str = ""
    summary: str = ""
    trigger: str = ""
    serial: int = 0
    scope: str = "case"
    allowed_roles: list[str] = []
    automation_steps: list[str] = []
    automated_by: str = ""
    can_trigger: bool = False
    is_test_trigger: bool = False
    input_schema: dict[str, object] = {}
    output_schema: dict[str, object] = {}
    retries: int = 3
    failure: str = ""
    owner: str = ""
    version: int = 1
    is_active: bool = True
    last_status: str | None = None
    last_executed_at: datetime | None = None
    executions_24h: int = 0
    last_duration_ms: int | None = None
    last_retry_count: int = 0


class WorkflowCatalogExecutionItem(CamelModel):
    id: UUID
    case_id: UUID | None = None
    status: str
    input_payload: dict[str, object] = {}
    output_payload: dict[str, object] | None = None
    error_message: str | None = None
    retry_count: int = 0
    n8n_execution_id: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    duration_ms: int | None = None


class WorkflowExecutionDetailResponse(CamelModel):
    id: UUID
    workflow_definition_id: UUID
    case_id: UUID | None = None
    status: str
    input_payload: dict[str, object] = {}
    output_payload: dict[str, object] | None = None
    error_message: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    n8n_execution_id: str | None = None
    correlation_id: UUID
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    duration_ms: int | None = None
