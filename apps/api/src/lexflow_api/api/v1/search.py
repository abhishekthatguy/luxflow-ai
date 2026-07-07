from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser, get_current_user
from lexflow_api.db.session import get_db
from lexflow_api.models.cases import Case, Client
from lexflow_api.schemas.common import CamelModel, Envelope, envelope

router = APIRouter(prefix="/search", tags=["search"])


class SearchHit(CamelModel):
    type: str
    id: str
    title: str
    subtitle: str | None = None
    href: str


class SearchResults(CamelModel):
    query: str
    hits: list[SearchHit]


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


@router.get("", response_model=Envelope[SearchResults])
async def global_search(
    request: Request,
    q: str = Query(min_length=1, max_length=200),
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[SearchResults]:
    hits: list[SearchHit] = []
    term = f"%{q}%"

    case_rows = (
        await session.execute(
            select(Case)
            .where(
                Case.firm_id == user.firm_id,
                Case.deleted_at.is_(None),
                or_(Case.title.ilike(term), Case.case_number.ilike(term)),
            )
            .order_by(Case.updated_at.desc())
            .limit(8)
        )
    ).scalars().all()
    for c in case_rows:
        hits.append(
            SearchHit(
                type="case",
                id=str(c.id),
                title=f"{c.case_number} — {c.title}",
                subtitle=c.practice_area,
                href=f"/cases/{c.id}/overview",
            )
        )

    client_rows = (
        await session.execute(
            select(Client)
            .where(
                Client.firm_id == user.firm_id,
                Client.deleted_at.is_(None),
                or_(Client.name.ilike(term), Client.email.ilike(term)),
            )
            .order_by(Client.name.asc())
            .limit(6)
        )
    ).scalars().all()
    for cl in client_rows:
        hits.append(
            SearchHit(
                type="client",
                id=str(cl.id),
                title=cl.name,
                subtitle=cl.email,
                href=f"/clients/{cl.id}",
            )
        )

    static_ops = [
        ("operations", "Operations Overview", "/operations"),
        ("operations", "System Health", "/operations/health"),
        ("operations", "AI Jobs", "/operations/jobs"),
        ("operations", "Workflow Runs", "/operations/workflows"),
        ("operations", "Audit Log", "/operations/audit"),
    ]
    q_lower = q.lower()
    for _, title, href in static_ops:
        if q_lower in title.lower() or q_lower in href:
            hits.append(
                SearchHit(type="operations", id=href, title=title, href=href)
            )

    return envelope(SearchResults(query=q, hits=hits[:20]), _request_id(request))
