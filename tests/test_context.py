"""/context bundle (Issue 11) — keyless. Requires `docker compose up -d`.

The bundle is authority-ordered: voice snapshot, then hard constraints
(claims_blacklist + voice_constraint — always included), then task-relevant
atoms (hybrid-searched, confirmed-first), plus the full cleaned corpus when
the client is small enough (the fast path for 1M-context consumers).
"""

import time
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select

from content_engine.config import Settings
from content_engine.db import tenant_session
from content_engine.main import create_app
from content_engine.models import Atom, Document

FIXTURES = Path(__file__).parent / "fixtures"
KEY = "test-service-key-0123456789"
AUTH = {"X-API-Key": KEY}


@pytest.fixture()
def env(migrated_db, tmp_path: Path):
    settings = Settings(
        _env_file=None,
        service_api_key=KEY,
        database_url=migrated_db,
        raw_storage_root=str(tmp_path / "raw"),
        job_poll_interval=0.05,
    )
    engine = create_engine(migrated_db)
    with TestClient(create_app(settings)) as client:
        yield client, engine
    engine.dispose()


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
        body = api.get(f"/v1/clients/{cid}/documents/{doc_id}", headers=AUTH).json()
        if body["status"] == "atomised":
            return cid
        assert body["status"] != "failed"
        time.sleep(0.05)
    raise AssertionError("pipeline did not finish")


def _add_constraint_atom(engine, cid: str) -> None:
    client_id = uuid.UUID(cid)
    with tenant_session(engine, client_id) as s:
        doc = s.scalars(select(Document)).first()
        s.add(
            Atom(
                client_id=client_id,
                document_id=doc.id,
                atom_type="claims_blacklist",
                text="Never promise specific payback timelines.",
                payload={"say_instead": "Most teams report fast results."},
                provenance={"line": 3},
                evidence_kind="inferred",
                content_hash="manual-blacklist-1",
            )
        )


def test_context_bundle_shape_and_ordering(env) -> None:
    api, engine = env
    cid = _onboard(api, "Context Inc")
    _add_constraint_atom(engine, cid)

    response = api.post(
        f"/v1/clients/{cid}/context", json={"task": "handle pricing objections"}, headers=AUTH
    )
    assert response.status_code == 200
    bundle = response.json()

    # Voice snapshot: brand-loom shape, every field optional but keys present.
    assert set(bundle["voice"]) == {"tone", "audience", "do_phrases", "avoid_phrases"}
    assert "Never promise specific payback timelines." in bundle["voice"]["avoid_phrases"]

    # Constraints always ride along, regardless of task relevance.
    assert any(a["atom_type"] == "claims_blacklist" for a in bundle["constraints"])
    for atom in bundle["constraints"]:
        assert atom["client_id"] == cid
        assert "stale" in atom

    # Task-relevant atoms: ranked, provenance-rich, untrusted-labeled.
    assert bundle["atoms"]
    for atom in bundle["atoms"]:
        assert atom["client_id"] == cid
        assert atom["provenance"]
        assert atom["trust"] == "untrusted"

    # Small corpus -> full cleaned text included (fast path).
    assert bundle["full_corpus"]
    assert "payback" in bundle["full_corpus"][0]["text"]

    assert bundle["completeness"]["documents"] == 1
    assert bundle["completeness"]["atoms"] >= 2


def test_confirmed_atoms_rank_first(env) -> None:
    api, engine = env
    cid = _onboard(api, "Confirmed Inc")
    client_id = uuid.UUID(cid)
    with tenant_session(engine, client_id) as s:
        atom = s.scalars(select(Atom).where(Atom.atom_type == "proof_point")).first()
        atom.status = "confirmed"

    bundle = api.post(
        f"/v1/clients/{cid}/context", json={"task": "payback results"}, headers=AUTH
    ).json()
    statuses = [a["status"] for a in bundle["atoms"]]
    assert statuses[0] == "confirmed"
    assert statuses == sorted(statuses, key=lambda s: s != "confirmed")


def test_context_is_tenant_scoped(env) -> None:
    api, engine = env
    _onboard(api, "Owner Inc")
    other = api.post("/v1/clients", json={"name": "Intruder Inc"}, headers=AUTH).json()["id"]
    bundle = api.post(
        f"/v1/clients/{other}/context", json={"task": "pricing"}, headers=AUTH
    ).json()
    assert bundle["atoms"] == []
    assert bundle["constraints"] == []
    assert bundle["full_corpus"] == []


def test_large_corpus_skips_fast_path(env, monkeypatch) -> None:
    api, engine = env
    cid = _onboard(api, "Big Inc")
    # Shrink the threshold below the fixture size instead of uploading megabytes.
    api.app.state.settings.context_full_corpus_max_chars = 10
    bundle = api.post(
        f"/v1/clients/{cid}/context", json={"task": "pricing"}, headers=AUTH
    ).json()
    assert bundle["full_corpus"] == []
    assert bundle["atoms"]  # atoms still served


def test_blank_task_rejected(env) -> None:
    api, _ = env
    cid = api.post("/v1/clients", json={"name": "Blank Inc"}, headers=AUTH).json()["id"]
    assert (
        api.post(f"/v1/clients/{cid}/context", json={"task": " "}, headers=AUTH).status_code
        == 422
    )
