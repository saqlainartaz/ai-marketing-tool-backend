"""Operator review workflow (M1C): confirm / override / deprecate atoms.

The epistemic ladder (openmelon pattern): extraction yields provisional atoms;
a human decision promotes (confirm), corrects (override — edits + confirms),
or suppresses (deprecate) them. Every action lands in the append-only
decisions log with a reason, and survives reprocessing via content hashes.
"""

import hashlib
import uuid
from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, model_validator

from content_engine.api.schemas import AtomOut
from content_engine.auth import require_service_token
from content_engine.db import tenant_session
from content_engine.models import Atom, Decision
from content_engine.providers import get_embedding_provider

router = APIRouter(
    prefix="/v1/clients/{client_id}",
    tags=["review"],
    dependencies=[Depends(require_service_token)],
)


class DecisionRequest(BaseModel):
    decision: Literal["confirm", "override", "deprecate"]
    reason: str
    actor: str = "operator"
    text: str | None = None
    payload: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _override_needs_changes(self) -> "DecisionRequest":
        if self.decision == "override" and self.text is None and self.payload is None:
            raise ValueError("override requires new text and/or payload")
        if self.decision != "override" and (self.text is not None or self.payload is not None):
            raise ValueError("text/payload are only valid with decision=override")
        return self


class DecisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    atom_id: uuid.UUID
    atom_content_hash: str
    decision: str
    reason: str
    actor: str
    created_at: datetime


@router.post("/atoms/{atom_id}/decision", response_model=AtomOut)
def decide(
    client_id: uuid.UUID, atom_id: uuid.UUID, body: DecisionRequest, request: Request
) -> Atom:
    with tenant_session(request.app.state.engine, client_id) as session:
        atom = session.get(Atom, atom_id)
        if atom is None:  # RLS makes cross-tenant atoms invisible → 404
            raise HTTPException(status_code=404, detail="Atom not found")

        if body.decision == "confirm":
            atom.status = "confirmed"
        elif body.decision == "deprecate":
            atom.status = "deprecated"
        else:  # override: edit, re-hash, re-embed, confirm
            if body.text is not None:
                atom.text = body.text
                atom.content_hash = hashlib.sha256(
                    f"{atom.atom_type}\x00{atom.text}".encode()
                ).hexdigest()
                [atom.embedding] = get_embedding_provider().embed([atom.text])
            if body.payload is not None:
                atom.payload = body.payload
            atom.status = "confirmed"

        session.add(
            Decision(
                client_id=client_id,
                atom_id=atom.id,
                atom_content_hash=atom.content_hash,
                decision=body.decision,
                reason=body.reason,
                actor=body.actor,
            )
        )
        session.flush()
        session.expunge(atom)
        return atom


@router.get("/decisions", response_model=list[DecisionOut])
def list_decisions(client_id: uuid.UUID, request: Request) -> list[Decision]:
    from sqlalchemy import select

    with tenant_session(request.app.state.engine, client_id) as session:
        rows = session.scalars(
            select(Decision).order_by(Decision.created_at.desc()).limit(200)
        ).all()
        session.expunge_all()
        return list(rows)
