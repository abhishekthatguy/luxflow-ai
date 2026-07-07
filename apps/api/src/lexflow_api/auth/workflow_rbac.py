"""Workflow catalog RBAC — who may trigger each workflow and what it automates."""

from __future__ import annotations

from dataclasses import dataclass

from lexflow_api.auth.rbac import (
    FIRM_WIDE_ACCESS_ROLES,
    ROLE_ATTORNEY,
    ROLE_ASSOCIATE,
    ROLE_LEGAL_ASSISTANT,
    ROLE_MANAGING_PARTNER,
    ROLE_PARALEGAL,
    ROLE_PARTNER,
    ROLE_SYSTEM_ADMINISTRATOR,
    has_any_role,
)

_ALL_STAFF = frozenset(
    {
        ROLE_ATTORNEY,
        ROLE_ASSOCIATE,
        ROLE_PARALEGAL,
        ROLE_LEGAL_ASSISTANT,
        ROLE_MANAGING_PARTNER,
        ROLE_PARTNER,
        ROLE_SYSTEM_ADMINISTRATOR,
    }
)
_ATTORNEY_TIER = frozenset({ROLE_ATTORNEY, ROLE_ASSOCIATE, ROLE_PARTNER, ROLE_MANAGING_PARTNER})
_PARTNER_ADMIN = frozenset({ROLE_MANAGING_PARTNER, ROLE_SYSTEM_ADMINISTRATOR})


@dataclass(frozen=True)
class WorkflowAccess:
    serial: int
    allowed_roles: frozenset[str]
    scope: str  # case | firm
    manual_trigger: bool
    automated_by: str
    automation_steps: tuple[str, ...]
    test_trigger_roles: frozenset[str] = frozenset()


WORKFLOW_ACCESS: dict[str, WorkflowAccess] = {
    "case-intake-v1": WorkflowAccess(
        serial=1,
        allowed_roles=_ATTORNEY_TIER | {ROLE_SYSTEM_ADMINISTRATOR},
        scope="case",
        manual_trigger=True,
        automated_by="Auto on case creation (outbox → n8n webhook)",
        automation_steps=(
            "Validate request",
            "Load case details",
            "Assign lead attorney",
            "Create intake tasks",
            "Notify Teams",
            "Write audit log",
        ),
    ),
    "document-upload-v1": WorkflowAccess(
        serial=2,
        allowed_roles=_ALL_STAFF,
        scope="case",
        manual_trigger=True,
        automated_by="Auto after document OCR completes (Celery → n8n)",
        automation_steps=(
            "Validate signature",
            "Initialize workflow",
            "Heartbeat API",
            "Get case details",
            "Poll OCR status",
            "Decision: OCR complete?",
            "Trigger AI summary",
            "Decision: AI success?",
            "Execute notifications sub-workflow",
            "Execute audit sub-workflow",
            "Signed callback to FastAPI",
        ),
    ),
    "ai-summary-approved-v1": WorkflowAccess(
        serial=3,
        allowed_roles=_ATTORNEY_TIER | {ROLE_MANAGING_PARTNER},
        scope="case",
        manual_trigger=True,
        automated_by="Auto when attorney approves AI draft (outbox event)",
        automation_steps=(
            "Update case status",
            "Notify managing partner",
            "Archive approved summary",
            "Write audit log",
        ),
    ),
    "client-created-v1": WorkflowAccess(
        serial=4,
        allowed_roles=frozenset({ROLE_ATTORNEY, ROLE_PARALEGAL, ROLE_MANAGING_PARTNER}),
        scope="firm",
        manual_trigger=True,
        automated_by="Auto when a new client is created (clients API outbox)",
        automation_steps=(
            "CRM sync",
            "Send welcome email",
            "Assign intake team",
            "Write audit log",
        ),
    ),
    "case-closed-v1": WorkflowAccess(
        serial=5,
        allowed_roles=_ATTORNEY_TIER | {ROLE_MANAGING_PARTNER},
        scope="case",
        manual_trigger=True,
        automated_by="Auto when case status changes to closed",
        automation_steps=(
            "Archive documents",
            "Export case PDF",
            "Email client",
            "Move files to cold storage",
            "Write audit log",
        ),
    ),
    "ai-failure-recovery-v1": WorkflowAccess(
        serial=6,
        allowed_roles=_ATTORNEY_TIER | {ROLE_SYSTEM_ADMINISTRATOR},
        scope="case",
        manual_trigger=True,
        automated_by="Auto when an AI summary job fails",
        automation_steps=(
            "Retry AI job (×3)",
            "Create human review task",
            "Notify attorney + admin",
        ),
    ),
    "approval-escalation-v1": WorkflowAccess(
        serial=7,
        allowed_roles=_PARTNER_ADMIN,
        scope="firm",
        manual_trigger=False,
        test_trigger_roles=_PARTNER_ADMIN,
        automated_by="Scheduled — every hour (n8n cron)",
        automation_steps=(
            "Find pending approvals",
            "Filter older than 24h",
            "Send attorney reminder",
            "Escalate to managing partner",
        ),
    ),
    "daily-partner-report-v1": WorkflowAccess(
        serial=8,
        allowed_roles=frozenset({ROLE_MANAGING_PARTNER}),
        scope="firm",
        manual_trigger=False,
        test_trigger_roles=frozenset({ROLE_MANAGING_PARTNER, ROLE_SYSTEM_ADMINISTRATOR}),
        automated_by="Scheduled — daily 08:00 UTC (n8n cron)",
        automation_steps=(
            "Aggregate pending cases",
            "List failed AI jobs",
            "List workflow errors",
            "Email partner digest",
            "Post Teams notification",
        ),
    ),
    "ops-health-monitor-v1": WorkflowAccess(
        serial=9,
        allowed_roles=frozenset({ROLE_SYSTEM_ADMINISTRATOR, ROLE_MANAGING_PARTNER}),
        scope="firm",
        manual_trigger=False,
        test_trigger_roles=frozenset({ROLE_SYSTEM_ADMINISTRATOR, ROLE_MANAGING_PARTNER}),
        automated_by="Scheduled — every 5 minutes (n8n cron)",
        automation_steps=(
            "Probe Redis",
            "Probe RabbitMQ",
            "Probe Celery workers",
            "Probe API health",
            "Create incident record",
            "Alert ops admins",
        ),
    ),
    "smoke-callback-v1": WorkflowAccess(
        serial=10,
        allowed_roles=frozenset({ROLE_SYSTEM_ADMINISTRATOR}),
        scope="firm",
        manual_trigger=True,
        automated_by="Manual only — CI / platform smoke tests",
        automation_steps=("Verify n8n → FastAPI callback path",),
    ),
}


def can_trigger_workflow(*, user_roles: set[str], slug: str) -> bool:
    access = WORKFLOW_ACCESS.get(slug)
    if access is None:
        return False
    if access.manual_trigger and has_any_role(user_roles, access.allowed_roles):
        return True
    if access.test_trigger_roles and has_any_role(user_roles, access.test_trigger_roles):
        return True
    return False


def is_test_trigger(*, user_roles: set[str], slug: str) -> bool:
    """True when user may only test-run a normally scheduled workflow."""
    access = WORKFLOW_ACCESS.get(slug)
    if access is None or access.manual_trigger:
        return False
    return has_any_role(user_roles, access.test_trigger_roles)


def can_delete_workflow_execution(*, user_roles: set[str]) -> bool:
    return has_any_role(user_roles, FIRM_WIDE_ACCESS_ROLES)


def enrich_catalog_item(
    *,
    slug: str,
    meta: dict[str, object],
    user_roles: set[str],
) -> dict[str, object]:
    access = WORKFLOW_ACCESS.get(slug)
    if access is None:
        return {
            "serial": int(meta.get("serial", 0) or 0),
            "summary": str(meta.get("summary", "")),
            "scope": "case",
            "allowed_roles": [],
            "automation_steps": [],
            "automated_by": str(meta.get("fastapi_trigger", "")),
            "can_trigger": False,
            "is_test_trigger": False,
        }
    triggerable = can_trigger_workflow(user_roles=user_roles, slug=slug)
    return {
        "serial": access.serial,
        "summary": str(meta.get("summary", "")),
        "scope": access.scope,
        "allowed_roles": sorted(access.allowed_roles | access.test_trigger_roles),
        "automation_steps": list(access.automation_steps),
        "automated_by": access.automated_by,
        "can_trigger": triggerable,
        "is_test_trigger": triggerable and is_test_trigger(user_roles=user_roles, slug=slug),
    }
