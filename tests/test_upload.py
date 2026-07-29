"""Upload + sha256 dedupe (Issue 3). Requires `docker compose up -d`."""

import hashlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from content_engine.config import Settings
from content_engine.main import create_app

KEY = "test-service-key-0123456789"
AUTH = {"X-API-Key": KEY}


@pytest.fixture()
def client(migrated_db, tmp_path: Path) -> TestClient:
    settings = Settings(
        _env_file=None,
        service_api_key=KEY,
        database_url=migrated_db,
        raw_storage_root=str(tmp_path / "raw"),
    )
    app = create_app(settings)
    return TestClient(app)


def _make_client(client: TestClient, name: str) -> str:
    response = client.post("/v1/clients", json={"name": name}, headers=AUTH)
    assert response.status_code == 201
    return response.json()["id"]


def _upload(client: TestClient, client_id: str, content: bytes, **form):
    return client.post(
        f"/v1/clients/{client_id}/documents",
        files={"file": ("call.txt", content, "text/plain")},
        data={"source_type": "sales_call_transcript", **form},
        headers=AUTH,
    )


def test_upload_requires_service_token(client: TestClient) -> None:
    response = client.post("/v1/clients", json={"name": "NoAuth Inc"})
    assert response.status_code == 401


def test_upload_creates_document_with_content_address(client: TestClient, tmp_path: Path) -> None:
    cid = _make_client(client, "Acme")
    content = b"PROSPECT: What about pricing?\nREP: Great question."

    response = _upload(client, cid, content)
    assert response.status_code == 201
    doc = response.json()
    assert doc["sha256"] == hashlib.sha256(content).hexdigest()
    assert doc["status"] == "uploaded"
    assert doc["source_type"] == "sales_call_transcript"
    assert doc["source_authority"] == "CONVERSATIONAL"  # default tier
    assert doc["client_id"] == cid

    # Raw file is stored content-addressed and immutable.
    raw = list((tmp_path / "raw").rglob(doc["sha256"]))
    assert len(raw) == 1
    assert raw[0].read_bytes() == content


def test_duplicate_upload_creates_no_duplicates(client: TestClient) -> None:
    cid = _make_client(client, "Dup Inc")
    content = b"same bytes every time"

    first = _upload(client, cid, content)
    second = _upload(client, cid, content)
    assert first.status_code == 201
    assert second.status_code == 200  # dedupe: existing document returned
    assert second.json()["id"] == first.json()["id"]

    listing = client.get(f"/v1/clients/{cid}/documents", headers=AUTH)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_same_bytes_different_clients_are_separate_documents(client: TestClient) -> None:
    cid_a = _make_client(client, "A Corp")
    cid_b = _make_client(client, "B Corp")
    content = b"shared onboarding template"

    doc_a = _upload(client, cid_a, content)
    doc_b = _upload(client, cid_b, content)
    assert doc_a.status_code == 201
    assert doc_b.status_code == 201
    assert doc_a.json()["id"] != doc_b.json()["id"]

    # Each client lists only its own document (RLS-scoped endpoint).
    listing_a = client.get(f"/v1/clients/{cid_a}/documents", headers=AUTH)
    assert [d["client_id"] for d in listing_a.json()] == [cid_a]


def test_document_detail_returns_provenance_fields(client: TestClient) -> None:
    cid = _make_client(client, "Detail Inc")
    response = _upload(client, cid, b"detail body", source_authority="OPERATIONAL")
    doc_id = response.json()["id"]

    detail = client.get(f"/v1/clients/{cid}/documents/{doc_id}", headers=AUTH)
    assert detail.status_code == 200
    body = detail.json()
    assert body["source_authority"] == "OPERATIONAL"
    assert body["sha256"]
    assert body["pipeline_version"] == 1


def test_invalid_source_type_rejected(client: TestClient) -> None:
    cid = _make_client(client, "Bad Type Inc")
    response = client.post(
        f"/v1/clients/{cid}/documents",
        files={"file": ("x.txt", b"body", "text/plain")},
        data={"source_type": "not_a_real_type"},
        headers=AUTH,
    )
    assert response.status_code == 422
