import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select

from content_engine.api.schemas import AtomOut
from content_engine.auth import require_service_token
from content_engine.db import tenant_session
from content_engine.models import Atom

router = APIRouter(
    prefix="/v1/clients/{client_id}/atoms",
    tags=["atoms"],
    dependencies=[Depends(require_service_token)],
)


@router.get("", response_model=list[AtomOut])
def list_atoms(
    client_id: uuid.UUID,
    request: Request,
    type: str | None = Query(default=None),  # noqa: A002 - API surface
    limit: int = Query(default=100, le=500),
) -> list[Atom]:
    with tenant_session(request.app.state.engine, client_id) as session:
        query = select(Atom).order_by(Atom.created_at).limit(limit)
        if type is not None:
            query = query.where(Atom.atom_type == type)
        atoms = session.scalars(query).all()
        session.expunge_all()
        return list(atoms)
