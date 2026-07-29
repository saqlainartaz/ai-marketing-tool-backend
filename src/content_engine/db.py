import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, text
from sqlalchemy.orm import Session


@contextmanager
def tenant_session(engine: Engine, client_id: uuid.UUID) -> Iterator[Session]:
    """Session scoped to one tenant for the duration of one transaction.

    Sets the `app.client_id` GUC with SET LOCAL semantics; every RLS policy
    keys on it. When it is unset, policies match nothing (fail-closed).
    """
    with Session(engine) as session, session.begin():
        session.execute(
            text("SELECT set_config('app.client_id', :cid, true)"),
            {"cid": str(client_id)},
        )
        yield session
