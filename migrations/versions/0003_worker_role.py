"""Worker role: cross-tenant jobs dequeue via an explicit RLS policy.

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-29

The pipeline worker must see queued jobs across tenants. Rather than bypassing
RLS (forbidden), `engine_worker` gets an explicit policy on the jobs table only;
document/atom work still runs through tenant-scoped sessions as `engine_app`.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'engine_worker') THEN
                CREATE ROLE engine_worker LOGIN PASSWORD 'engine_worker_dev'
                    NOSUPERUSER NOBYPASSRLS;
            END IF;
        END
        $$;
        """
    )
    op.execute("GRANT USAGE ON SCHEMA public TO engine_worker")
    op.execute("GRANT SELECT, UPDATE ON jobs TO engine_worker")
    op.execute(
        """
        CREATE POLICY worker_jobs_access ON jobs
            AS PERMISSIVE FOR ALL TO engine_worker
            USING (true) WITH CHECK (true)
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS worker_jobs_access ON jobs")
    op.execute("REVOKE ALL ON jobs FROM engine_worker")
