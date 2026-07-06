from datetime import datetime
from uuid import UUID

from lexflow_api.schemas.common import CamelModel


class WorkflowTriggerRequest(CamelModel):
    workflow_slug: str


class WorkflowExecutionResponse(CamelModel):
    id: UUID
    workflow_definition_id: UUID
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
