from typing import Any

from fastapi import APIRouter

from lexflow_api.tasks.platform import ping_task

router = APIRouter(prefix="/internal/platform", tags=["internal-platform"])


@router.post("/smoke")
async def platform_smoke(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "api",
        "received": True,
        "correlationId": payload.get("correlationId"),
    }


@router.post("/celery-ping")
async def platform_celery_ping(payload: dict[str, Any] | None = None) -> dict[str, str]:
    body = payload or {}
    correlation_id = body.get("correlationId")
    async_result = ping_task.delay(correlation_id)
    return {"taskId": async_result.id}
