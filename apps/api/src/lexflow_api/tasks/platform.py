import logging

from lexflow_api.celery_app import celery_app

logger = logging.getLogger("lexflow.worker")


@celery_app.task(name="lexflow_api.tasks.platform.ping")  # type: ignore[untyped-decorator]
def ping_task(correlation_id: str | None = None) -> str:
    logger.info(
        "celery_ping",
        extra={
            "correlationId": correlation_id or "none",
            "service": "worker",
            "event": "celery_ping",
        },
    )
    return "pong"
