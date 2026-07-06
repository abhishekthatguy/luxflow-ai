from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser, get_current_user
from lexflow_api.db.session import get_db
from lexflow_api.schemas.cases import (
    CaseCreate,
    CaseResponse,
    CaseUpdate,
    ParticipantCreate,
    ParticipantResponse,
)
from lexflow_api.schemas.common import Envelope, envelope, pagination_meta
from lexflow_api.schemas.deadlines import DeadlineCreate, DeadlineResponse, DeadlineUpdate
from lexflow_api.schemas.hearings import HearingCreate, HearingResponse
from lexflow_api.schemas.notes import NoteCreate, NoteResponse
from lexflow_api.schemas.tasks import TaskCreate, TaskResponse, TaskUpdate
from lexflow_api.schemas.timeline import TimelineEventResponse
from lexflow_api.services.case_service import CaseService

router = APIRouter(prefix="/cases", tags=["cases"])


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


def _parse_if_match(if_match: str | None) -> int | None:
    if not if_match:
        return None
    value = if_match.strip().strip('"')
    try:
        return int(value)
    except ValueError:
        return None


@router.get("", response_model=Envelope[list[CaseResponse]])
async def list_cases(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100, alias="pageSize"),
    status: str | None = None,
    client_id: UUID | None = Query(None, alias="clientId"),
    search: str | None = None,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[CaseResponse]]:
    service = CaseService(session)
    cases, total = await service.list_cases(
        user, page=page, page_size=page_size, status=status, client_id=client_id, search=search
    )
    return envelope(cases, _request_id(request), pagination_meta(page, page_size, total))


@router.post("", response_model=Envelope[CaseResponse], status_code=201)
async def create_case(
    request: Request,
    body: CaseCreate,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[CaseResponse]:
    service = CaseService(session)
    case = await service.create_case(user, body)
    return envelope(case, _request_id(request))


@router.get("/{case_id}", response_model=Envelope[CaseResponse])
async def get_case(
    request: Request,
    case_id: UUID,
    response: Response,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[CaseResponse]:
    service = CaseService(session)
    case = await service.get_case(user, case_id)
    response.headers["ETag"] = f'"{case.version}"'
    return envelope(case, _request_id(request))


@router.patch("/{case_id}", response_model=Envelope[CaseResponse])
async def update_case(
    request: Request,
    case_id: UUID,
    body: CaseUpdate,
    response: Response,
    if_match: str | None = Header(None, alias="If-Match"),
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[CaseResponse]:
    service = CaseService(session)
    expected = _parse_if_match(if_match) if if_match else body.version
    case = await service.update_case(user, case_id, body, expected)
    response.headers["ETag"] = f'"{case.version}"'
    return envelope(case, _request_id(request))


@router.get("/{case_id}/participants", response_model=Envelope[list[ParticipantResponse]])
async def list_participants(
    request: Request,
    case_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[ParticipantResponse]]:
    service = CaseService(session)
    participants = await service.list_participants(user, case_id)
    return envelope(participants, _request_id(request))


@router.post(
    "/{case_id}/participants",
    response_model=Envelope[ParticipantResponse],
    status_code=201,
)
async def add_participant(
    request: Request,
    case_id: UUID,
    body: ParticipantCreate,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[ParticipantResponse]:
    service = CaseService(session)
    participant = await service.add_participant(user, case_id, body)
    return envelope(participant, _request_id(request))


@router.delete("/{case_id}/participants/{participant_id}", status_code=204)
async def remove_participant(
    case_id: UUID,
    participant_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    service = CaseService(session)
    await service.remove_participant(user, case_id, participant_id)


@router.get("/{case_id}/tasks", response_model=Envelope[list[TaskResponse]])
async def list_tasks(
    request: Request,
    case_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[TaskResponse]]:
    service = CaseService(session)
    tasks = await service.list_tasks(user, case_id)
    return envelope(tasks, _request_id(request))


@router.post("/{case_id}/tasks", response_model=Envelope[TaskResponse], status_code=201)
async def create_task(
    request: Request,
    case_id: UUID,
    body: TaskCreate,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[TaskResponse]:
    service = CaseService(session)
    task = await service.create_task(user, case_id, body)
    return envelope(task, _request_id(request))


@router.patch("/{case_id}/tasks/{task_id}", response_model=Envelope[TaskResponse])
async def update_task(
    request: Request,
    case_id: UUID,
    task_id: UUID,
    body: TaskUpdate,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[TaskResponse]:
    service = CaseService(session)
    task = await service.update_task(user, case_id, task_id, body)
    return envelope(task, _request_id(request))


@router.get("/{case_id}/deadlines", response_model=Envelope[list[DeadlineResponse]])
async def list_deadlines(
    request: Request,
    case_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[DeadlineResponse]]:
    service = CaseService(session)
    deadlines = await service.list_deadlines(user, case_id)
    return envelope(deadlines, _request_id(request))


@router.post("/{case_id}/deadlines", response_model=Envelope[DeadlineResponse], status_code=201)
async def create_deadline(
    request: Request,
    case_id: UUID,
    body: DeadlineCreate,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[DeadlineResponse]:
    service = CaseService(session)
    deadline = await service.create_deadline(user, case_id, body)
    return envelope(deadline, _request_id(request))


@router.patch("/{case_id}/deadlines/{deadline_id}", response_model=Envelope[DeadlineResponse])
async def update_deadline(
    request: Request,
    case_id: UUID,
    deadline_id: UUID,
    body: DeadlineUpdate,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[DeadlineResponse]:
    service = CaseService(session)
    deadline = await service.update_deadline(user, case_id, deadline_id, body)
    return envelope(deadline, _request_id(request))


@router.get("/{case_id}/hearings", response_model=Envelope[list[HearingResponse]])
async def list_hearings(
    request: Request,
    case_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[HearingResponse]]:
    service = CaseService(session)
    hearings = await service.list_hearings(user, case_id)
    return envelope(hearings, _request_id(request))


@router.post("/{case_id}/hearings", response_model=Envelope[HearingResponse], status_code=201)
async def create_hearing(
    request: Request,
    case_id: UUID,
    body: HearingCreate,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[HearingResponse]:
    service = CaseService(session)
    hearing = await service.create_hearing(user, case_id, body)
    return envelope(hearing, _request_id(request))


@router.get("/{case_id}/notes", response_model=Envelope[list[NoteResponse]])
async def list_notes(
    request: Request,
    case_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[NoteResponse]]:
    service = CaseService(session)
    notes = await service.list_notes(user, case_id)
    return envelope(notes, _request_id(request))


@router.post("/{case_id}/notes", response_model=Envelope[NoteResponse], status_code=201)
async def create_note(
    request: Request,
    case_id: UUID,
    body: NoteCreate,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[NoteResponse]:
    service = CaseService(session)
    note = await service.create_note(user, case_id, body)
    return envelope(note, _request_id(request))


@router.get("/{case_id}/timeline", response_model=Envelope[list[TimelineEventResponse]])
async def list_timeline(
    request: Request,
    case_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100, alias="pageSize"),
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[TimelineEventResponse]]:
    service = CaseService(session)
    events, total = await service.list_timeline(user, case_id, page=page, page_size=page_size)
    return envelope(events, _request_id(request), pagination_meta(page, page_size, total))
