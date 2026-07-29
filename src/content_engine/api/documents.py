import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, UploadFile
from sqlalchemy import select

from content_engine.api.schemas import DocumentOut, SourceAuthority, SourceType
from content_engine.auth import require_service_token
from content_engine.db import tenant_session
from content_engine.models import Document, Job
from content_engine.storage import content_address

router = APIRouter(
    prefix="/v1/clients/{client_id}/documents",
    tags=["documents"],
    dependencies=[Depends(require_service_token)],
)


@router.post("", response_model=DocumentOut)
async def upload_document(
    client_id: uuid.UUID,
    file: UploadFile,
    source_type: Annotated[SourceType, Form()],
    request: Request,
    response: Response,
    source_authority: Annotated[SourceAuthority, Form()] = "CONVERSATIONAL",
) -> Document:
    data = await file.read()
    sha256 = content_address(data)
    engine = request.app.state.engine
    storage = request.app.state.storage

    with tenant_session(engine, client_id) as session:
        existing = session.scalars(
            select(Document).where(Document.sha256 == sha256)
        ).one_or_none()
        if existing is not None:
            # Idempotent re-upload: same bytes → same document, no duplicate.
            response.status_code = 200
            session.expunge(existing)
            return existing

        raw_path = storage.put(client_id, sha256, data)
        doc = Document(
            client_id=client_id,
            source_type=source_type,
            source_authority=source_authority,
            sha256=sha256,
            raw_path=raw_path,
            doc_metadata={"filename": file.filename},
        )
        session.add(doc)
        session.flush()
        session.add(Job(client_id=client_id, document_id=doc.id, kind="process_document"))
        response.status_code = 201
        session.expunge(doc)
        return doc


@router.get("", response_model=list[DocumentOut])
def list_documents(client_id: uuid.UUID, request: Request) -> list[Document]:
    with tenant_session(request.app.state.engine, client_id) as session:
        docs = session.scalars(select(Document).order_by(Document.created_at)).all()
        session.expunge_all()
        return list(docs)


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(client_id: uuid.UUID, document_id: uuid.UUID, request: Request) -> Document:
    with tenant_session(request.app.state.engine, client_id) as session:
        doc = session.get(Document, document_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="Document not found")
        session.expunge(doc)
        return doc
