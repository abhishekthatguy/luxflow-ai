from datetime import datetime
from uuid import UUID

from pydantic import Field

from lexflow_api.models.cases import Priority, TaskStatus
from lexflow_api.schemas.common import CamelModel


class TaskCreate(CamelModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.NORMAL
    assigned_to: UUID | None = None
    due_at: datetime | None = None


class TaskUpdate(CamelModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    status: TaskStatus | None = None
    priority: Priority | None = None
    assigned_to: UUID | None = None
    due_at: datetime | None = None
    version: int | None = None


class TaskResponse(CamelModel):
    id: UUID
    case_id: UUID
    title: str
    description: str | None = None
    status: TaskStatus
    priority: Priority
    assigned_to: UUID | None = None
    due_at: datetime | None = None
    completed_at: datetime | None = None
    created_by: UUID
    version: int
    created_at: datetime
    updated_at: datetime
