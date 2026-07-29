"""SQLAlchemy models — the M1 schema.

Every tenant-scoped table carries `client_id` and is protected by Postgres RLS
(policies live in the Alembic migration). Provenance is structural: atoms always
point at their source document, location, and lineage.
"""

import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    TIMESTAMP,
    Computed,
    Float,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Voyage embeddings are 1024-dim; the fake embedder must match (docs/DECISIONS.md).
EMBEDDING_DIM = 1024

# M1 atom taxonomy (narrowed — full taxonomy is M1B/M2, enum+prompt change only).
M1_ATOM_TYPES = frozenset(
    {
        "tldr",
        "insight",
        "pain_point",
        "objection",
        "proof_point",
        "quote",
        "terminology",
        "claims_blacklist",
        "voice_constraint",
    }
)


class Base(DeclarativeBase):
    type_annotation_map = {
        uuid.UUID: UUID(as_uuid=True),
        dict[str, Any]: JSONB,
        datetime: TIMESTAMP(timezone=True),
    }


class Client(Base):
    """Tenant registry. Service-level table — not RLS-scoped (holds no client content)."""

    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str]
    status: Mapped[str] = mapped_column(server_default="active")
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("client_id", "sha256", name="uq_documents_client_sha"),
        Index("ix_documents_client_id", "client_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"))
    # sales_call_transcript | meeting_transcript | onboarding_form | brand_doc | other
    source_type: Mapped[str]
    source_authority: Mapped[str] = mapped_column(server_default="CONVERSATIONAL")
    sha256: Mapped[str]  # content address of the immutable raw file
    raw_path: Mapped[str]
    status: Mapped[str] = mapped_column(server_default="uploaded")
    doc_metadata: Mapped[dict[str, Any]] = mapped_column(server_default=text("'{}'::jsonb"))
    pipeline_version: Mapped[int] = mapped_column(Integer, server_default="1")
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), onupdate=text("now()")
    )


class Atom(Base):
    __tablename__ = "atoms"
    __table_args__ = (
        UniqueConstraint("document_id", "content_hash", name="uq_atoms_doc_content"),
        Index("ix_atoms_client_id", "client_id"),
        Index("ix_atoms_client_type", "client_id", "atom_type"),
        Index("ix_atoms_tsv", "tsv", postgresql_using="gin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"))
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    atom_type: Mapped[str]
    text: Mapped[str]
    payload: Mapped[dict[str, Any]] = mapped_column(server_default=text("'{}'::jsonb"))
    # Structural provenance: location-in-source (section_anchor, breadcrumb,
    # speaker, timestamp) — never optional.
    provenance: Mapped[dict[str, Any]]
    confidence: Mapped[float | None] = mapped_column(Float)
    impact: Mapped[int | None] = mapped_column(Integer)  # 1-5 standalone-viability
    evidence_kind: Mapped[str] = mapped_column(server_default="inferred")
    status: Mapped[str] = mapped_column(server_default="provisional")
    stale_after: Mapped[datetime | None]
    content_hash: Mapped[str]
    pipeline_version: Mapped[int] = mapped_column(Integer, server_default="1")
    embedding: Mapped[Any | None] = mapped_column(Vector(EMBEDDING_DIM))
    tsv: Mapped[Any | None] = mapped_column(
        TSVECTOR, Computed("to_tsvector('english', text)", persisted=True)
    )
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (Index("ix_jobs_status", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"))
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    kind: Mapped[str]  # e.g. "process_document"
    status: Mapped[str] = mapped_column(server_default="queued")
    attempts: Mapped[int] = mapped_column(Integer, server_default="0")
    error: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), onupdate=text("now()")
    )


class LineageRecord(Base):
    """Append-only per-transformation record — full reproducibility of every atom."""

    __tablename__ = "lineage"
    __table_args__ = (Index("ix_lineage_document_id", "document_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"))
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    source_sha: Mapped[str]
    stage: Mapped[str]  # parse | clean | atomise | embed
    actor: Mapped[str]  # cleaner/parser version or model id
    prompt_hash: Mapped[str | None]
    params: Mapped[dict[str, Any]] = mapped_column(server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))


class Decision(Base):
    """Append-only log of confirm/override/deprecate actions on atoms.

    No FK to atoms: decisions must survive atom replacement on reprocess;
    re-linking uses atom_content_hash (M1C).
    """

    __tablename__ = "decisions"
    __table_args__ = (Index("ix_decisions_client_id", "client_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"))
    atom_id: Mapped[uuid.UUID]
    atom_content_hash: Mapped[str]
    decision: Mapped[str]  # confirm | override | deprecate
    reason: Mapped[str]
    actor: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
