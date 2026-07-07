from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser
from lexflow_api.auth.permissions import PERM_VIEW_AUDIT, has_permission
from lexflow_api.exceptions import ForbiddenError
from lexflow_api.models.audit import AuditLog
from lexflow_api.schemas.audit import AuditLogResponse


class AuditQueryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _require_audit_access(self, user: CurrentUser) -> None:
        if not has_permission(user.roles, PERM_VIEW_AUDIT):
            raise ForbiddenError("Your role is not permitted to view audit logs.")

    async def list_logs(
        self,
        user: CurrentUser,
        *,
        page: int = 1,
        page_size: int = 25,
        action: str | None = None,
        resource_type: str | None = None,
        case_id: UUID | None = None,
    ) -> tuple[list[AuditLogResponse], int]:
        self._require_audit_access(user)
        filters = [AuditLog.firm_id == user.firm_id]
        if action:
            filters.append(AuditLog.action == action)
        if resource_type:
            filters.append(AuditLog.resource_type == resource_type)
        if case_id:
            filters.append(AuditLog.details["caseId"].astext == str(case_id))

        count_stmt = select(func.count()).select_from(AuditLog).where(*filters)
        total = int((await self._session.scalar(count_stmt)) or 0)

        stmt = (
            select(AuditLog)
            .where(*filters)
            .order_by(AuditLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self._session.scalars(stmt)).all()
        return [AuditLogResponse.model_validate(row) for row in rows], total
