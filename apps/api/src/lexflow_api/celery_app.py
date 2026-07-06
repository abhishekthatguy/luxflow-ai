from celery import Celery

from lexflow_api.config import settings

celery_app = Celery(
    "lexflow",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["lexflow_api.tasks.platform", "lexflow_api.tasks.case_events"],
)

celery_app.conf.update(
    task_default_queue="platform.default",
    task_routes={"lexflow_api.tasks.platform.*": {"queue": "platform.default"}},
    result_expires=3600,
)
