from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser
from lexflow_api.exceptions import ConflictError, NotFoundError
from lexflow_api.models.cases import Case, Client, ClientType
from lexflow_api.schemas.clients import ClientCreate, ClientResponse, ClientUpdate
from lexflow_api.services.audit import write_audit_log
from lexflow_api.services.outbox import write_outbox_event


class ClientService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def to_response(client: Client) -> ClientResponse:
        return ClientResponse(
            id=client.id,
            firm_id=client.firm_id,
            name=client.name,
            type=client.type,  # type: ignore[arg-type]
            email=client.email,
            phone=client.phone,
            metadata=client.metadata_,
            version=client.version,
            created_at=client.created_at,
            updated_at=client.updated_at,
        )

    async def list_clients(
        self,
        user: CurrentUser,
        *,
        page: int = 1,
        page_size: int = 25,
        search: str | None = None,
    ) -> tuple[list[ClientResponse], int]:
        query = select(Client).where(
            Client.firm_id == user.firm_id,
            Client.deleted_at.is_(None),
        )
        if search:
            query = query.where(Client.name.ilike(f"%{search}%"))

        count_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = int(count_result.scalar_one())

        offset = (page - 1) * page_size
        result = await self._session.execute(
            query.order_by(Client.created_at.desc()).offset(offset).limit(page_size)
        )
        clients = result.scalars().all()
        return [self.to_response(c) for c in clients], total

    async def get_client(self, user: CurrentUser, client_id: UUID) -> ClientResponse:
        client = await self._get_client_model(user, client_id)
        return self.to_response(client)

    async def create_client(self, user: CurrentUser, data: ClientCreate) -> ClientResponse:
        client = Client(
            firm_id=user.firm_id,
            name=data.name,
            type=data.type.value,
            email=data.email,
            phone=data.phone,
            metadata_=data.metadata,
        )
        self._session.add(client)
        await self._session.flush()
        await write_audit_log(
            self._session,
            firm_id=user.firm_id,
            actor_id=user.id,
            action="client.created",
            resource_type="client",
            resource_id=client.id,
            details={"name": client.name, "email": client.email},
        )
        await write_outbox_event(
            self._session,
            firm_id=user.firm_id,
            aggregate_type="client",
            aggregate_id=client.id,
            event_type="ClientCreated",
            payload={
                "clientId": str(client.id),
                "name": client.name,
                "email": client.email,
            },
        )
        await self._session.commit()
        from lexflow_api.tasks.workflow_tasks import trigger_client_created_workflow

        trigger_client_created_workflow.delay(
            str(client.id),
            str(user.firm_id),
            str(user.id),
        )
        return self.to_response(client)

    async def update_client(
        self, user: CurrentUser, client_id: UUID, data: ClientUpdate
    ) -> ClientResponse:
        client = await self._get_client_model(user, client_id)
        if data.version is not None and data.version != client.version:
            raise ConflictError("Client version mismatch.")

        updates = data.model_dump(exclude_unset=True)
        updates.pop("version", None)

        if "name" in updates and updates["name"] is not None:
            client.name = updates["name"]
        if "type" in updates:
            raw_type = updates["type"]
            client.type = raw_type.value if isinstance(raw_type, ClientType) else str(raw_type)
        if "email" in updates:
            client.email = updates["email"]
        if "phone" in updates:
            client.phone = updates["phone"]
        if "metadata" in updates and updates["metadata"] is not None:
            client.metadata_ = updates["metadata"]

        client.version += 1
        client.updated_at = datetime.now(UTC)
        await write_audit_log(
            self._session,
            firm_id=user.firm_id,
            actor_id=user.id,
            action="client.updated",
            resource_type="client",
            resource_id=client.id,
        )
        return self.to_response(client)

    async def list_client_cases(
        self, user: CurrentUser, client_id: UUID, *, page: int = 1, page_size: int = 25
    ) -> tuple[list[Case], int]:
        await self._get_client_model(user, client_id)
        query = select(Case).where(
            Case.client_id == client_id,
            Case.firm_id == user.firm_id,
            Case.deleted_at.is_(None),
        )
        count_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = int(count_result.scalar_one())
        offset = (page - 1) * page_size
        result = await self._session.execute(
            query.order_by(Case.created_at.desc()).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def _get_client_model(self, user: CurrentUser, client_id: UUID) -> Client:
        result = await self._session.execute(
            select(Client).where(
                Client.id == client_id,
                Client.firm_id == user.firm_id,
                Client.deleted_at.is_(None),
            )
        )
        client = result.scalar_one_or_none()
        if client is None:
            raise NotFoundError("Client not found.")
        return client

    async def soft_delete_client(self, user: CurrentUser, client_id: UUID) -> None:
        client = await self._get_client_model(user, client_id)
        client.deleted_at = datetime.now(UTC)
        await write_audit_log(
            self._session,
            firm_id=user.firm_id,
            actor_id=user.id,
            action="client.deleted",
            resource_type="client",
            resource_id=client.id,
        )
