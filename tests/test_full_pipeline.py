"""Atomise + embed stages and the async jobs worker (Issue 5).

Requires `docker compose up -d`. Keyless: fake LLM + fake embedder only.
"""

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from content_engine.config import Settings
from content_engine.db import tenant_session
from content_engine.main import create_app
from content_engine.models import EMBEDDING_DIM, Atom, Client, Document, LineageRecord
from content_engine.pipeline.runner import run_full_pipeline
from content_engine.storage import LocalDiskStorage, content_address

FIXTURES = Path(__file__).parent / "fixtures"
KEY = "test-service-key-0123456789"
AUTH = {"X-API-Key": KEY}


@pytest.fixture()
def env(migrated_db, admin_engine, tmp_path: Path):
    engine = create_engine(migrated_db)
    storage = LocalDiskStorage(str(tmp_path / "raw"))
    with Session(admin_engine) as s, s.begin():
        client = Client(name="FullPipe Inc")
        s.add(client)
        s.flush()
        client_id = client.id
    yield engine, storage, client_id
    engine.dispose()


def _insert_fixture_doc(engine, storage, client_id):
    data = (FIXTURES / "transcript_raw.txt").read_bytes()
    sha = content_address(data)
    raw_path = storage.put(client_id, sha, data)
    with tenant_session(engine, client_id) as s:
        doc = Document(
            client_id=client_id,
            source_type="sales_call_transcript",
            sha256=sha,
            raw_path=raw_path,
        )
        s.add(doc)
        s.flush()
        return doc.id


def test_full_pipeline_persists_atoms_with_embeddings(env) -> None:
    engine, storage, client_id = env
    doc_id = _insert_fixture_doc(engine, storage, client_id)

    run_full_pipeline(engine, storage, client_id, doc_id)

    with tenant_session(engine, client_id) as s:
        doc = s.get(Document, doc_id)
        assert doc.status == "atomised"
        atoms = s.scalars(select(Atom).where(Atom.document_id == doc_id)).all()
        assert atoms
        for atom in atoms:
            assert atom.status == "provisional"
            assert atom.provenance
            assert atom.embedding is not None and len(atom.embedding) == EMBEDDING_DIM
        stages = {
            lr.stage for lr in s.scalars(
                select(LineageRecord).where(LineageRecord.document_id == doc_id)
            )
        }
        assert {"parse", "clean", "atomise", "embed"} <= stages


def test_reprocess_does_not_duplicate_atoms(env) -> None:
    engine, storage, client_id = env
    doc_id = _insert_fixture_doc(engine, storage, client_id)

    run_full_pipeline(engine, storage, client_id, doc_id)
    with tenant_session(engine, client_id) as s:
        first = sorted(
            a.content_hash for a in s.scalars(select(Atom).where(Atom.document_id == doc_id))
        )

    run_full_pipeline(engine, storage, client_id, doc_id)
    with tenant_session(engine, client_id) as s:
        second = sorted(
            a.content_hash for a in s.scalars(select(Atom).where(Atom.document_id == doc_id))
        )
    assert first == second


@pytest.fixture()
def api(migrated_db, tmp_path: Path):
    settings = Settings(
        _env_file=None,
        service_api_key=KEY,
        database_url=migrated_db,
        raw_storage_root=str(tmp_path / "raw"),
        job_poll_interval=0.05,
    )
    app = create_app(settings)
    with TestClient(app) as client:  # context manager runs lifespan → worker
        yield client


def _wait_for_status(client: TestClient, cid: str, doc_id: str, status: str, timeout=10.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        body = client.get(f"/v1/clients/{cid}/documents/{doc_id}", headers=AUTH).json()
        if body["status"] == status:
            return body
        if body["status"] == "failed":
            raise AssertionError(f"pipeline failed: {body}")
        time.sleep(0.05)
    raise AssertionError(f"timed out waiting for {status}")


def test_upload_triggers_worker_and_atoms_endpoint_serves_results(api: TestClient) -> None:
    cid = api.post("/v1/clients", json={"name": "Worker Inc"}, headers=AUTH).json()["id"]
    upload = api.post(
        f"/v1/clients/{cid}/documents",
        files={"file": ("call.txt", (FIXTURES / "transcript_raw.txt").read_bytes(), "text/plain")},
        data={"source_type": "sales_call_transcript"},
        headers=AUTH,
    )
    assert upload.status_code == 201
    doc_id = upload.json()["id"]

    _wait_for_status(api, cid, doc_id, "atomised")

    atoms = api.get(f"/v1/clients/{cid}/atoms", headers=AUTH).json()
    assert atoms
    for atom in atoms:
        assert atom["client_id"] == cid
        assert atom["provenance"]
        assert atom["trust"] == "untrusted"

    objections = api.get(f"/v1/clients/{cid}/atoms?type=objection", headers=AUTH).json()
    assert objections and all(a["atom_type"] == "objection" for a in objections)

    # Another client sees nothing.
    other = api.post("/v1/clients", json={"name": "Other Inc"}, headers=AUTH).json()["id"]
    assert api.get(f"/v1/clients/{other}/atoms", headers=AUTH).json() == []
