"""Pipeline stage runner: parse → clean, with lineage per transformation.

Idempotent: re-running over the same document converges to the same derived
artifacts and status. The atomise/embed stages join in Issue 5.
"""

import uuid

from sqlalchemy import Engine, delete

from content_engine.db import tenant_session
from content_engine.models import Atom, Document, LineageRecord
from content_engine.pipeline.atomise import ATOMIZER_VERSION, extract_atoms
from content_engine.pipeline.clean import clean_for
from content_engine.pipeline.parse import PARSER_VERSION, parse_text
from content_engine.providers import get_embedding_provider
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


def run_atomise_and_embed(
    engine: Engine,
    storage: RawStorage,
    client_id: uuid.UUID,
    document_id: uuid.UUID,
) -> None:
    """Extract typed atoms from the cleaned text and embed them.

    Idempotent by replacement: a document's atoms are deleted and re-extracted
    atomically; identical input yields identical content hashes. (Confirmed-atom
    survival across replacement lands in M1C via the decisions log.)
    """
    embedder = get_embedding_provider()

    with tenant_session(engine, client_id) as session:
        doc = session.get(Document, document_id)
        if doc is None or doc.cleaned_path is None:
            raise ValueError(f"document {document_id} is not cleaned yet")

        cleaned = storage.get(doc.cleaned_path).decode("utf-8", errors="replace")
        extracted = extract_atoms(doc.source_type, cleaned)
        vectors = embedder.embed([a.text for a in extracted])

        session.execute(delete(Atom).where(Atom.document_id == doc.id))
        for atom, vector in zip(extracted, vectors, strict=True):
            session.add(
                Atom(
                    client_id=client_id,
                    document_id=doc.id,
                    atom_type=atom.atom_type,
                    text=atom.text,
                    payload=atom.payload,
                    provenance=atom.provenance,
                    confidence=atom.confidence,
                    impact=atom.impact,
                    evidence_kind=atom.evidence_kind,
                    content_hash=atom.content_hash,
                    pipeline_version=doc.pipeline_version,
                    embedding=vector,
                )
            )
        session.add(
            LineageRecord(
                client_id=client_id,
                document_id=doc.id,
                source_sha=doc.sha256,
                stage="atomise",
                actor=ATOMIZER_VERSION,
                params={"atoms": len(extracted)},
            )
        )
        session.add(
            LineageRecord(
                client_id=client_id,
                document_id=doc.id,
                source_sha=doc.sha256,
                stage="embed",
                actor=f"embedder:{embedder.name}",
                params={"count": len(extracted)},
            )
        )
        doc.status = "atomised"


def run_full_pipeline(
    engine: Engine,
    storage: RawStorage,
    client_id: uuid.UUID,
    document_id: uuid.UUID,
) -> None:
    run_parse_and_clean(engine, storage, client_id, document_id)
    run_atomise_and_embed(engine, storage, client_id, document_id)
