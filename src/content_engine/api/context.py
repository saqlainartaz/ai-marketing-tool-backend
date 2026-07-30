"""The context-injection endpoint — the engine's payoff surface.

Downstream generators call this with a task and get an authority-ordered
bundle: voice snapshot (brand-loom shape) → hard constraints (blacklists and
voice rules, always included) → task-relevant atoms (hybrid-searched,
confirmed-first) → the full cleaned corpus when the client is small enough
for a long-context consumer to just read everything.
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from content_engine.api.schemas import AtomOut
from content_engine.auth import require_service_token
from content_engine.db import tenant_session
from content_engine.models import Atom, Document
from content_engine.providers import get_embedding_provider
from content_engine.search import hybrid_search

router = APIRouter(
    prefix="/v1/clients/{client_id}",
    tags=["context"],
    dependencies=[Depends(require_service_token)],
)

CONSTRAINT_TYPES = ("claims_blacklist", "voice_constraint")


class ContextRequest(BaseModel):
    task: str = Field(min_length=1, pattern=r"\S")
    limit: int = Field(default=25, ge=1, le=100)


class ContextAtomOut(AtomOut):
    stale: bool = False
    score: float | None = None


class VoiceSnapshot(BaseModel):
    tone: list[str] = []
    audience: str | None = None
    do_phrases: list[str] = []
    avoid_phrases: list[str] = []


class CorpusDocOut(BaseModel):
    document_id: uuid.UUID
    source_type: str
    sha256: str
    text: str


class ContextBundle(BaseModel):
    task: str
    voice: VoiceSnapshot
    constraints: list[ContextAtomOut]
    atoms: list[ContextAtomOut]
    full_corpus: list[CorpusDocOut]
    completeness: dict[str, int]
    trust: str = "untrusted"


def _to_out(atom: Atom, score: float | None = None) -> ContextAtomOut:
    stale = atom.stale_after is not None and atom.stale_after < datetime.now(UTC)
    base = AtomOut.model_validate(atom)
    return ContextAtomOut(**base.model_dump(), stale=stale, score=score)


def _voice_snapshot(session: Session) -> VoiceSnapshot:
    def texts(atom_type: str, limit: int) -> list[str]:
        return list(
            session.scalars(
                select(Atom.text)
                .where(Atom.atom_type == atom_type, Atom.status != "deprecated")
                .order_by(Atom.impact.desc().nulls_last(), Atom.confidence.desc().nulls_last())
                .limit(limit)
            )
        )

    return VoiceSnapshot(
        tone=texts("voice_constraint", 5),
        audience=None,  # derived properly by the M2 voice profile
        do_phrases=texts("quote", 5),
        avoid_phrases=texts("claims_blacklist", 10),
    )


@router.post("/context", response_model=ContextBundle)
def context(client_id: uuid.UUID, body: ContextRequest, request: Request) -> ContextBundle:
    try:
        [query_vec] = get_embedding_provider().embed([body.task], input_type="query")
    except Exception:
        # Embedding outage (e.g. rate limit): degrade to keyword-only retrieval.
        query_vec = None
    settings = request.app.state.settings
    storage = request.app.state.storage

    with tenant_session(request.app.state.engine, client_id) as session:
        voice = _voice_snapshot(session)

        constraints = [
            _to_out(atom)
            for atom in session.scalars(
                select(Atom)
                .where(Atom.atom_type.in_(CONSTRAINT_TYPES), Atom.status != "deprecated")
                .order_by(Atom.impact.desc().nulls_last())
                .limit(50)
            )
        ]

        hits = hybrid_search(session, body.task, query_vec, limit=body.limit)
        hits.sort(key=lambda h: (h.atom.status != "confirmed", -h.score))
        atoms = [_to_out(h.atom, h.score) for h in hits]

        docs = list(session.scalars(select(Document).where(Document.cleaned_path.isnot(None))))
        full_corpus: list[CorpusDocOut] = []
        texts = {d.id: storage.get(d.cleaned_path).decode("utf-8", "replace") for d in docs}
        if texts and sum(len(t) for t in texts.values()) <= settings.context_full_corpus_max_chars:
            full_corpus = [
                CorpusDocOut(
                    document_id=d.id, source_type=d.source_type, sha256=d.sha256,
                    text=texts[d.id],
                )
                for d in docs
            ]

        completeness = {
            "documents": session.scalar(select(func.count(Document.id))) or 0,
            "atoms": session.scalar(select(func.count(Atom.id))) or 0,
        }

    return ContextBundle(
        task=body.task,
        voice=voice,
        constraints=constraints,
        atoms=atoms,
        full_corpus=full_corpus,
        completeness=completeness,
    )
