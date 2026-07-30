import uuid

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from content_engine.api.schemas import AtomOut
from content_engine.auth import require_service_token
from content_engine.db import tenant_session
from content_engine.providers import get_embedding_provider
from content_engine.search import hybrid_search

router = APIRouter(
    prefix="/v1/clients/{client_id}",
    tags=["search"],
    dependencies=[Depends(require_service_token)],
)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, pattern=r"\S")
    type: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


class SearchHitOut(AtomOut):
    score: float


@router.post("/search", response_model=list[SearchHitOut])
def search(client_id: uuid.UUID, body: SearchRequest, request: Request) -> list[SearchHitOut]:
    try:
        [query_vec] = get_embedding_provider().embed([body.query], input_type="query")
    except Exception:
        # Embedding outage (e.g. rate limit): degrade to keyword-only retrieval.
        query_vec = None

    with tenant_session(request.app.state.engine, client_id) as session:
        hits = hybrid_search(
            session, body.query, query_vec, atom_type=body.type, limit=body.limit
        )
        results = []
        for hit in hits:
            # Belt-and-braces guard: RLS already scopes rows; assert anyway.
            assert hit.atom.client_id == client_id
            atom_out = AtomOut.model_validate(hit.atom)
            results.append(SearchHitOut(**atom_out.model_dump(), score=hit.score))
        return results
