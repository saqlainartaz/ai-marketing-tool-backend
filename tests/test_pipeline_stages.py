"""Parse+clean stage runner: statuses, lineage, immutability (Issue 4).

Requires `docker compose up -d`.
"""

import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from content_engine.db import tenant_session
from content_engine.models import Client, Document, LineageRecord
from content_engine.pipeline.runner import run_parse_and_clean
from content_engine.storage import LocalDiskStorage, content_address

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def env(migrated_db, admin_engine, tmp_path: Path):
    engine = create_engine(migrated_db)
    storage = LocalDiskStorage(str(tmp_path / "raw"))
    with Session(admin_engine) as s, s.begin():
        client = Client(name="Pipeline Inc")
        s.add(client)
        s.flush()
        client_id = client.id
    yield engine, storage, client_id
    engine.dispose()


def _upload_fixture(engine, storage, client_id: uuid.UUID, source_type: str) -> uuid.UUID:
    data = (FIXTURES / "transcript_raw.txt").read_bytes()
    sha = content_address(data)
    raw_path = storage.put(client_id, sha, data)
    with tenant_session(engine, client_id) as s:
        doc = Document(
            client_id=client_id,
            source_type=source_type,
            sha256=sha,
            raw_path=raw_path,
        )
        s.add(doc)
        s.flush()
        return doc.id


def test_stages_progress_status_and_write_lineage(env) -> None:
    engine, storage, client_id = env
    doc_id = _upload_fixture(engine, storage, client_id, "sales_call_transcript")

    run_parse_and_clean(engine, storage, client_id, doc_id)

    with tenant_session(engine, client_id) as s:
        doc = s.get(Document, doc_id)
        assert doc.status == "cleaned"
        assert doc.cleaned_path is not None
        cleaned = storage.get(doc.cleaned_path).decode("utf-8")
        golden = (FIXTURES / "transcript_cleaned.golden.txt").read_text(encoding="utf-8")
        assert cleaned == golden

        stages = {
            record.stage: record
            for record in s.scalars(
                select(LineageRecord).where(LineageRecord.document_id == doc_id)
            )
        }
        assert set(stages) == {"parse", "clean"}
        assert stages["parse"].source_sha == doc.sha256
        assert stages["clean"].actor.startswith("transcript-cleaner/")


def test_raw_file_is_untouched_by_cleaning(env) -> None:
    engine, storage, client_id = env
    original = (FIXTURES / "transcript_raw.txt").read_bytes()
    doc_id = _upload_fixture(engine, storage, client_id, "sales_call_transcript")

    run_parse_and_clean(engine, storage, client_id, doc_id)

    with tenant_session(engine, client_id) as s:
        doc = s.get(Document, doc_id)
        assert storage.get(doc.raw_path) == original


def test_brand_docs_pass_through_uncleaned(env) -> None:
    engine, storage, client_id = env
    doc_id = _upload_fixture(engine, storage, client_id, "brand_doc")

    run_parse_and_clean(engine, storage, client_id, doc_id)

    with tenant_session(engine, client_id) as s:
        doc = s.get(Document, doc_id)
        assert doc.status == "cleaned"
        cleaned = storage.get(doc.cleaned_path)
        assert cleaned == (FIXTURES / "transcript_raw.txt").read_bytes()


def test_rerunning_stages_is_idempotent(env) -> None:
    engine, storage, client_id = env
    doc_id = _upload_fixture(engine, storage, client_id, "sales_call_transcript")

    run_parse_and_clean(engine, storage, client_id, doc_id)
    first = None
    with tenant_session(engine, client_id) as s:
        first = storage.get(s.get(Document, doc_id).cleaned_path)

    run_parse_and_clean(engine, storage, client_id, doc_id)
    with tenant_session(engine, client_id) as s:
        doc = s.get(Document, doc_id)
        assert storage.get(doc.cleaned_path) == first
        assert doc.status == "cleaned"
