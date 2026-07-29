from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="Client Content Engine", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
