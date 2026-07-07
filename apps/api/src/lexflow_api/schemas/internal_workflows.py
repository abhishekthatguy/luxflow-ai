from uuid import UUID

from lexflow_api.schemas.common import CamelModel


class WorkflowInitializeRequest(CamelModel):
    execution_id: UUID
    case_id: UUID | None = None
    payload: dict[str, object] = {}


class WorkflowInitializeResponse(CamelModel):
    authorized: bool
    slug: str
    execution_id: UUID
    case_id: UUID | None = None
    firm_id: UUID
    document_id: UUID | None = None
    flags: dict[str, bool]
    callback_url: str
    step_url: str


class WorkflowCaseContext(CamelModel):
    execution_id: UUID
    case_id: UUID
    case_number: str
    title: str
    status: str
    practice_area: str
    lead_attorney_id: UUID | None = None


class WorkflowOcrStatus(CamelModel):
    document_id: UUID
    ocr_status: str
    ocr_complete: bool
    title: str
    attempt: int = 1


class WorkflowActionResult(CamelModel):
    success: bool
    message: str
    data: dict[str, object] = {}


class WorkflowStepPayload(CamelModel):
    execution_id: UUID
    step_name: str
    step_order: int
    status: str = "completed"
    metadata: dict[str, object] = {}
    error_message: str | None = None
