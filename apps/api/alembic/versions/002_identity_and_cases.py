"""Identity, cases, audit, and outbox tables (Sprint 2–3).

Revision ID: 002_identity_cases
Revises: 001_baseline
Create Date: 2026-07-06
"""

from alembic import op

revision = "002_identity_cases"
down_revision = "001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TYPE identity.user_status AS ENUM ('active', 'inactive', 'locked');
        CREATE TYPE cases.client_type AS ENUM ('individual', 'organization');
        CREATE TYPE cases.case_status AS ENUM ('intake', 'active', 'on_hold', 'closed', 'archived');
        CREATE TYPE cases.priority AS ENUM ('low', 'normal', 'high', 'urgent');
        CREATE TYPE cases.participant_role AS ENUM ('lead', 'associate', 'paralegal', 'observer');
        CREATE TYPE cases.task_status AS ENUM ('pending', 'in_progress', 'completed', 'cancelled');
        CREATE TYPE cases.deadline_type AS ENUM (
            'filing', 'discovery', 'statute_of_limitations', 'internal', 'other'
        );
        CREATE TYPE cases.deadline_status AS ENUM ('upcoming', 'met', 'missed', 'extended');
        CREATE TYPE cases.note_visibility AS ENUM ('team', 'attorneys_only', 'private');
    """)

    op.execute("""
        CREATE TABLE identity.firms (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            slug VARCHAR(100) NOT NULL UNIQUE,
            settings JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE identity.roles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            firm_id UUID REFERENCES identity.firms(id),
            name VARCHAR(100) NOT NULL,
            description TEXT,
            is_system BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE identity.users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            firm_id UUID NOT NULL REFERENCES identity.firms(id),
            email VARCHAR(320) NOT NULL UNIQUE,
            password_hash VARCHAR(255),
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            title VARCHAR(100),
            status identity.user_status NOT NULL DEFAULT 'active',
            last_login_at TIMESTAMPTZ,
            version INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            deleted_at TIMESTAMPTZ
        );

        CREATE TABLE identity.user_roles (
            user_id UUID NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
            role_id UUID NOT NULL REFERENCES identity.roles(id) ON DELETE CASCADE,
            PRIMARY KEY (user_id, role_id)
        );

        CREATE TABLE identity.refresh_tokens (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
            token_hash VARCHAR(255) NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            revoked_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE cases.clients (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            firm_id UUID NOT NULL REFERENCES identity.firms(id),
            type cases.client_type NOT NULL DEFAULT 'individual',
            name VARCHAR(255) NOT NULL,
            email VARCHAR(320),
            phone VARCHAR(50),
            metadata JSONB NOT NULL DEFAULT '{}',
            version INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            deleted_at TIMESTAMPTZ
        );

        CREATE TABLE cases.cases (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            firm_id UUID NOT NULL REFERENCES identity.firms(id),
            client_id UUID NOT NULL REFERENCES cases.clients(id),
            case_number VARCHAR(50) NOT NULL,
            title VARCHAR(500) NOT NULL,
            practice_area VARCHAR(100),
            status cases.case_status NOT NULL DEFAULT 'intake',
            priority cases.priority NOT NULL DEFAULT 'normal',
            lead_attorney_id UUID NOT NULL REFERENCES identity.users(id),
            description TEXT,
            opened_at TIMESTAMPTZ,
            closed_at TIMESTAMPTZ,
            metadata JSONB NOT NULL DEFAULT '{}',
            version INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            deleted_at TIMESTAMPTZ,
            UNIQUE (firm_id, case_number)
        );

        CREATE TABLE cases.case_participants (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            case_id UUID NOT NULL REFERENCES cases.cases(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES identity.users(id),
            role cases.participant_role NOT NULL,
            added_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            added_by UUID NOT NULL REFERENCES identity.users(id),
            UNIQUE (case_id, user_id)
        );

        CREATE TABLE cases.tasks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            case_id UUID NOT NULL REFERENCES cases.cases(id) ON DELETE CASCADE,
            title VARCHAR(500) NOT NULL,
            description TEXT,
            status cases.task_status NOT NULL DEFAULT 'pending',
            priority cases.priority NOT NULL DEFAULT 'normal',
            assigned_to UUID REFERENCES identity.users(id),
            due_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            created_by UUID NOT NULL REFERENCES identity.users(id),
            version INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE cases.deadlines (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            case_id UUID NOT NULL REFERENCES cases.cases(id) ON DELETE CASCADE,
            title VARCHAR(500) NOT NULL,
            deadline_at TIMESTAMPTZ NOT NULL,
            type cases.deadline_type NOT NULL,
            status cases.deadline_status NOT NULL DEFAULT 'upcoming',
            reminder_sent BOOLEAN NOT NULL DEFAULT false,
            created_by UUID NOT NULL REFERENCES identity.users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE cases.hearings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            case_id UUID NOT NULL REFERENCES cases.cases(id) ON DELETE CASCADE,
            title VARCHAR(500) NOT NULL,
            hearing_at TIMESTAMPTZ NOT NULL,
            location VARCHAR(500),
            court VARCHAR(255),
            judge VARCHAR(255),
            notes TEXT,
            created_by UUID NOT NULL REFERENCES identity.users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE cases.notes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            case_id UUID NOT NULL REFERENCES cases.cases(id) ON DELETE CASCADE,
            author_id UUID NOT NULL REFERENCES identity.users(id),
            body TEXT NOT NULL,
            visibility cases.note_visibility NOT NULL DEFAULT 'team',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE cases.case_timeline_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            case_id UUID NOT NULL REFERENCES cases.cases(id) ON DELETE CASCADE,
            firm_id UUID NOT NULL REFERENCES identity.firms(id),
            event_type VARCHAR(100) NOT NULL,
            title VARCHAR(500) NOT NULL,
            payload JSONB NOT NULL DEFAULT '{}',
            actor_id UUID REFERENCES identity.users(id),
            occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE audit.audit_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            firm_id UUID NOT NULL REFERENCES identity.firms(id),
            actor_id UUID REFERENCES identity.users(id),
            action VARCHAR(100) NOT NULL,
            resource_type VARCHAR(100) NOT NULL,
            resource_id UUID,
            details JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE shared.outbox_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            firm_id UUID NOT NULL REFERENCES identity.firms(id),
            aggregate_type VARCHAR(100) NOT NULL,
            aggregate_id UUID NOT NULL,
            event_type VARCHAR(100) NOT NULL,
            payload JSONB NOT NULL DEFAULT '{}',
            published_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX idx_clients_firm ON cases.clients (firm_id) WHERE deleted_at IS NULL;
        CREATE INDEX idx_cases_firm_status ON cases.cases (firm_id, status) WHERE deleted_at IS NULL;
        CREATE INDEX idx_participants_user ON cases.case_participants (user_id, case_id);
        CREATE INDEX idx_timeline_case ON cases.case_timeline_events (case_id, occurred_at DESC);
        CREATE INDEX idx_outbox_unpublished ON shared.outbox_events (created_at) WHERE published_at IS NULL;
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS shared.outbox_events;
        DROP TABLE IF EXISTS audit.audit_logs;
        DROP TABLE IF EXISTS cases.case_timeline_events;
        DROP TABLE IF EXISTS cases.notes;
        DROP TABLE IF EXISTS cases.hearings;
        DROP TABLE IF EXISTS cases.deadlines;
        DROP TABLE IF EXISTS cases.tasks;
        DROP TABLE IF EXISTS cases.case_participants;
        DROP TABLE IF EXISTS cases.cases;
        DROP TABLE IF EXISTS cases.clients;
        DROP TABLE IF EXISTS identity.refresh_tokens;
        DROP TABLE IF EXISTS identity.user_roles;
        DROP TABLE IF EXISTS identity.users;
        DROP TABLE IF EXISTS identity.roles;
        DROP TABLE IF EXISTS identity.firms;
        DROP TYPE IF EXISTS cases.note_visibility;
        DROP TYPE IF EXISTS cases.deadline_status;
        DROP TYPE IF EXISTS cases.deadline_type;
        DROP TYPE IF EXISTS cases.task_status;
        DROP TYPE IF EXISTS cases.participant_role;
        DROP TYPE IF EXISTS cases.priority;
        DROP TYPE IF EXISTS cases.case_status;
        DROP TYPE IF EXISTS cases.client_type;
        DROP TYPE IF EXISTS identity.user_status;
    """)
