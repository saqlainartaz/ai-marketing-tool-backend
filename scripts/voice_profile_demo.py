"""Live voice-profile build over the demo client's real atoms.

Requires: docker compose up -d, real keys in .env. Finds the most recent
client named 'Live Demo Client' (created by live_demo.py) and builds a
profile with the real LLM, then prints the highlights.
"""

import json
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from content_engine.config import Settings
from content_engine.db import tenant_session
from content_engine.models import Client, VoiceProfile
from content_engine.pipeline.voice_profile import build_voice_profile


def main() -> int:
    settings = Settings(service_api_key="x" * 32)
    engine = create_engine(settings.database_url)
    admin = create_engine(settings.admin_database_url)

    with Session(admin) as s:
        client = s.scalars(
            select(Client).where(Client.name == "Live Demo Client")
            .order_by(Client.created_at.desc()).limit(1)
        ).one_or_none()
        if client is None:
            print("run scripts/live_demo.py first")
            return 1
        client_id = client.id
    print(f"building voice profile for client {client_id} ...")

    build_voice_profile(engine, client_id)

    with tenant_session(engine, client_id) as s:
        profile = s.scalars(
            select(VoiceProfile).order_by(VoiceProfile.version.desc()).limit(1)
        ).one()
        payload = profile.payload
        print(f"\n=== Voice Profile v{profile.version} ({profile.built_by}) ===")
        print(f"corpus: {profile.corpus['atom_count']} atoms, "
              f"{len(profile.corpus['document_ids'])} documents\n")
        print("SUMMARY:", payload.get("executive_summary"), "\n")
        for entry in payload.get("we_are", []):
            n_evidence = len(entry.get("evidence", []))
            print(f"WE ARE: {entry['attribute']}  /  NOT: {entry['counter']} "
                  f"[{entry.get('confidence')}] ({n_evidence} cited)")
        personality = payload.get("personality") or {}
        print("\nARCHETYPE:", personality.get("archetype"))
        for row in payload.get("tone_matrix", [])[:4]:
            print(f"TONE {row.get('context')}: formality={row.get('formality')} "
                  f"energy={row.get('energy')} depth={row.get('technical_depth')}")
        terms = payload.get("terminology") or {}
        print("\nMUST USE:", [t.get("term") for t in terms.get("must_use", [])][:6])
        print("NEVER USE:", [t.get("term") for t in terms.get("never_use", [])][:6])
        for question in payload.get("open_questions", []):
            print(f"\nOPEN QUESTION [{question.get('priority')}]: {question.get('title')}")
            print(f"  found: {question.get('what_was_found')}")
            print(f"  recommendation: {question.get('recommendation')}")
        out = f"data/real-client/_voice_profile_v{profile.version}.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"\nfull payload saved to {out} (gitignored)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
