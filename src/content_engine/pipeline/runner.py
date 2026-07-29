"""Pipeline stage runner: parse → clean, with lineage per transformation.

Idempotent: re-running over the same document converges to the same derived
artifacts and status. The atomise/embed stages join in Issue 5.
"""

import uuid

from sqlalchemy import Engine

from content_engine.db import tenant_session
from content_engine.models import Document, LineageRecord
from content_engine.pipeline.clean import clean_for
from content_engine.pipeline.parse import PARSER_VERSION, parse_text
from content_engine.storage import RawStorage


def run_parse_and_clean(
    engine: Engine,
    storage: RawStorage,
    client_id: uuid.UUID,
    document_id: uuid.UUID,
) -> None:
    with tenant_session(engine, client_id) as session:
        doc = session.get(Document, document_id)
        if doc is None:
            raise ValueError(f"document {document_id} not found for tenant")

        raw = storage.get(doc.raw_path).decode("utf-8", errors="replace")

        parsed = parse_text(raw)
        session.add(
            LineageRecord(
                client_id=client_id,
                document_id=doc.id,
                source_sha=doc.sha256,
                stage="parse",
                actor=PARSER_VERSION,
                params={"sections": len(parsed.sections)},
            )
        )
        doc.status = "parsed"

        cleaned, cleaner_actor = clean_for(doc.source_type, raw)
        doc.cleaned_path = storage.put_derived(
            client_id, f"{doc.sha256}.cleaned.txt", cleaned.encode("utf-8")
        )
        session.add(
            LineageRecord(
                client_id=client_id,
                document_id=doc.id,
                source_sha=doc.sha256,
                stage="clean",
                actor=cleaner_actor,
            )
        )
        doc.status = "cleaned"
