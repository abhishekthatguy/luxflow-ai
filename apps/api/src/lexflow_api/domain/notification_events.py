"""Notification event types — enterprise workflow notification taxonomy."""

from enum import StrEnum


class NotificationEventType(StrEnum):
    CASE_CREATED = "case.created"
    CASE_ASSIGNED = "case.assigned"
    DOCUMENT_UPLOADED = "document.uploaded"
    OCR_COMPLETED = "ocr.completed"
    AI_SUMMARY_READY = "ai.summary.ready"
    AI_SUMMARY_APPROVED = "ai.summary.approved"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    APPROVAL_REQUIRED = "approval.required"
    DAILY_SUMMARY = "daily.summary"
    SYSTEM_ALERT = "system.alert"


# Maps event type → Jinja2 email template (without .html)
EMAIL_TEMPLATE_MAP: dict[NotificationEventType, str] = {
    NotificationEventType.CASE_CREATED: "case-created",
    NotificationEventType.CASE_ASSIGNED: "case-created",
    NotificationEventType.DOCUMENT_UPLOADED: "document-uploaded",
    NotificationEventType.OCR_COMPLETED: "ocr-completed",
    NotificationEventType.AI_SUMMARY_READY: "ai-summary-ready",
    NotificationEventType.AI_SUMMARY_APPROVED: "ai-summary-approved",
    NotificationEventType.WORKFLOW_STARTED: "workflow-started",
    NotificationEventType.WORKFLOW_COMPLETED: "workflow-completed",
    NotificationEventType.WORKFLOW_FAILED: "workflow-failed",
    NotificationEventType.APPROVAL_REQUIRED: "approval-required",
    NotificationEventType.DAILY_SUMMARY: "daily-report",
    NotificationEventType.SYSTEM_ALERT: "system-health",
}
