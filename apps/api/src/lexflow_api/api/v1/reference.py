from fastapi import APIRouter, Request

from lexflow_api.domain.practice_areas import practice_area_options
from lexflow_api.schemas.common import CamelModel, Envelope, envelope

router = APIRouter(prefix="/reference", tags=["reference"])


class PracticeAreaOption(CamelModel):
    value: str
    label: str


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


@router.get("/practice-areas", response_model=Envelope[list[PracticeAreaOption]])
async def list_practice_areas(request: Request) -> Envelope[list[PracticeAreaOption]]:
    """Return supported practice areas for case create/edit forms."""
    options = [PracticeAreaOption(**item) for item in practice_area_options()]
    return envelope(options, _request_id(request))
