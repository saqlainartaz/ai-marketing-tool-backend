from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from content_engine.auth import require_service_token
from content_engine.config import Settings

KEY = "test-service-key-0123456789"


def _app_with_protected_route() -> FastAPI:
    app = FastAPI()
    app.state.settings = Settings(_env_file=None, service_api_key=KEY)

    @app.get("/protected", dependencies=[Depends(require_service_token)])
    def protected() -> dict[str, str]:
        return {"ok": "yes"}

    return app


def test_missing_key_is_401() -> None:
    client = TestClient(_app_with_protected_route())
    assert client.get("/protected").status_code == 401


def test_wrong_key_is_401() -> None:
    client = TestClient(_app_with_protected_route())
    response = client.get("/protected", headers={"X-API-Key": "wrong-key-wrong-key"})
    assert response.status_code == 401


def test_valid_key_passes() -> None:
    client = TestClient(_app_with_protected_route())
    response = client.get("/protected", headers={"X-API-Key": KEY})
    assert response.status_code == 200
    assert response.json() == {"ok": "yes"}
