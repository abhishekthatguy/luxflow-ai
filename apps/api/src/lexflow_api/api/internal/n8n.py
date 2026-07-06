from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.db.session import get_db
from lexflow_api.schemas.common import Envelope, envelope
from lexflow_api.schemas.workflows import N8nCallbackPayload
from lexflow_api.services.workflow_service import WorkflowService

router = APIRouter(prefix="/internal/webhooks/n8n", tags=["internal-n8n"])


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


@router.post("/{slug}", response_model=Envelope[dict[str, str]])
async def n8n_callback(
    request: Request,
    slug: str,
    session: AsyncSession = Depends(get_db),
    x_lexflow_signature: str | None = Header(default=None, alias="X-LexFlow-Signature"),
) -> Envelope[dict[str, str]]:
    raw = await request.body()
    if not WorkflowService.verify_hmac(raw, x_lexflow_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature.")
    payload = N8nCallbackPayload.model_validate_json(raw)
    await WorkflowService(session).handle_n8n_callback(slug, payload)
    return envelope({"status": "ok", "slug": slug}, _request_id(request))
