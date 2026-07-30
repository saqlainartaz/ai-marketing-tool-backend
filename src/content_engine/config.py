from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Fail-closed configuration: the service refuses to boot without a valid
    service token (tenant-auth config). See docs/API_CONTRACT.md."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Authenticates the calling service (Next.js server). Required, no default.
    service_api_key: SecretStr = Field(min_length=16)

    # App connection — non-superuser role, subject to RLS.
    database_url: str = (
        "postgresql+psycopg://engine_app:engine_app_dev@localhost:5432/content_engine"
    )
    # Admin connection — migrations only. Never used to serve requests.
    admin_database_url: str = (
        "postgresql+psycopg://content_engine:content_engine_dev@localhost:5432/content_engine"
    )

    # Worker connection — sees jobs across tenants via an explicit RLS policy
    # (migration 0003); never used for document/atom access.
    worker_database_url: str = (
        "postgresql+psycopg://engine_worker:engine_worker_dev@localhost:5432/content_engine"
    )

    # Immutable raw-file store (local disk in dev; S3-compatible interface).
    raw_storage_root: str = "./data/raw"

    # In-process pipeline worker (no Redis/Celery in M1).
    worker_enabled: bool = True
    job_poll_interval: float = 0.5

    # /context fast path: include the whole cleaned corpus in the bundle when a
    # client's corpus is at most this many characters (long-context consumers
    # can then read everything; atoms remain the durable representation).
    context_full_corpus_max_chars: int = 100_000
