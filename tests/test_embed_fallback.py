"""Search and /context must degrade to keyword-only retrieval when the
embedding provider is unavailable (e.g. Voyage rate-limited) — never 500.

Requires `docker compose up -d`. Keyless.
"""

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from content_engine.api import context as context_module
from content_engine.api import search as search_module
from content_engine.config import Settings
from content_engine.main import create_app

FIXTURES = Path(__file__).parent / "fixtures"
KEY = "test-service-key-0123456789"
AUTH = {"X-API-Key": KEY}


class ExplodingEmbedder:
    name = "exploding"

    def embed(self, texts, *, input_type="document"):
        raise RuntimeError("rate limited")


@pytest.fixture()
def api(migrated_db, tmp_path: Path):
    settings = Settings(
        _env_file=None,
        service_api_key=KEY,
        database_url=migrated_db,
        raw_storage_root=str(tmp_path / "raw"),
        job_poll_interval=0.05,
    )
    with TestClient(create_app(settings)) as client:
        yield client


def _onboard(api: TestClient) -> str:
    cid = api.post("/v1/clients", json={"name": "Fallback Inc"}, headers=AUTH).json()["id"]
    doc_id = api.post(
        f"/v1/clients/{cid}/documents",
        files={"file": ("call.txt", (FIXTURES / "transcript_raw.txt").read_bytes(), "text/plain")},
        data={"source_type": "sales_call_transcript"},
        headers=AUTH,
    ).json()["id"]
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if api.get(f"/v1/clients/{cid}/documents/{doc_id}", headers=AUTH).json()[
            "status"
        ] == "atomised":
            return cid
        time.sleep(0.05)
    raise AssertionError("pipeline did not finish")


def test_search_survives_embedder_outage(api: TestClient, monkeypatch) -> None:
    cid = _onboard(api)
    monkeypatch.setattr(
        search_module, "get_embedding_provider", lambda *a, **k: ExplodingEmbedder()
    )
    response = api.post(
        f"/v1/clients/{cid}/search", json={"query": "price steep Acme"}, headers=AUTH
    )
    assert response.status_code == 200
    results = response.json()
    assert results, "keyword leg should still return the pricing objection"
    assert "steep" in results[0]["text"]


def test_context_survives_embedder_outage(api: TestClient, monkeypatch) -> None:
    cid = _onboard(api)
    monkeypatch.setattr(
        context_module, "get_embedding_provider", lambda *a, **k: ExplodingEmbedder()
    )
    response = api.post(
        f"/v1/clients/{cid}/context", json={"task": "price steep"}, headers=AUTH
    )
    assert response.status_code == 200
    bundle = response.json()
    assert bundle["atoms"], "keyword-only retrieval should still fill the bundle"
    assert bundle["completeness"]["atoms"] >= 1
