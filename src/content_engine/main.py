from fastapi import FastAPI
from sqlalchemy import create_engine

from content_engine.api import clients, documents
from content_engine.config import Settings
from content_engine.storage import LocalDiskStorage


def create_app(settings: Settings | None = None) -> FastAPI:
    # Fail-closed: Settings() raises if the service token is missing/invalid,
    # so the app refuses to boot without tenant-auth config.
    settings = settings or Settings()

    app = FastAPI(title="Client Content Engine", version="0.1.0")
    app.state.settings = settings
    app.state.engine = create_engine(settings.database_url)
    app.state.storage = LocalDiskStorage(settings.raw_storage_root)

    app.include_router(clients.router)
    app.include_router(documents.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
