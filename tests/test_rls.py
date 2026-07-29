"""Cross-tenant zero-recall regression tests.

These assert that Postgres RLS *alone* blocks leakage: queries here use no
app-layer WHERE filtering at all (PharosRAG acl_regression pattern).
Requires `docker compose up -d`.
"""

import uuid

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from content_engine.db import tenant_session
from content_engine.models import Atom, Client, Document


def _seed_client(admin_engine, name: str) -> uuid.UUID:
    with Session(admin_engine) as s, s.begin():
        client = Client(name=name)
        s.add(client)
        s.flush()
        return client.id


def _add_doc_with_atom(engine, client_id: uuid.UUID, marker: str) -> None:
    with tenant_session(engine, client_id) as s:
        doc = Document(
            client_id=client_id,
            source_type="sales_call_transcript",
            source_authority="CONVERSATIONAL",
            sha256=f"sha-{marker}",
            raw_path=f"/raw/{marker}",
        )
        s.add(doc)
        s.flush()
        s.add(
            Atom(
                client_id=client_id,
                document_id=doc.id,
                atom_type="objection",
                text=f"objection text {marker}",
                provenance={"section_anchor": [0, 1], "speaker": "prospect"},
                evidence_kind="quoted",
                content_hash=f"hash-{marker}",
            )
        )


def test_rls_blocks_cross_tenant_reads(app_engine, admin_engine) -> None:
    client_a = _seed_client(admin_engine, "Client A")
    client_b = _seed_client(admin_engine, "Client B")
    _add_doc_with_atom(app_engine, client_a, f"a-{client_a.hex[:8]}")
    _add_doc_with_atom(app_engine, client_b, f"b-{client_b.hex[:8]}")

    # No app-layer filter: SELECT * — RLS must scope to the session tenant.
    with tenant_session(app_engine, client_b) as s:
        atom_clients = {a.client_id for a in s.scalars(select(Atom)).all()}
        doc_clients = {d.client_id for d in s.scalars(select(Document)).all()}
    assert atom_clients == {client_b}
    assert doc_clients == {client_b}


def test_no_tenant_context_yields_zero_rows(app_engine, admin_engine) -> None:
    client_a = _seed_client(admin_engine, "Client A2")
    _add_doc_with_atom(app_engine, client_a, f"a2-{client_a.hex[:8]}")

    # A session with NO app.client_id set must see nothing (fail-closed).
    with Session(app_engine) as s, s.begin():
        atoms = s.scalars(select(Atom)).all()
    assert atoms == []


def test_rls_blocks_cross_tenant_writes(app_engine, admin_engine) -> None:
    client_a = _seed_client(admin_engine, "Client A3")
    client_b = _seed_client(admin_engine, "Client B3")

    # Writing a row for tenant A while the session is scoped to tenant B
    # must be rejected by the WITH CHECK clause.
    with pytest.raises(ProgrammingError):
        with tenant_session(app_engine, client_b) as s:
            s.add(
                Document(
                    client_id=client_a,
                    source_type="brand_doc",
                    source_authority="OPERATIONAL",
                    sha256="sha-cross-write",
                    raw_path="/raw/cross-write",
                )
            )
            s.flush()


def test_app_role_is_not_superuser(app_engine) -> None:
    # RLS is bypassed entirely by superusers/BYPASSRLS roles; the app role
    # being unprivileged is a precondition for every other test here.
    with Session(app_engine) as s:
        row = s.execute(
            text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")
        ).one()
    assert row.rolsuper is False
    assert row.rolbypassrls is False
