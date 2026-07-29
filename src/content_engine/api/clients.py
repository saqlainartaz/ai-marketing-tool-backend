from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from content_engine.api.schemas import ClientCreate, ClientOut
from content_engine.auth import require_service_token
from content_engine.models import Client

router = APIRouter(
    prefix="/v1/clients",
    tags=["clients"],
    dependencies=[Depends(require_service_token)],
)


@router.post("", response_model=ClientOut, status_code=201)
def create_client(body: ClientCreate, request: Request) -> Client:
    with Session(request.app.state.engine) as session, session.begin():
        client = Client(name=body.name)
        session.add(client)
        session.flush()
        session.expunge(client)
        return client


@router.get("", response_model=list[ClientOut])
def list_clients(request: Request) -> list[Client]:
    with Session(request.app.state.engine) as session:
        clients = session.scalars(select(Client).order_by(Client.created_at)).all()
        session.expunge_all()
        return list(clients)
