"""Voice profiles (M2): versioned, diffable, RLS-protected. Also relaxes
jobs.document_id so client-level jobs (profile builds) can queue.

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "voice_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("payload", JSONB(), nullable=False),
        sa.Column("corpus", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("diff", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("built_by", sa.String(), nullable=False),
        sa.Column("prompt_hash", sa.String(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.UniqueConstraint("client_id", "version", name="uq_voice_profiles_client_version"),
    )
    op.execute("ALTER TABLE voice_profiles ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE voice_profiles FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON voice_profiles
            USING (client_id = NULLIF(current_setting('app.client_id', true), '')::uuid)
            WITH CHECK (client_id = NULLIF(current_setting('app.client_id', true), '')::uuid)
        """
    )
    op.execute("GRANT SELECT, INSERT, UPDATE ON voice_profiles TO engine_app")

    # Client-level jobs (voice-profile builds) have no document.
    op.alter_column("jobs", "document_id", nullable=True)


def downgrade() -> None:
    op.alter_column("jobs", "document_id", nullable=False)
    op.drop_table("voice_profiles")
