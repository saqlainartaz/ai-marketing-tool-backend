import asyncio
import contextlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import create_engine

from content_engine.api import atoms, clients, documents
from content_engine.config import Settings
from content_engine.jobs import worker_loop
from content_engine.storage import LocalDiskStorage


def create_app(settings: Settings | None = None) -> FastAPI:
    # Fail-closed: Settings() raises if the service token is missing/invalid,
    # so the app refuses to boot without tenant-auth config.
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        task: asyncio.Task | None = None
        if settings.worker_enabled:
            worker_engine = create_engine(settings.worker_database_url)
            task = asyncio.create_task(
                worker_loop(
                    worker_engine,
                    app.state.engine,
                    app.state.storage,
                    settings.job_poll_interval,
                )
            )
        yield
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    app = FastAPI(title="Client Content Engine", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = create_engine(settings.database_url)
    app.state.storage = LocalDiskStorage(settings.raw_storage_root)

    app.include_router(clients.router)
    app.include_router(documents.router)
    app.include_router(atoms.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
