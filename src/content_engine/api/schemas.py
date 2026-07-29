import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

SourceType = Literal[
    "sales_call_transcript",
    "meeting_transcript",
    "onboarding_form",
    "brand_doc",
    "other",
]

SourceAuthority = Literal[
    "AUTHORITATIVE",  # 1.0 — published style guides, leadership-approved
    "OPERATIONAL",  # 0.8 — templates/playbooks in active use
    "CONVERSATIONAL",  # 0.6 — call transcripts, meeting notes
    "CONTEXTUAL",  # 0.3 — design files, competitor analysis
    "STALE",  # 0.1 — superseded/deprecated
]


class ClientCreate(BaseModel):
    name: str


class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    status: str
    created_at: datetime


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    source_type: str
    source_authority: str
    sha256: str
    status: str
    pipeline_version: int
    created_at: datetime


class AtomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    document_id: uuid.UUID
    atom_type: str
    text: str
    payload: dict
    provenance: dict
    confidence: float | None
    impact: int | None
    evidence_kind: str
    status: str
    content_hash: str
    created_at: datetime
    # Retrieved source-derived text is untrusted input for any LLM consumer
    # (prompt-injection hygiene — docs/AI_CODING_RULES.md).
    trust: Literal["untrusted"] = "untrusted"
