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
