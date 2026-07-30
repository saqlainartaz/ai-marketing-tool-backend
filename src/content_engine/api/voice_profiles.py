"""Voice-profile endpoints (M2): build (async via worker), fetch, list
versions, approve."""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from content_engine.auth import require_service_token
from content_engine.db import tenant_session
from content_engine.models import Atom, Job, VoiceProfile

router = APIRouter(
    prefix="/v1/clients/{client_id}/voice-profile",
    tags=["voice-profile"],
    dependencies=[Depends(require_service_token)],
)


class VoiceProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    version: int
    status: str
    payload: dict[str, Any]
    corpus: dict[str, Any]
    diff: dict[str, Any]
    built_by: str
    created_at: datetime


class VoiceProfileSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version: int
    status: str
    corpus: dict[str, Any]
    diff: dict[str, Any]
    built_by: str
    created_at: datetime


@router.post("", status_code=202)
def build(client_id: uuid.UUID, request: Request) -> dict[str, str]:
    """Queue a profile build. The worker computes it (LLM builds take a minute
    or two); poll GET until the new version appears."""
    with tenant_session(request.app.state.engine, client_id) as session:
        if session.scalars(select(Atom.id).limit(1)).one_or_none() is None:
            raise HTTPException(status_code=409, detail="No atoms yet — ingest documents first")
        session.add(Job(client_id=client_id, document_id=None, kind="build_voice_profile"))
    return {"status": "queued"}


@router.get("", response_model=VoiceProfileOut)
def get_latest(
    client_id: uuid.UUID,
    request: Request,
    version: int | None = Query(default=None, ge=1),
) -> VoiceProfile:
    with tenant_session(request.app.state.engine, client_id) as session:
        stmt = select(VoiceProfile).order_by(VoiceProfile.version.desc()).limit(1)
        if version is not None:
            stmt = select(VoiceProfile).where(VoiceProfile.version == version)
        profile = session.scalars(stmt).one_or_none()
        if profile is None:
            raise HTTPException(status_code=404, detail="No voice profile yet")
        session.expunge(profile)
        return profile


@router.get("/versions", response_model=list[VoiceProfileSummaryOut])
def list_versions(client_id: uuid.UUID, request: Request) -> list[VoiceProfile]:
    with tenant_session(request.app.state.engine, client_id) as session:
        rows = session.scalars(
            select(VoiceProfile).order_by(VoiceProfile.version.desc())
        ).all()
        session.expunge_all()
        return list(rows)


@router.post("/{version}/approve", response_model=VoiceProfileOut)
def approve(client_id: uuid.UUID, version: int, request: Request) -> VoiceProfile:
    with tenant_session(request.app.state.engine, client_id) as session:
        profile = session.scalars(
            select(VoiceProfile).where(VoiceProfile.version == version)
        ).one_or_none()
        if profile is None:
            raise HTTPException(status_code=404, detail="Version not found")
        profile.status = "approved"
        session.flush()
        session.expunge(profile)
        return profile
