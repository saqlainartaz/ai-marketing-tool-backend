"""Initial schema: tenancy, documents, atoms, jobs, lineage, decisions + RLS.

Revision ID: 0001
Revises:
Create Date: 2026-07-29

Tenant isolation is DB-enforced: every tenant-scoped table has RLS ENABLED and
FORCED, with policies keyed on current_setting('app.client_id', true). When the
GUC is unset, current_setting returns NULL and policies match nothing — fail-closed.

The app connects as the non-superuser role `engine_app` (superusers bypass RLS
entirely, so serving requests as the admin role would silently disable isolation).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMBEDDING_DIM = 1024  # Voyage voyage-3; fake embedder matches (docs/DECISIONS.md)

TENANT_TABLES = ("documents", "atoms", "jobs", "lineage", "decisions")


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Non-superuser app role. Dev password only — production rotates it with
    # ALTER ROLE outside migrations (docs/DECISIONS.md).
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'engine_app') THEN
                CREATE ROLE engine_app LOGIN PASSWORD 'engine_app_dev'
                    NOSUPERUSER NOBYPASSRLS;
            END IF;
        END
        $$;
        """
    )

    op.create_table(
        "clients",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )

    op.create_table(
        "documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_authority", sa.String(), nullable=False,
                  server_default="CONVERSATIONAL"),
        sa.Column("sha256", sa.String(), nullable=False),
        sa.Column("raw_path", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="uploaded"),
        sa.Column("doc_metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("pipeline_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.UniqueConstraint("client_id", "sha256", name="uq_documents_client_sha"),
    )
    op.create_index("ix_documents_client_id", "documents", ["client_id"])

    op.create_table(
        "atoms",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("document_id", UUID(as_uuid=True),
                  sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("atom_type", sa.String(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("provenance", JSONB(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("impact", sa.Integer(), nullable=True),
        sa.Column("evidence_kind", sa.String(), nullable=False, server_default="inferred"),
        sa.Column("status", sa.String(), nullable=False, server_default="provisional"),
        sa.Column("stale_after", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("content_hash", sa.String(), nullable=False),
        sa.Column("pipeline_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column("tsv", TSVECTOR(),
                  sa.Computed("to_tsvector('english', text)", persisted=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.UniqueConstraint("document_id", "content_hash", name="uq_atoms_doc_content"),
    )
    op.create_index("ix_atoms_client_id", "atoms", ["client_id"])
    op.create_index("ix_atoms_client_type", "atoms", ["client_id", "atom_type"])
    op.create_index("ix_atoms_tsv", "atoms", ["tsv"], postgresql_using="gin")

    op.create_table(
        "jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("document_id", UUID(as_uuid=True),
                  sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="queued"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_jobs_status", "jobs", ["status"])

    op.create_table(
        "lineage",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("document_id", UUID(as_uuid=True),
                  sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_sha", sa.String(), nullable=False),
        sa.Column("stage", sa.String(), nullable=False),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("prompt_hash", sa.String(), nullable=True),
        sa.Column("params", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_lineage_document_id", "lineage", ["document_id"])

    op.create_table(
        "decisions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("atom_id", UUID(as_uuid=True), nullable=False),
        sa.Column("atom_content_hash", sa.String(), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_decisions_client_id", "decisions", ["client_id"])

    # --- RLS: enable + FORCE on every tenant-scoped table -------------------
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        # NULLIF guards the '' left behind on a pooled connection after a
        # SET LOCAL on an otherwise-undefined GUC; ''::uuid would error.
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {table}
                USING (client_id = NULLIF(current_setting('app.client_id', true), '')::uuid)
                WITH CHECK (client_id = NULLIF(current_setting('app.client_id', true), '')::uuid)
            """
        )

    # --- Grants for the app role --------------------------------------------
    op.execute("GRANT USAGE ON SCHEMA public TO engine_app")
    op.execute("GRANT SELECT, INSERT, UPDATE ON clients TO engine_app")
    for table in TENANT_TABLES:
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO engine_app")


def downgrade() -> None:
    for table in reversed(TENANT_TABLES):
        op.drop_table(table)
    op.drop_table("clients")
