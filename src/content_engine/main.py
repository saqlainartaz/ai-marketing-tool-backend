from fastapi import FastAPI

from content_engine.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    # Fail-closed: Settings() raises if the service token is missing/invalid,
    # so the app refuses to boot without tenant-auth config.
    settings = settings or Settings()

    app = FastAPI(title="Client Content Engine", version="0.1.0")
    app.state.settings = settings

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
