import os

import pytest

# Tests are keyless and deterministic by design: pin the fake providers even
# when a developer's .env switches the app to real ones. The live-smoke tests
# opt in explicitly via get_llm_provider("anthropic") etc., so they still run.
os.environ["ENGINE_LLM_PROVIDER"] = "fake"
os.environ["ENGINE_EMBEDDING_PROVIDER"] = "fake"
# The service token is our own config, required for fail-closed startup.
os.environ.setdefault("SERVICE_API_KEY", "test-service-key-0123456789")

# Tests run against a DEDICATED database (created on demand) so the suite can
# never wipe local dev data. Hard-set — .env must not redirect tests.
_MAINT_URL = "postgresql+psycopg://content_engine:content_engine_dev@localhost:5432/content_engine"
TEST_DB = "content_engine_test"
ADMIN_URL = f"postgresql+psycopg://content_engine:content_engine_dev@localhost:5432/{TEST_DB}"
APP_URL = f"postgresql+psycopg://engine_app:engine_app_dev@localhost:5432/{TEST_DB}"
os.environ["ADMIN_DATABASE_URL"] = ADMIN_URL
os.environ["DATABASE_URL"] = APP_URL
os.environ["WORKER_DATABASE_URL"] = (
    f"postgresql+psycopg://engine_worker:engine_worker_dev@localhost:5432/{TEST_DB}"
)


@pytest.fixture(scope="session")
def migrated_db():
    """Reset the dockerized dev database and run migrations to head.

    Requires `docker compose up -d`. Migrations run as the admin role;
    the app connects as the non-superuser `engine_app` role (RLS applies).
    """
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, text

    maint_engine = create_engine(_MAINT_URL, isolation_level="AUTOCOMMIT")
    with maint_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": TEST_DB}
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{TEST_DB}"'))
    maint_engine.dispose()

    admin_engine = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    admin_engine.dispose()

    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
    return APP_URL


@pytest.fixture()
def app_engine(migrated_db):
    from sqlalchemy import create_engine

    engine = create_engine(migrated_db)
    yield engine
    engine.dispose()


@pytest.fixture()
def admin_engine(migrated_db):
    from sqlalchemy import create_engine

    engine = create_engine(ADMIN_URL)
    yield engine
    engine.dispose()
