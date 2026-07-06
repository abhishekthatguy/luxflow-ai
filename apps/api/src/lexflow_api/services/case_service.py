from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser
from lexflow_api.auth.matter_wall import get_participant_role, user_can_access_case
from lexflow_api.auth.rbac import FIRM_WIDE_ACCESS_ROLES, can_manage_participants, has_any_role
from lexflow_api.exceptions import ConflictError, ForbiddenError, NotFoundError
from lexflow_api.models.cases import (
    Case,
    CaseParticipant,
    CaseTimelineEvent,
    Client,
    Deadline,
    Hearing,
    Note,
    ParticipantRole,
    Task,
    TaskStatus,
)
from lexflow_api.schemas.cases import (
    CaseCreate,
    CaseResponse,
    CaseUpdate,
    ParticipantCreate,
    ParticipantResponse,
)
from lexflow_api.schemas.deadlines import DeadlineCreate, DeadlineResponse, DeadlineUpdate
from lexflow_api.schemas.hearings import HearingCreate, HearingResponse
from lexflow_api.schemas.notes import NoteCreate, NoteResponse
from lexflow_api.schemas.tasks import TaskCreate, TaskResponse, TaskUpdate
from lexflow_api.schemas.timeline import TimelineEventResponse
from lexflow_api.services.audit import write_audit_log
from lexflow_api.services.outbox import write_outbox_event
from lexflow_api.services.timeline import write_timeline_event


class CaseService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def to_case_response(case: Case) -> CaseResponse:
        return CaseResponse(
            id=case.id,
            firm_id=case.firm_id,
            client_id=case.client_id,
            case_number=case.case_number,
            title=case.title,
            practice_area=case.practice_area,
            status=case.status,  # type: ignore[arg-type]
            priority=case.priority,  # type: ignore[arg-type]
            lead_attorney_id=case.lead_attorney_id,
            description=case.description,
            opened_at=case.opened_at,
            closed_at=case.closed_at,
            metadata=case.metadata_,
            version=case.version,
            created_at=case.created_at,
            updated_at=case.updated_at,
        )

    async def list_cases(
        self,
        user: CurrentUser,
        *,
        page: int = 1,
        page_size: int = 25,
        status: str | None = None,
        client_id: UUID | None = None,
        search: str | None = None,
    ) -> tuple[list[CaseResponse], int]:
        query = select(Case).where(Case.firm_id == user.firm_id, Case.deleted_at.is_(None))

        if not has_any_role(user.roles, FIRM_WIDE_ACCESS_ROLES):
            participant_subq = select(CaseParticipant.case_id).where(
                CaseParticipant.user_id == user.id
            )
            query = query.where(Case.id.in_(participant_subq))

        if status:
            query = query.where(Case.status == status)
        if client_id:
            query = query.where(Case.client_id == client_id)
        if search:
            query = query.where(
                or_(Case.title.ilike(f"%{search}%"), Case.case_number.ilike(f"%{search}%"))
            )

        count_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = int(count_result.scalar_one())
        offset = (page - 1) * page_size
        result = await self._session.execute(
            query.order_by(Case.created_at.desc()).offset(offset).limit(page_size)
        )
        cases = result.scalars().all()
        return [self.to_case_response(c) for c in cases], total

    async def get_case(self, user: CurrentUser, case_id: UUID) -> CaseResponse:
        case = await self._get_accessible_case(user, case_id)
        return self.to_case_response(case)

    async def create_case(self, user: CurrentUser, data: CaseCreate) -> CaseResponse:
        client = await self._session.execute(
            select(Client).where(
                Client.id == data.client_id,
                Client.firm_id == user.firm_id,
                Client.deleted_at.is_(None),
            )
        )
        if client.scalar_one_or_none() is None:
            raise NotFoundError("Client not found.")

        case = Case(
            firm_id=user.firm_id,
            client_id=data.client_id,
            case_number=data.case_number,
            title=data.title,
            practice_area=data.practice_area,
            status=data.status.value,
            priority=data.priority.value,
            lead_attorney_id=data.lead_attorney_id,
            description=data.description,
            metadata_=data.metadata,
            opened_at=datetime.now(UTC),
        )
        self._session.add(case)
        await self._session.flush()

        participant = CaseParticipant(
            case_id=case.id,
            user_id=data.lead_attorney_id,
            role=ParticipantRole.LEAD.value,
            added_by=user.id,
        )
        self._session.add(participant)
        await self._session.flush()

        await write_audit_log(
            self._session,
            firm_id=user.firm_id,
            actor_id=user.id,
            action="case.created",
            resource_type="case",
            resource_id=case.id,
            details={"caseNumber": case.case_number},
        )
        await write_outbox_event(
            self._session,
            firm_id=user.firm_id,
            aggregate_type="case",
            aggregate_id=case.id,
            event_type="CaseCreated",
            payload={"caseId": str(case.id), "caseNumber": case.case_number},
        )
        await write_timeline_event(
            self._session,
            case_id=case.id,
            firm_id=user.firm_id,
            event_type="CaseCreated",
            title=f"Case {case.case_number} created",
            actor_id=user.id,
            payload={"caseNumber": case.case_number},
        )
        return self.to_case_response(case)

    async def update_case(
        self, user: CurrentUser, case_id: UUID, data: CaseUpdate, expected_version: int | None
    ) -> CaseResponse:
        case = await self._get_accessible_case(user, case_id)
        if expected_version is not None and expected_version != case.version:
            raise ConflictError("Case version mismatch.")

        if data.title is not None:
            case.title = data.title
        if data.practice_area is not None:
            case.practice_area = data.practice_area
        if data.status is not None:
            case.status = data.status.value
        if data.priority is not None:
            case.priority = data.priority.value
        if data.lead_attorney_id is not None:
            case.lead_attorney_id = data.lead_attorney_id
        if data.description is not None:
            case.description = data.description
        if data.metadata is not None:
            case.metadata_ = data.metadata

        case.version += 1
        case.updated_at = datetime.now(UTC)
        await write_audit_log(
            self._session,
            firm_id=user.firm_id,
            actor_id=user.id,
            action="case.updated",
            resource_type="case",
            resource_id=case.id,
        )
        return self.to_case_response(case)

    async def list_participants(
        self, user: CurrentUser, case_id: UUID
    ) -> list[ParticipantResponse]:
        await self._get_accessible_case(user, case_id)
        result = await self._session.execute(
            select(CaseParticipant).where(CaseParticipant.case_id == case_id)
        )
        return [self._participant_response(p) for p in result.scalars().all()]

    async def add_participant(
        self, user: CurrentUser, case_id: UUID, data: ParticipantCreate
    ) -> ParticipantResponse:
        await self._get_accessible_case(user, case_id)
        role = await get_participant_role(self._session, user_id=user.id, case_id=case_id)
        if not can_manage_participants(user.roles, role):
            raise ForbiddenError("Only lead attorney or administrators can manage participants.")

        existing = await self._session.execute(
            select(CaseParticipant).where(
                CaseParticipant.case_id == case_id,
                CaseParticipant.user_id == data.user_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictError("User is already a participant.")

        participant = CaseParticipant(
            case_id=case_id,
            user_id=data.user_id,
            role=data.role.value,
            added_by=user.id,
        )
        self._session.add(participant)
        await self._session.flush()

        await write_audit_log(
            self._session,
            firm_id=user.firm_id,
            actor_id=user.id,
            action="case.participant.added",
            resource_type="case_participant",
            resource_id=participant.id,
            details={"caseId": str(case_id), "userId": str(data.user_id)},
        )
        await write_outbox_event(
            self._session,
            firm_id=user.firm_id,
            aggregate_type="case",
            aggregate_id=case_id,
            event_type="CaseParticipantAdded",
            payload={"caseId": str(case_id), "userId": str(data.user_id), "role": data.role.value},
        )
        await write_timeline_event(
            self._session,
            case_id=case_id,
            firm_id=user.firm_id,
            event_type="CaseParticipantAdded",
            title="Participant added to case",
            actor_id=user.id,
            payload={"userId": str(data.user_id), "role": data.role.value},
        )
        return self._participant_response(participant)

    async def remove_participant(
        self, user: CurrentUser, case_id: UUID, participant_id: UUID
    ) -> None:
        await self._get_accessible_case(user, case_id)
        role = await get_participant_role(self._session, user_id=user.id, case_id=case_id)
        if not can_manage_participants(user.roles, role):
            raise ForbiddenError("Only lead attorney or administrators can manage participants.")

        result = await self._session.execute(
            select(CaseParticipant).where(
                CaseParticipant.id == participant_id,
                CaseParticipant.case_id == case_id,
            )
        )
        participant = result.scalar_one_or_none()
        if participant is None:
            raise NotFoundError("Participant not found.")

        await self._session.delete(participant)
        await write_audit_log(
            self._session,
            firm_id=user.firm_id,
            actor_id=user.id,
            action="case.participant.removed",
            resource_type="case_participant",
            resource_id=participant_id,
            details={"caseId": str(case_id)},
        )

    async def list_tasks(self, user: CurrentUser, case_id: UUID) -> list[TaskResponse]:
        await self._get_accessible_case(user, case_id)
        result = await self._session.execute(
            select(Task).where(Task.case_id == case_id).order_by(Task.created_at.desc())
        )
        return [self._task_response(t) for t in result.scalars().all()]

    async def create_task(self, user: CurrentUser, case_id: UUID, data: TaskCreate) -> TaskResponse:
        await self._get_accessible_case(user, case_id)
        task = Task(
            case_id=case_id,
            title=data.title,
            description=data.description,
            status=data.status.value,
            priority=data.priority.value,
            assigned_to=data.assigned_to,
            due_at=data.due_at,
            created_by=user.id,
        )
        self._session.add(task)
        await self._session.flush()
        await write_audit_log(
            self._session,
            firm_id=user.firm_id,
            actor_id=user.id,
            action="task.created",
            resource_type="task",
            resource_id=task.id,
            details={"caseId": str(case_id)},
        )
        return self._task_response(task)

    async def update_task(
        self, user: CurrentUser, case_id: UUID, task_id: UUID, data: TaskUpdate
    ) -> TaskResponse:
        await self._get_accessible_case(user, case_id)
        result = await self._session.execute(
            select(Task).where(Task.id == task_id, Task.case_id == case_id)
        )
        task = result.scalar_one_or_none()
        if task is None:
            raise NotFoundError("Task not found.")

        previous_status = task.status
        if data.title is not None:
            task.title = data.title
        if data.description is not None:
            task.description = data.description
        if data.status is not None:
            task.status = data.status.value
            if data.status == TaskStatus.COMPLETED:
                task.completed_at = datetime.now(UTC)
        if data.priority is not None:
            task.priority = data.priority.value
        if data.assigned_to is not None:
            task.assigned_to = data.assigned_to
        if data.due_at is not None:
            task.due_at = data.due_at

        task.version += 1
        task.updated_at = datetime.now(UTC)
        await write_audit_log(
            self._session,
            firm_id=user.firm_id,
            actor_id=user.id,
            action="task.updated",
            resource_type="task",
            resource_id=task.id,
        )

        completed = TaskStatus.COMPLETED.value
        if previous_status != completed and task.status == completed:
            await write_outbox_event(
                self._session,
                firm_id=user.firm_id,
                aggregate_type="task",
                aggregate_id=task.id,
                event_type="TaskCompleted",
                payload={"taskId": str(task.id), "caseId": str(case_id)},
            )
            await write_timeline_event(
                self._session,
                case_id=case_id,
                firm_id=user.firm_id,
                event_type="TaskCompleted",
                title=f"Task completed: {task.title}",
                actor_id=user.id,
                payload={"taskId": str(task.id)},
            )

        return self._task_response(task)

    async def list_deadlines(self, user: CurrentUser, case_id: UUID) -> list[DeadlineResponse]:
        await self._get_accessible_case(user, case_id)
        result = await self._session.execute(
            select(Deadline).where(Deadline.case_id == case_id).order_by(Deadline.deadline_at)
        )
        return [self._deadline_response(d) for d in result.scalars().all()]

    async def create_deadline(
        self, user: CurrentUser, case_id: UUID, data: DeadlineCreate
    ) -> DeadlineResponse:
        await self._get_accessible_case(user, case_id)
        deadline = Deadline(
            case_id=case_id,
            title=data.title,
            deadline_at=data.deadline_at,
            type=data.type.value,
            status=data.status.value,
            created_by=user.id,
        )
        self._session.add(deadline)
        await self._session.flush()
        await write_audit_log(
            self._session,
            firm_id=user.firm_id,
            actor_id=user.id,
            action="deadline.created",
            resource_type="deadline",
            resource_id=deadline.id,
        )
        return self._deadline_response(deadline)

    async def update_deadline(
        self, user: CurrentUser, case_id: UUID, deadline_id: UUID, data: DeadlineUpdate
    ) -> DeadlineResponse:
        await self._get_accessible_case(user, case_id)
        result = await self._session.execute(
            select(Deadline).where(Deadline.id == deadline_id, Deadline.case_id == case_id)
        )
        deadline = result.scalar_one_or_none()
        if deadline is None:
            raise NotFoundError("Deadline not found.")

        if data.title is not None:
            deadline.title = data.title
        if data.deadline_at is not None:
            deadline.deadline_at = data.deadline_at
        if data.type is not None:
            deadline.type = data.type.value
        if data.status is not None:
            deadline.status = data.status.value

        deadline.updated_at = datetime.now(UTC)
        await write_audit_log(
            self._session,
            firm_id=user.firm_id,
            actor_id=user.id,
            action="deadline.updated",
            resource_type="deadline",
            resource_id=deadline.id,
        )
        return self._deadline_response(deadline)

    async def list_hearings(self, user: CurrentUser, case_id: UUID) -> list[HearingResponse]:
        await self._get_accessible_case(user, case_id)
        result = await self._session.execute(
            select(Hearing).where(Hearing.case_id == case_id).order_by(Hearing.hearing_at)
        )
        return [self._hearing_response(h) for h in result.scalars().all()]

    async def create_hearing(
        self, user: CurrentUser, case_id: UUID, data: HearingCreate
    ) -> HearingResponse:
        await self._get_accessible_case(user, case_id)
        hearing = Hearing(
            case_id=case_id,
            title=data.title,
            hearing_at=data.hearing_at,
            location=data.location,
            court=data.court,
            judge=data.judge,
            notes=data.notes,
            created_by=user.id,
        )
        self._session.add(hearing)
        await self._session.flush()
        await write_audit_log(
            self._session,
            firm_id=user.firm_id,
            actor_id=user.id,
            action="hearing.created",
            resource_type="hearing",
            resource_id=hearing.id,
        )
        return self._hearing_response(hearing)

    async def list_notes(self, user: CurrentUser, case_id: UUID) -> list[NoteResponse]:
        await self._get_accessible_case(user, case_id)
        result = await self._session.execute(
            select(Note).where(Note.case_id == case_id).order_by(Note.created_at.desc())
        )
        return [self._note_response(n) for n in result.scalars().all()]

    async def create_note(self, user: CurrentUser, case_id: UUID, data: NoteCreate) -> NoteResponse:
        await self._get_accessible_case(user, case_id)
        note = Note(
            case_id=case_id,
            author_id=user.id,
            body=data.body,
            visibility=data.visibility.value,
        )
        self._session.add(note)
        await self._session.flush()
        await write_audit_log(
            self._session,
            firm_id=user.firm_id,
            actor_id=user.id,
            action="note.created",
            resource_type="note",
            resource_id=note.id,
        )
        return self._note_response(note)

    async def list_timeline(
        self, user: CurrentUser, case_id: UUID, *, page: int = 1, page_size: int = 25
    ) -> tuple[list[TimelineEventResponse], int]:
        await self._get_accessible_case(user, case_id)
        query = select(CaseTimelineEvent).where(CaseTimelineEvent.case_id == case_id)
        count_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = int(count_result.scalar_one())
        offset = (page - 1) * page_size
        result = await self._session.execute(
            query.order_by(CaseTimelineEvent.occurred_at.desc()).offset(offset).limit(page_size)
        )
        events = [self._timeline_response(e) for e in result.scalars().all()]
        return events, total

    async def _get_accessible_case(self, user: CurrentUser, case_id: UUID) -> Case:
        result = await self._session.execute(
            select(Case).where(
                Case.id == case_id,
                Case.firm_id == user.firm_id,
                Case.deleted_at.is_(None),
            )
        )
        case = result.scalar_one_or_none()
        if case is None:
            raise NotFoundError("Case not found.")

        allowed = await user_can_access_case(
            self._session,
            user_id=user.id,
            firm_id=user.firm_id,
            user_roles=user.roles,
            case_id=case_id,
        )
        if not allowed:
            raise NotFoundError("Case not found.")
        return case

    @staticmethod
    def _participant_response(participant: CaseParticipant) -> ParticipantResponse:
        return ParticipantResponse(
            id=participant.id,
            case_id=participant.case_id,
            user_id=participant.user_id,
            role=participant.role,  # type: ignore[arg-type]
            added_at=participant.added_at,
            added_by=participant.added_by,
        )

    @staticmethod
    def _task_response(task: Task) -> TaskResponse:
        return TaskResponse(
            id=task.id,
            case_id=task.case_id,
            title=task.title,
            description=task.description,
            status=task.status,  # type: ignore[arg-type]
            priority=task.priority,  # type: ignore[arg-type]
            assigned_to=task.assigned_to,
            due_at=task.due_at,
            completed_at=task.completed_at,
            created_by=task.created_by,
            version=task.version,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    @staticmethod
    def _deadline_response(deadline: Deadline) -> DeadlineResponse:
        return DeadlineResponse(
            id=deadline.id,
            case_id=deadline.case_id,
            title=deadline.title,
            deadline_at=deadline.deadline_at,
            type=deadline.type,  # type: ignore[arg-type]
            status=deadline.status,  # type: ignore[arg-type]
            reminder_sent=deadline.reminder_sent,
            created_by=deadline.created_by,
            created_at=deadline.created_at,
            updated_at=deadline.updated_at,
        )

    @staticmethod
    def _hearing_response(hearing: Hearing) -> HearingResponse:
        return HearingResponse(
            id=hearing.id,
            case_id=hearing.case_id,
            title=hearing.title,
            hearing_at=hearing.hearing_at,
            location=hearing.location,
            court=hearing.court,
            judge=hearing.judge,
            notes=hearing.notes,
            created_by=hearing.created_by,
            created_at=hearing.created_at,
            updated_at=hearing.updated_at,
        )

    @staticmethod
    def _note_response(note: Note) -> NoteResponse:
        return NoteResponse(
            id=note.id,
            case_id=note.case_id,
            author_id=note.author_id,
            body=note.body,
            visibility=note.visibility,  # type: ignore[arg-type]
            created_at=note.created_at,
            updated_at=note.updated_at,
        )

    @staticmethod
    def _timeline_response(event: CaseTimelineEvent) -> TimelineEventResponse:
        return TimelineEventResponse(
            id=event.id,
            case_id=event.case_id,
            firm_id=event.firm_id,
            event_type=event.event_type,
            title=event.title,
            payload=event.payload,
            actor_id=event.actor_id,
            occurred_at=event.occurred_at,
            created_at=event.created_at,
        )
