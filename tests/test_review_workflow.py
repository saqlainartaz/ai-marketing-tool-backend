"""M1C — operator review workflow: confirm / override / deprecate with an
append-only decisions log; confirmed atoms survive reprocessing; deprecated
atoms vanish from retrieval. Requires `docker compose up -d`. Keyless.
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


def _wait_atomised(api: TestClient, cid: str, doc_id: str, timeout=15.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        body = api.get(f"/v1/clients/{cid}/documents/{doc_id}", headers=AUTH).json()
        if body["status"] == "atomised":
            return
        assert body["status"] != "failed", body
        time.sleep(0.05)
    raise AssertionError("pipeline did not finish")


def _onboard(api: TestClient, name: str) -> tuple[str, str]:
    cid = api.post("/v1/clients", json={"name": name}, headers=AUTH).json()["id"]
    upload = api.post(
        f"/v1/clients/{cid}/documents",
        files={"file": ("call.txt", (FIXTURES / "transcript_raw.txt").read_bytes(), "text/plain")},
        data={"source_type": "sales_call_transcript"},
        headers=AUTH,
    )
    doc_id = upload.json()["id"]
    _wait_atomised(api, cid, doc_id)
    return cid, doc_id


def _decide(api: TestClient, cid: str, atom_id: str, **body):
    return api.post(f"/v1/clients/{cid}/atoms/{atom_id}/decision", json=body, headers=AUTH)


def test_confirm_promotes_and_logs(api: TestClient) -> None:
    cid, _ = _onboard(api, "Confirm Inc")
    atom = api.get(f"/v1/clients/{cid}/atoms?type=objection", headers=AUTH).json()[0]

    response = _decide(api, cid, atom["id"], decision="confirm",
                       reason="verified against the call", actor="saqlain")
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"

    decisions = api.get(f"/v1/clients/{cid}/decisions", headers=AUTH).json()
    assert any(
        d["atom_id"] == atom["id"] and d["decision"] == "confirm" and d["actor"] == "saqlain"
        for d in decisions
    )


def test_override_edits_text_and_confirms(api: TestClient) -> None:
    cid, _ = _onboard(api, "Override Inc")
    atom = api.get(f"/v1/clients/{cid}/atoms?type=objection", headers=AUTH).json()[0]

    response = _decide(api, cid, atom["id"], decision="override",
                       reason="tightened wording", actor="saqlain",
                       text="Price feels steep compared to Acme's quote.")
    assert response.status_code == 200
    updated = response.json()
    assert updated["status"] == "confirmed"
    assert updated["text"] == "Price feels steep compared to Acme's quote."
    assert updated["content_hash"] != atom["content_hash"]


def test_override_requires_changes(api: TestClient) -> None:
    cid, _ = _onboard(api, "BadOverride Inc")
    atom = api.get(f"/v1/clients/{cid}/atoms", headers=AUTH).json()[0]
    response = _decide(api, cid, atom["id"], decision="override", reason="no-op", actor="x")
    assert response.status_code == 422


def test_deprecated_atoms_vanish_from_retrieval(api: TestClient) -> None:
    cid, _ = _onboard(api, "Deprecate Inc")
    atom = api.get(f"/v1/clients/{cid}/atoms?type=objection", headers=AUTH).json()[0]
    assert "steep" in atom["text"]

    _decide(api, cid, atom["id"], decision="deprecate", reason="wrong speaker", actor="s")

    hits = api.post(f"/v1/clients/{cid}/search",
                    json={"query": "price steep Acme"}, headers=AUTH).json()
    assert all(h["id"] != atom["id"] for h in hits)

    bundle = api.post(f"/v1/clients/{cid}/context",
                      json={"task": "pricing objections"}, headers=AUTH).json()
    assert all(a["id"] != atom["id"] for a in bundle["atoms"])


def test_decisions_survive_reprocessing(api: TestClient) -> None:
    cid, doc_id = _onboard(api, "Survival Inc")
    atoms = api.get(f"/v1/clients/{cid}/atoms", headers=AUTH).json()
    confirmed = next(a for a in atoms if a["atom_type"] == "objection")
    deprecated = next(a for a in atoms if a["atom_type"] == "proof_point")

    _decide(api, cid, confirmed["id"], decision="confirm", reason="good", actor="s")
    _decide(api, cid, deprecated["id"], decision="deprecate", reason="bad", actor="s")

    assert api.post(
        f"/v1/clients/{cid}/documents/{doc_id}/reprocess", headers=AUTH
    ).status_code == 202
    time.sleep(0.3)
    _wait_atomised(api, cid, doc_id)

    after = api.get(f"/v1/clients/{cid}/atoms?limit=500", headers=AUTH).json()
    by_hash = {a["content_hash"]: a for a in after}
    # Confirmed atom survives, same identity, still confirmed.
    assert by_hash[confirmed["content_hash"]]["id"] == confirmed["id"]
    assert by_hash[confirmed["content_hash"]]["status"] == "confirmed"
    # Deprecated atom stays suppressed rather than resurrected as provisional.
    assert by_hash[deprecated["content_hash"]]["status"] == "deprecated"
    # No duplicates.
    assert len(by_hash) == len(after)


def test_decision_is_tenant_scoped(api: TestClient) -> None:
    cid, _ = _onboard(api, "Mine Inc")
    atom = api.get(f"/v1/clients/{cid}/atoms", headers=AUTH).json()[0]
    other = api.post("/v1/clients", json={"name": "Other Inc"}, headers=AUTH).json()["id"]
    response = _decide(api, other, atom["id"], decision="confirm", reason="steal", actor="x")
    assert response.status_code == 404
