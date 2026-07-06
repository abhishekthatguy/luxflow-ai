"""Documents, AI, workflows, and async jobs (Sprint 4).

Revision ID: 003_documents_ai_workflows
Revises: 002_identity_cases
Create Date: 2026-07-06
"""

from alembic import op

revision = "003_documents_ai_workflows"
down_revision = "002_identity_cases"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TYPE documents.document_type AS ENUM (
            'pleading', 'contract', 'evidence', 'correspondence', 'invoice', 'other'
        );
        CREATE TYPE documents.document_status AS ENUM (
            'pending_upload', 'uploaded', 'processing', 'ready', 'failed', 'archived'
        );
        CREATE TYPE documents.ocr_status AS ENUM (
            'pending', 'processing', 'completed', 'failed', 'skipped'
        );

        CREATE TYPE ai.summary_type AS ENUM (
            'case_overview', 'document_summary', 'deposition_summary', 'contract_review'
        );
        CREATE TYPE ai.summary_status AS ENUM (
            'generating', 'draft', 'approved', 'rejected', 'failed'
        );
        CREATE TYPE ai.llm_provider AS ENUM (
            'openai', 'azure_openai', 'anthropic', 'ollama'
        );
        CREATE TYPE ai.prompt_status AS ENUM (
            'success', 'error', 'filtered'
        );

        CREATE TYPE workflows.trigger_type AS ENUM ('manual', 'event', 'schedule');
        CREATE TYPE workflows.execution_status AS ENUM (
            'queued', 'running', 'completed', 'failed', 'cancelled'
        );
        CREATE TYPE workflows.step_status AS ENUM (
            'pending', 'running', 'completed', 'failed', 'skipped'
        );

        CREATE TYPE shared.job_type AS ENUM (
            'ai.summary', 'document.process', 'workflow.execution'
        );
        CREATE TYPE shared.job_status AS ENUM (
            'queued', 'running', 'completed', 'failed', 'cancelled'
        );
    """)

    op.execute("""
        CREATE TABLE documents.documents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            case_id UUID NOT NULL REFERENCES cases.cases(id),
            firm_id UUID NOT NULL REFERENCES identity.firms(id),
            title VARCHAR(500) NOT NULL,
            document_type documents.document_type NOT NULL DEFAULT 'other',
            status documents.document_status NOT NULL DEFAULT 'pending_upload',
            current_version_id UUID,
            s3_key VARCHAR(1000) NOT NULL,
            mime_type VARCHAR(100) NOT NULL,
            file_size_bytes BIGINT NOT NULL,
            checksum_sha256 VARCHAR(64) NOT NULL,
            ocr_status documents.ocr_status NOT NULL DEFAULT 'pending',
            ocr_text TEXT,
            metadata JSONB NOT NULL DEFAULT '{}',
            uploaded_by UUID NOT NULL REFERENCES identity.users(id),
            version INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            deleted_at TIMESTAMPTZ
        );

        CREATE TABLE documents.document_versions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID NOT NULL REFERENCES documents.documents(id) ON DELETE CASCADE,
            version_number INTEGER NOT NULL,
            s3_key VARCHAR(1000) NOT NULL,
            file_size_bytes BIGINT NOT NULL,
            checksum_sha256 VARCHAR(64) NOT NULL,
            change_summary TEXT,
            created_by UUID NOT NULL REFERENCES identity.users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (document_id, version_number)
        );

        ALTER TABLE documents.documents
            ADD CONSTRAINT fk_documents_current_version
            FOREIGN KEY (current_version_id) REFERENCES documents.document_versions(id);

        CREATE INDEX idx_documents_case ON documents.documents (case_id, document_type, status)
            WHERE deleted_at IS NULL;
        CREATE INDEX idx_documents_firm ON documents.documents (firm_id, created_at DESC)
            WHERE deleted_at IS NULL;
    """)

    op.execute("""
        CREATE TABLE ai.prompt_templates (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            slug VARCHAR(100) NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            template TEXT NOT NULL,
            model_config JSONB NOT NULL DEFAULT '{}',
            requires_approval BOOLEAN NOT NULL DEFAULT true,
            is_active BOOLEAN NOT NULL DEFAULT true,
            description TEXT,
            created_by UUID REFERENCES identity.users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (slug, version)
        );

        CREATE INDEX idx_prompt_templates_active_slug ON ai.prompt_templates (slug)
            WHERE is_active = true;

        CREATE TABLE ai.ai_summaries (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            case_id UUID NOT NULL REFERENCES cases.cases(id),
            document_id UUID REFERENCES documents.documents(id),
            firm_id UUID NOT NULL REFERENCES identity.firms(id),
            summary_type ai.summary_type NOT NULL,
            content TEXT,
            model VARCHAR(100) NOT NULL,
            prompt_version VARCHAR(50) NOT NULL,
            status ai.summary_status NOT NULL DEFAULT 'generating',
            approved_by UUID REFERENCES identity.users(id),
            approved_at TIMESTAMPTZ,
            rejection_reason TEXT,
            token_count INTEGER,
            requested_by UUID NOT NULL REFERENCES identity.users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX idx_ai_summaries_case ON ai.ai_summaries (case_id, summary_type, created_at DESC);
        CREATE INDEX idx_ai_summaries_pending ON ai.ai_summaries (status)
            WHERE status IN ('generating', 'draft');

        CREATE TABLE ai.prompt_history (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            case_id UUID REFERENCES cases.cases(id),
            firm_id UUID NOT NULL REFERENCES identity.firms(id),
            user_id UUID NOT NULL REFERENCES identity.users(id),
            prompt_template_id UUID REFERENCES ai.prompt_templates(id),
            rendered_prompt TEXT NOT NULL,
            response TEXT,
            model VARCHAR(100) NOT NULL,
            provider ai.llm_provider NOT NULL DEFAULT 'azure_openai',
            input_tokens INTEGER NOT NULL DEFAULT 0,
            output_tokens INTEGER NOT NULL DEFAULT 0,
            latency_ms INTEGER,
            status ai.prompt_status NOT NULL DEFAULT 'success',
            error_message TEXT,
            correlation_id UUID NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX idx_prompt_history_case ON ai.prompt_history (case_id, created_at DESC);
        CREATE INDEX idx_prompt_history_correlation ON ai.prompt_history (correlation_id);

        CREATE TABLE ai.llm_usage (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            firm_id UUID NOT NULL REFERENCES identity.firms(id),
            user_id UUID REFERENCES identity.users(id),
            case_id UUID REFERENCES cases.cases(id),
            provider VARCHAR(50) NOT NULL,
            model VARCHAR(100) NOT NULL,
            input_tokens BIGINT NOT NULL DEFAULT 0,
            output_tokens BIGINT NOT NULL DEFAULT 0,
            estimated_cost_usd DECIMAL(10, 6) NOT NULL DEFAULT 0,
            period_start DATE NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (firm_id, user_id, case_id, provider, model, period_start)
        );

        CREATE INDEX idx_llm_usage_firm ON ai.llm_usage (firm_id, period_start DESC);
    """)

    op.execute("""
        CREATE TABLE workflows.workflow_definitions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            firm_id UUID REFERENCES identity.firms(id),
            name VARCHAR(255) NOT NULL,
            slug VARCHAR(100) NOT NULL,
            description TEXT,
            n8n_workflow_id VARCHAR(100) NOT NULL,
            trigger_type workflows.trigger_type NOT NULL DEFAULT 'event',
            is_active BOOLEAN NOT NULL DEFAULT true,
            config_schema JSONB,
            version INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE UNIQUE INDEX uq_workflow_def_firm_slug
            ON workflows.workflow_definitions (firm_id, slug)
            WHERE firm_id IS NOT NULL;
        CREATE UNIQUE INDEX uq_workflow_def_system_slug
            ON workflows.workflow_definitions (slug)
            WHERE firm_id IS NULL;

        CREATE TABLE workflows.workflow_executions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            workflow_definition_id UUID NOT NULL REFERENCES workflows.workflow_definitions(id),
            case_id UUID REFERENCES cases.cases(id),
            firm_id UUID NOT NULL REFERENCES identity.firms(id),
            triggered_by UUID REFERENCES identity.users(id),
            status workflows.execution_status NOT NULL DEFAULT 'queued',
            input_payload JSONB NOT NULL DEFAULT '{}',
            output_payload JSONB,
            correlation_id UUID NOT NULL,
            idempotency_key VARCHAR(255),
            n8n_execution_id VARCHAR(100),
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            error_message TEXT,
            retry_count INTEGER NOT NULL DEFAULT 0,
            max_retries INTEGER NOT NULL DEFAULT 3,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE UNIQUE INDEX uq_workflow_exec_idempotency
            ON workflows.workflow_executions (idempotency_key)
            WHERE idempotency_key IS NOT NULL;
        CREATE INDEX idx_workflow_exec_case ON workflows.workflow_executions (case_id, created_at DESC)
            WHERE case_id IS NOT NULL;
        CREATE INDEX idx_workflow_exec_poll ON workflows.workflow_executions (status, created_at)
            WHERE status IN ('queued', 'running');

        CREATE TABLE workflows.workflow_steps (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            execution_id UUID NOT NULL REFERENCES workflows.workflow_executions(id) ON DELETE CASCADE,
            step_name VARCHAR(255) NOT NULL,
            step_order INTEGER NOT NULL,
            status workflows.step_status NOT NULL DEFAULT 'pending',
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            metadata JSONB NOT NULL DEFAULT '{}',
            error_message TEXT
        );

        CREATE INDEX idx_workflow_steps_exec ON workflows.workflow_steps (execution_id, step_order);
    """)

    op.execute("""
        CREATE TABLE shared.async_jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            firm_id UUID NOT NULL REFERENCES identity.firms(id),
            case_id UUID REFERENCES cases.cases(id),
            user_id UUID NOT NULL REFERENCES identity.users(id),
            job_type shared.job_type NOT NULL,
            status shared.job_status NOT NULL DEFAULT 'queued',
            progress INTEGER NOT NULL DEFAULT 0,
            resource_type VARCHAR(100),
            resource_id UUID,
            result JSONB,
            error JSONB,
            correlation_id UUID NOT NULL DEFAULT gen_random_uuid(),
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX idx_async_jobs_user ON shared.async_jobs (user_id, created_at DESC);
        CREATE INDEX idx_async_jobs_case ON shared.async_jobs (case_id, created_at DESC)
            WHERE case_id IS NOT NULL;
        CREATE INDEX idx_async_jobs_poll ON shared.async_jobs (status, created_at)
            WHERE status IN ('queued', 'running');
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS shared.async_jobs;
        DROP TABLE IF EXISTS workflows.workflow_steps;
        DROP TABLE IF EXISTS workflows.workflow_executions;
        DROP TABLE IF EXISTS workflows.workflow_definitions;
        DROP TABLE IF EXISTS ai.llm_usage;
        DROP TABLE IF EXISTS ai.prompt_history;
        DROP TABLE IF EXISTS ai.ai_summaries;
        DROP TABLE IF EXISTS ai.prompt_templates;
        ALTER TABLE IF EXISTS documents.documents DROP CONSTRAINT IF EXISTS fk_documents_current_version;
        DROP TABLE IF EXISTS documents.document_versions;
        DROP TABLE IF EXISTS documents.documents;

        DROP TYPE IF EXISTS shared.job_status;
        DROP TYPE IF EXISTS shared.job_type;
        DROP TYPE IF EXISTS workflows.step_status;
        DROP TYPE IF EXISTS workflows.execution_status;
        DROP TYPE IF EXISTS workflows.trigger_type;
        DROP TYPE IF EXISTS ai.prompt_status;
        DROP TYPE IF EXISTS ai.llm_provider;
        DROP TYPE IF EXISTS ai.summary_status;
        DROP TYPE IF EXISTS ai.summary_type;
        DROP TYPE IF EXISTS documents.ocr_status;
        DROP TYPE IF EXISTS documents.document_status;
        DROP TYPE IF EXISTS documents.document_type;
    """)
