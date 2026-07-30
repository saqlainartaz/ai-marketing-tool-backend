"""Hybrid search (Issue 10) — keyless via fake embedder, RLS-scoped.

Requires `docker compose up -d`.
"""

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from content_engine.config import Settings
from content_engine.main import create_app

FIXTURES = Path(__file__).parent / "fixtures"
KEY = "test-service-key-0123456789"
AUTH = {"X-API-Key": KEY}


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


def _onboard(api: TestClient, name: str) -> str:
    cid = api.post("/v1/clients", json={"name": name}, headers=AUTH).json()["id"]
    upload = api.post(
        f"/v1/clients/{cid}/documents",
        files={"file": ("call.txt", (FIXTURES / "transcript_raw.txt").read_bytes(), "text/plain")},
        data={"source_type": "sales_call_transcript"},
        headers=AUTH,
    )
    doc_id = upload.json()["id"]
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        status = api.get(f"/v1/clients/{cid}/documents/{doc_id}", headers=AUTH).json()["status"]
        if status == "atomised":
            return cid
        assert status != "failed"
        time.sleep(0.05)
    raise AssertionError("pipeline did not finish")


def test_search_returns_ranked_atoms_with_provenance(api: TestClient) -> None:
    cid = _onboard(api, "Search Inc")
    response = api.post(
        f"/v1/clients/{cid}/search", json={"query": "price steep Acme"}, headers=AUTH
    )
    assert response.status_code == 200
    results = response.json()
    assert results
    # Keyword leg must surface the objection about pricing at the top.
    assert "steep" in results[0]["text"]
    for hit in results:
        assert hit["client_id"] == cid
        assert hit["provenance"]
        assert hit["trust"] == "untrusted"
        assert hit["score"] > 0
    # Ranked: scores are non-increasing.
    scores = [hit["score"] for hit in results]
    assert scores == sorted(scores, reverse=True)


def test_search_type_filter(api: TestClient) -> None:
    cid = _onboard(api, "Filter Inc")
    results = api.post(
        f"/v1/clients/{cid}/search",
        json={"query": "payback weeks", "type": "proof_point"},
        headers=AUTH,
    ).json()
    assert results
    assert all(hit["atom_type"] == "proof_point" for hit in results)


def test_search_is_tenant_scoped(api: TestClient) -> None:
    cid_a = _onboard(api, "Tenant A")
    cid_b = api.post("/v1/clients", json={"name": "Tenant B"}, headers=AUTH).json()["id"]
    results = api.post(
        f"/v1/clients/{cid_b}/search", json={"query": "price steep Acme"}, headers=AUTH
    ).json()
    assert results == []
    # And A still sees its own.
    assert api.post(
        f"/v1/clients/{cid_a}/search", json={"query": "price"}, headers=AUTH
    ).json()


def test_empty_query_rejected(api: TestClient) -> None:
    cid = api.post("/v1/clients", json={"name": "Empty Inc"}, headers=AUTH).json()["id"]
    response = api.post(f"/v1/clients/{cid}/search", json={"query": "  "}, headers=AUTH)
    assert response.status_code == 422
