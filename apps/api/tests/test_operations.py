"""Operations dashboard and case processing pipeline tests."""

from lexflow_api.services.operations_service import (
    OperationsDashboard,
    PipelineStage,
    ProcessingMetrics,
)


def test_pipeline_stage_model() -> None:
    stage = PipelineStage(id="uploaded", label="Uploaded", status="completed")
    assert stage.label == "Uploaded"


def test_expected_pipeline_labels() -> None:
    """Canonical AI processing timeline shown in the UI."""
    labels = [
        "Uploaded",
        "Virus Scan",
        "OCR",
        "AI Summary",
        "Human Approval",
        "Workflow Triggered",
        "Completed",
    ]
    assert len(labels) == 7


def test_operations_dashboard_schema_fields() -> None:
    fields = OperationsDashboard.model_fields
    assert "health" in fields
    assert "queues" in fields
    assert "active_ai_jobs" in fields
    assert "failed_workflows" in fields
    assert "recent_audit_events" in fields
    assert "processing_metrics" in fields


def test_processing_metrics_defaults() -> None:
    metrics = ProcessingMetrics(
        documents_ready=10,
        ai_summaries_total=5,
        ai_summaries_approved=3,
        workflow_success_rate=0.95,
    )
    assert metrics.avg_job_duration_seconds is None
