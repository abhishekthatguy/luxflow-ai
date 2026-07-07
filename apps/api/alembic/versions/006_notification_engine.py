"""Notification engine — extended delivery tracking."""

from alembic import op

revision = "006_notification_engine"
down_revision = "005_pgvector_document_chunks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE shared.notifications
            ADD COLUMN IF NOT EXISTS event_type VARCHAR(100),
            ADD COLUMN IF NOT EXISTS correlation_id UUID,
            ADD COLUMN IF NOT EXISTS workflow_execution_id UUID,
            ADD COLUMN IF NOT EXISTS workflow_slug VARCHAR(100),
            ADD COLUMN IF NOT EXISTS priority VARCHAR(50),
            ADD COLUMN IF NOT EXISTS attempts INTEGER NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS provider VARCHAR(50),
            ADD COLUMN IF NOT EXISTS delivered_at TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS action_url VARCHAR(500),
            ADD COLUMN IF NOT EXISTS description TEXT;

        CREATE INDEX IF NOT EXISTS idx_notif_correlation
            ON shared.notifications (correlation_id)
            WHERE correlation_id IS NOT NULL;

        CREATE TABLE IF NOT EXISTS shared.notification_deliveries (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            notification_id UUID REFERENCES shared.notifications(id) ON DELETE CASCADE,
            firm_id UUID NOT NULL REFERENCES identity.firms(id),
            channel VARCHAR(50) NOT NULL,
            provider VARCHAR(50),
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            attempts INTEGER NOT NULL DEFAULT 0,
            max_attempts INTEGER NOT NULL DEFAULT 4,
            correlation_id UUID,
            workflow_execution_id UUID,
            workflow_slug VARCHAR(100),
            latency_ms INTEGER,
            error_message TEXT,
            payload JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_delivery_correlation
            ON shared.notification_deliveries (correlation_id);
        CREATE INDEX IF NOT EXISTS idx_delivery_status
            ON shared.notification_deliveries (status, created_at DESC);
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS shared.notification_deliveries;
        ALTER TABLE shared.notifications
            DROP COLUMN IF EXISTS event_type,
            DROP COLUMN IF EXISTS correlation_id,
            DROP COLUMN IF EXISTS workflow_execution_id,
            DROP COLUMN IF EXISTS workflow_slug,
            DROP COLUMN IF EXISTS priority,
            DROP COLUMN IF EXISTS attempts,
            DROP COLUMN IF EXISTS provider,
            DROP COLUMN IF EXISTS delivered_at,
            DROP COLUMN IF EXISTS action_url,
            DROP COLUMN IF EXISTS description;
    """)
