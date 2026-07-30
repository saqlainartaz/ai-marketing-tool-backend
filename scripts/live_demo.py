"""Live end-to-end demo (Issue 12): real client documents through the full
stack — upload API -> worker -> Claude extraction -> Voyage embeddings ->
Postgres (RLS) -> /search and /context.

Requires: docker compose up -d, ANTHROPIC_API_KEY + VOYAGE_API_KEY in .env.
Usage: python -m uv run python scripts/live_demo.py
"""

import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient

from content_engine.config import Settings
from content_engine.main import create_app

DATA = Path("data/real-client")
KEY = "live-demo-service-key-0123456789"
AUTH = {"X-API-Key": KEY}
DOCS = [
    ("keira-brinton__interview_transcript.txt", "sales_call_transcript"),
    ("barbara-parker__onboarding_form.md", "onboarding_form"),
]


def main() -> int:
    settings = Settings(service_api_key=KEY, raw_storage_root="./data/raw", job_poll_interval=0.2)
    app = create_app(settings)
    with TestClient(app) as api:
        cid = api.post(
            "/v1/clients", json={"name": "Live Demo Client"}, headers=AUTH
        ).json()["id"]
        print(f"client: {cid}")

        doc_ids = []
        for filename, source_type in DOCS:
            response = api.post(
                f"/v1/clients/{cid}/documents",
                files={"file": (filename, (DATA / filename).read_bytes(), "text/plain")},
                data={"source_type": source_type},
                headers=AUTH,
            )
            doc_ids.append(response.json()["id"])
            print(f"uploaded {filename} -> {response.json()['id']}")

        deadline = time.monotonic() + 600
        pending = set(doc_ids)
        while pending and time.monotonic() < deadline:
            for doc_id in list(pending):
                body = api.get(f"/v1/clients/{cid}/documents/{doc_id}", headers=AUTH).json()
                if body["status"] == "atomised":
                    pending.discard(doc_id)
                    print(f"  atomised: {doc_id}")
                elif body["status"] == "failed":
                    print(f"  FAILED: {doc_id}")
                    return 1
            time.sleep(2)
        if pending:
            print("timed out waiting for pipeline")
            return 1

        atoms = api.get(f"/v1/clients/{cid}/atoms?limit=500", headers=AUTH).json()
        print(f"\ntotal atoms: {len(atoms)}")

        print("\n=== /search: 'what objections do prospects raise?' ===")
        hits = api.post(
            f"/v1/clients/{cid}/search",
            json={"query": "what objections do prospects raise?", "limit": 5},
            headers=AUTH,
        ).json()
        for hit in hits:
            prov = hit["provenance"]
            print(f"[{hit['atom_type']:<14}] score={hit['score']:.4f} "
                  f"L{prov.get('line')} {prov.get('speaker', '')}")
            print(f"  {hit['text'][:160]}")

        print("\n=== /context: 'write a landing page about overcoming self-doubt' ===")
        bundle = api.post(
            f"/v1/clients/{cid}/context",
            json={"task": "write a landing page about overcoming self-doubt", "limit": 8},
            headers=AUTH,
        ).json()
        print(f"voice.tone: {bundle['voice']['tone'][:2]}")
        print(f"voice.do_phrases: {bundle['voice']['do_phrases'][:3]}")
        print(f"voice.avoid_phrases: {bundle['voice']['avoid_phrases'][:3]}")
        print(f"constraints: {len(bundle['constraints'])} | atoms: {len(bundle['atoms'])} "
              f"| full_corpus docs: {len(bundle['full_corpus'])} "
              f"| completeness: {bundle['completeness']}")
        for atom in bundle["atoms"][:5]:
            print(f"  [{atom['atom_type']:<14}] {atom['text'][:120]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
