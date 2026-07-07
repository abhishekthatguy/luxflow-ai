"""Password reset token storage."""

from alembic import op

revision = "007_password_reset_tokens"
down_revision = "006_notification_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE identity.password_reset_purpose AS ENUM ('invite', 'reset');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;

        CREATE TABLE IF NOT EXISTS identity.password_reset_tokens (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
            token_hash VARCHAR(64) NOT NULL,
            purpose identity.password_reset_purpose NOT NULL DEFAULT 'reset',
            expires_at TIMESTAMPTZ NOT NULL,
            used_at TIMESTAMPTZ,
            request_ip VARCHAR(45),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_password_reset_token_active
            ON identity.password_reset_tokens (token_hash)
            WHERE used_at IS NULL;

        CREATE INDEX IF NOT EXISTS idx_password_reset_user_created
            ON identity.password_reset_tokens (user_id, created_at DESC);
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS identity.password_reset_tokens;
        DROP TYPE IF EXISTS identity.password_reset_purpose;
    """)
