"""Sprint 5 — notifications table and audit read indexes."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004_sprint5_notifications"
down_revision = "003_documents_ai_workflows"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS shared")

    notification_channel = postgresql.ENUM(
        "in_app", "email", "teams", name="notification_channel", schema="shared", create_type=False
    )
    notification_status = postgresql.ENUM(
        "pending", "sent", "read", "failed", name="notification_status", schema="shared", create_type=False
    )
    notification_channel.create(op.get_bind(), checkfirst=True)
    notification_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.users.id"), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.cases.id"), nullable=True),
        sa.Column("firm_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.firms.id"), nullable=False),
        sa.Column("channel", notification_channel, nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", notification_status, nullable=False, server_default="pending"),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="shared",
    )
    op.create_index(
        "idx_notif_user",
        "notifications",
        ["user_id", "status", sa.text("created_at DESC")],
        schema="shared",
    )
    op.create_index(
        "idx_audit_firm_created",
        "audit_logs",
        ["firm_id", sa.text("created_at DESC")],
        schema="audit",
    )


def downgrade() -> None:
    op.drop_index("idx_audit_firm_created", table_name="audit_logs", schema="audit")
    op.drop_index("idx_notif_user", table_name="notifications", schema="shared")
    op.drop_table("notifications", schema="shared")
    op.execute("DROP TYPE IF EXISTS shared.notification_status")
    op.execute("DROP TYPE IF EXISTS shared.notification_channel")
