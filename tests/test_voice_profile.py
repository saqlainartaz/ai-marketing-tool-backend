"""Voice profiles (M2) — keyless via the deterministic fake builder.

Requires `docker compose up -d`.
"""

import json
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


def _upload_and_wait(api: TestClient, cid: str, filename: str, content: bytes) -> None:
    doc_id = api.post(
        f"/v1/clients/{cid}/documents",
        files={"file": (filename, content, "text/plain")},
        data={"source_type": "sales_call_transcript"},
        headers=AUTH,
    ).json()["id"]
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        body = api.get(f"/v1/clients/{cid}/documents/{doc_id}", headers=AUTH).json()
        if body["status"] == "atomised":
            return
        assert body["status"] != "failed"
        time.sleep(0.05)
    raise AssertionError("pipeline did not finish")


def _build_and_wait(api: TestClient, cid: str, expect_version: int) -> dict:
    assert api.post(f"/v1/clients/{cid}/voice-profile", headers=AUTH).status_code == 202
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        response = api.get(f"/v1/clients/{cid}/voice-profile", headers=AUTH)
        if response.status_code == 200 and response.json()["version"] == expect_version:
            return response.json()
        time.sleep(0.05)
    raise AssertionError(f"profile v{expect_version} did not appear")


def test_build_versions_and_diff(api: TestClient) -> None:
    cid = api.post("/v1/clients", json={"name": "Voice Inc"}, headers=AUTH).json()["id"]

    # No atoms yet → refuse to queue.
    assert api.post(f"/v1/clients/{cid}/voice-profile", headers=AUTH).status_code == 409
    assert api.get(f"/v1/clients/{cid}/voice-profile", headers=AUTH).status_code == 404

    _upload_and_wait(api, cid, "call.txt", (FIXTURES / "transcript_raw.txt").read_bytes())
    profile = _build_and_wait(api, cid, expect_version=1)

    assert profile["status"] == "draft"
    payload = profile["payload"]
    assert payload["we_are"], "We Are section required"
    for entry in payload["we_are"]:
        assert entry["confidence"] in ("High", "Medium", "Low")
    assert profile["corpus"]["atom_count"] >= 2
    assert profile["diff"]["previous_version"] is None

    # Evidence cites real atoms of this client.
    atoms = {a["id"] for a in api.get(f"/v1/clients/{cid}/atoms", headers=AUTH).json()}
    cited = {
        e["atom_id"] for entry in payload["we_are"] for e in entry.get("evidence", [])
    }
    assert cited and cited <= atoms

    # Grow the corpus → version 2 with a diff.
    _upload_and_wait(api, cid, "call2.txt", b"Dana Reyes: Results doubled in six weeks.\n")
    second = _build_and_wait(api, cid, expect_version=2)
    assert second["diff"]["previous_version"] == 1
    assert second["diff"]["changed_sections"]
    assert second["corpus"]["atom_digest"] != profile["corpus"]["atom_digest"]

    versions = api.get(f"/v1/clients/{cid}/voice-profile/versions", headers=AUTH).json()
    assert [v["version"] for v in versions] == [2, 1]


def test_approve_workflow(api: TestClient) -> None:
    cid = api.post("/v1/clients", json={"name": "Approve Inc"}, headers=AUTH).json()["id"]
    _upload_and_wait(api, cid, "call.txt", (FIXTURES / "transcript_raw.txt").read_bytes())
    _build_and_wait(api, cid, expect_version=1)

    approved = api.post(f"/v1/clients/{cid}/voice-profile/1/approve", headers=AUTH)
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert api.get(f"/v1/clients/{cid}/voice-profile", headers=AUTH).json()["status"] == "approved"


def test_profiles_are_tenant_scoped(api: TestClient) -> None:
    cid = api.post("/v1/clients", json={"name": "Own Inc"}, headers=AUTH).json()["id"]
    _upload_and_wait(api, cid, "call.txt", (FIXTURES / "transcript_raw.txt").read_bytes())
    _build_and_wait(api, cid, expect_version=1)

    other = api.post("/v1/clients", json={"name": "Nosy Inc"}, headers=AUTH).json()["id"]
    assert api.get(f"/v1/clients/{other}/voice-profile", headers=AUTH).status_code == 404
    assert (
        api.post(f"/v1/clients/{other}/voice-profile/1/approve", headers=AUTH).status_code == 404
    )


def test_llm_builder_scrubs_invented_evidence() -> None:
    from content_engine.pipeline.voice_profile import LLMProfileBuilder

    class Scripted:
        name = "scripted"

        def generate(self, prompt, *, system=None, max_tokens=1024, temperature=0.0):
            return json.dumps(
                {
                    "executive_summary": "s",
                    "we_are": [
                        {
                            "attribute": "Real",
                            "counter": "Fake",
                            "what_it_means": "m",
                            "how_it_shows_up": "h",
                            "what_to_avoid": "a",
                            "evidence": [
                                {"atom_id": str(REAL_ID), "quote": "q"},
                                {"atom_id": "00000000-0000-0000-0000-00000000dead", "quote": "x"},
                            ],
                            "confidence": "High",
                        }
                    ],
                    "personality": {}, "tone_matrix": [], "terminology": {},
                    "language_that_works": {}, "language_to_avoid": [], "open_questions": [],
                }
            )

    import uuid as uuid_mod

    class StubAtom:
        def __init__(self):
            self.id = uuid_mod.uuid4()
            self.atom_type = "insight"
            self.status = "provisional"
            self.confidence = 0.5
            self.evidence_kind = "quoted"
            self.text = "text"
            self.payload = {}

    stub = StubAtom()
    global REAL_ID
    REAL_ID = stub.id
    payload, prompt_hash = LLMProfileBuilder(Scripted()).build([stub])
    evidence = payload["we_are"][0]["evidence"]
    assert [e["atom_id"] for e in evidence] == [str(stub.id)]
    assert prompt_hash
