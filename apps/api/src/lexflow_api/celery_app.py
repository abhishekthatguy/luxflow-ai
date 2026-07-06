from celery import Celery

from lexflow_api.config import settings

celery_app = Celery(
    "lexflow",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "lexflow_api.tasks.platform",
        "lexflow_api.tasks.case_events",
        "lexflow_api.tasks.document_tasks",
        "lexflow_api.tasks.ai_tasks",
        "lexflow_api.tasks.workflow_tasks",
    ],
)

celery_app.conf.update(
    task_default_queue="platform.default",
    task_routes={
        "lexflow_api.tasks.platform.*": {"queue": "platform.default"},
        "lexflow_api.tasks.document_tasks.*": {"queue": "platform.default"},
        "lexflow_api.tasks.ai_tasks.*": {"queue": "platform.default"},
        "lexflow_api.tasks.workflow_tasks.*": {"queue": "platform.default"},
    },
    result_expires=3600,
)
