"""pgvector extension and document chunk embeddings (Phase 1)."""

from alembic import op

revision = "005_pgvector_document_chunks"
down_revision = "004_sprint5_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        CREATE TABLE documents.document_chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID NOT NULL REFERENCES documents.documents(id) ON DELETE CASCADE,
            case_id UUID NOT NULL REFERENCES cases.cases(id),
            firm_id UUID NOT NULL REFERENCES identity.firms(id),
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding vector(768),
            ocr_method TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX idx_document_chunks_document
        ON documents.document_chunks (document_id, chunk_index)
        """
    )
    op.execute(
        """
        CREATE INDEX idx_document_chunks_case
        ON documents.document_chunks (case_id)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS documents.document_chunks")
    op.execute("DROP EXTENSION IF EXISTS vector")
