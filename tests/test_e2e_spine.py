"""M1A end-to-end spine demo — acceptance criteria 1-4, 8-11 of docs/M1_SCOPE.md.

Two clients, three documents, full keyless pipeline through the worker, atoms
with provenance, tenant isolation via the API, dedupe, and reprocess idempotency.
Requires `docker compose up -d`. Zero API keys.
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

DOCS = [
    ("transcript_raw.txt", "sales_call_transcript", "CONVERSATIONAL"),
    ("onboarding_form.md", "onboarding_form", "OPERATIONAL"),
    ("brand_doc.md", "brand_doc", "AUTHORITATIVE"),
]


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


def _upload(api: TestClient, cid: str, filename: str, source_type: str, authority: str):
    return api.post(
        f"/v1/clients/{cid}/documents",
        files={"file": (filename, (FIXTURES / filename).read_bytes(), "text/plain")},
        data={"source_type": source_type, "source_authority": authority},
        headers=AUTH,
    )


def _wait_atomised(api: TestClient, cid: str, doc_id: str, timeout=15.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        body = api.get(f"/v1/clients/{cid}/documents/{doc_id}", headers=AUTH).json()
        if body["status"] == "atomised":
            return
        assert body["status"] != "failed", f"pipeline failed: {body}"
        time.sleep(0.05)
    raise AssertionError("timed out waiting for atomised")


def test_m1a_spine_demo(api: TestClient) -> None:
    # 1. Two clients.
    cid_a = api.post("/v1/clients", json={"name": "Client A"}, headers=AUTH).json()["id"]
    cid_b = api.post("/v1/clients", json={"name": "Client B"}, headers=AUTH).json()["id"]

    # 2. Three fixture documents for A; 3. overlapping content for B.
    doc_ids = []
    for filename, source_type, authority in DOCS:
        response = _upload(api, cid_a, filename, source_type, authority)
        assert response.status_code == 201
        doc_ids.append(response.json()["id"])
    assert _upload(api, cid_b, "transcript_raw.txt", "sales_call_transcript",
                   "CONVERSATIONAL").status_code == 201

    # 4. Pipeline produces provisional atoms for every document.
    for doc_id in doc_ids:
        _wait_atomised(api, cid_a, doc_id)
    atoms_a = api.get(f"/v1/clients/{cid_a}/atoms", headers=AUTH).json()
    assert atoms_a
    assert all(a["status"] == "provisional" for a in atoms_a)

    # Objections from the sales call are retrievable with full provenance.
    objections = api.get(f"/v1/clients/{cid_a}/atoms?type=objection", headers=AUTH).json()
    assert objections
    for atom in objections:
        assert atom["client_id"] == cid_a
        assert atom["document_id"] == doc_ids[0]
        assert atom["provenance"].get("speaker")
        assert atom["evidence_kind"] == "quoted"
        assert atom["trust"] == "untrusted"

    # 8. Client B cannot retrieve Client A's atoms through the API.
    atoms_b = api.get(f"/v1/clients/{cid_b}/atoms", headers=AUTH).json()
    assert atoms_b == [] or all(a["client_id"] == cid_b for a in atoms_b)

    # 9. Re-upload of the same file creates no duplicates.
    re_upload = _upload(api, cid_a, "transcript_raw.txt", "sales_call_transcript",
                        "CONVERSATIONAL")
    assert re_upload.status_code == 200
    assert re_upload.json()["id"] == doc_ids[0]
    docs = api.get(f"/v1/clients/{cid_a}/documents", headers=AUTH).json()
    assert len(docs) == 3

    # 10. Reprocess does not duplicate atoms.
    before = sorted(a["content_hash"] for a in atoms_a)
    reprocess = api.post(
        f"/v1/clients/{cid_a}/documents/{doc_ids[0]}/reprocess", headers=AUTH
    )
    assert reprocess.status_code == 202
    time.sleep(0.2)
    _wait_atomised(api, cid_a, doc_ids[0])
    after = sorted(
        a["content_hash"]
        for a in api.get(f"/v1/clients/{cid_a}/atoms", headers=AUTH).json()
    )
    assert after == before
