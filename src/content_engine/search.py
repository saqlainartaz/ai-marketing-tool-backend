"""Hybrid retrieval: pgvector cosine + Postgres full-text, fused with
Reciprocal Rank Fusion.

Both legs run inside the same tenant-scoped session, so RLS applies to each
individually — fusion happens after isolation, never instead of it
(PharosRAG lesson: push the ACL below retrieval, don't filter after fusion).
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from content_engine.models import Atom

RRF_K = 60  # standard damping constant
LEG_LIMIT = 50  # candidates per leg before fusion


@dataclass(frozen=True)
class SearchHit:
    atom: Atom
    score: float


def hybrid_search(
    session: Session,
    query_text: str,
    query_embedding: list[float] | None,
    *,
    atom_type: str | None = None,
    limit: int = 20,
) -> list[SearchHit]:
    """query_embedding=None degrades gracefully to keyword-only retrieval
    (embedding provider outage/rate limit must never take search down)."""

    def base(stmt):
        stmt = stmt.where(Atom.status != "deprecated")
        return stmt.where(Atom.atom_type == atom_type) if atom_type else stmt

    legs = []
    if query_embedding is not None:
        legs.append(
            base(
                select(Atom.id)
                .where(Atom.embedding.isnot(None))
                .order_by(Atom.embedding.cosine_distance(query_embedding))
                .limit(LEG_LIMIT)
            )
        )
    tsquery = func.websearch_to_tsquery("english", query_text)
    legs.append(
        base(
            select(Atom.id)
            .where(Atom.tsv.op("@@")(tsquery))
            .order_by(func.ts_rank(Atom.tsv, tsquery).desc())
            .limit(LEG_LIMIT)
        )
    )

    scores: dict[uuid.UUID, float] = {}
    for stmt in legs:
        for rank, atom_id in enumerate(session.scalars(stmt), start=1):
            scores[atom_id] = scores.get(atom_id, 0.0) + 1.0 / (RRF_K + rank)

    if not scores:
        return []
    top = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:limit]
    atoms = {a.id: a for a in session.scalars(select(Atom).where(Atom.id.in_([i for i, _ in top])))}
    return [SearchHit(atom=atoms[i], score=s) for i, s in top if i in atoms]
