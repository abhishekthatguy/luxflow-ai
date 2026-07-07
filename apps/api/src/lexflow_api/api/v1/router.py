from fastapi import APIRouter

from lexflow_api.api.v1.admin import router as admin_router
from lexflow_api.api.v1.ai import ai_router, case_ai_router
from lexflow_api.api.v1.audit import router as audit_router
from lexflow_api.api.v1.auth import router as auth_router
from lexflow_api.api.v1.cases import router as cases_router
from lexflow_api.api.v1.clients import router as clients_router
from lexflow_api.api.v1.documents import case_documents_router, documents_router
from lexflow_api.api.v1.jobs import router as jobs_router
from lexflow_api.api.v1.notifications import router as notifications_router
from lexflow_api.api.v1.operations import router as operations_router
from lexflow_api.api.v1.reference import router as reference_router
from lexflow_api.api.v1.search import router as search_router
from lexflow_api.api.v1.workflow_catalog import router as workflow_catalog_router
from lexflow_api.api.v1.workflows import router as workflows_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(admin_router)
v1_router.include_router(auth_router)
v1_router.include_router(clients_router)
v1_router.include_router(cases_router)
v1_router.include_router(case_documents_router)
v1_router.include_router(documents_router)
v1_router.include_router(case_ai_router)
v1_router.include_router(ai_router)
v1_router.include_router(jobs_router)
v1_router.include_router(workflows_router)
v1_router.include_router(workflow_catalog_router)
v1_router.include_router(audit_router)
v1_router.include_router(notifications_router)
v1_router.include_router(operations_router)
v1_router.include_router(search_router)
v1_router.include_router(reference_router)
