"""In-process pipeline worker over a DB-backed jobs table (no Redis/Celery).

Dequeue runs as `engine_worker` — a role with an explicit cross-tenant RLS
policy on jobs only (migration 0003). The pipeline itself always runs through
tenant-scoped sessions. M1 retry policy: one attempt; failures are recorded on
the job and the document and are re-runnable via /reprocess.
"""

import asyncio
import logging

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from content_engine.db import tenant_session
from content_engine.models import Document, Job
from content_engine.pipeline.runner import run_full_pipeline
from content_engine.pipeline.voice_profile import build_voice_profile
from content_engine.storage import RawStorage

logger = logging.getLogger(__name__)


def claim_and_run_next(worker_engine: Engine, app_engine: Engine, storage: RawStorage) -> bool:
    """Claim one queued job (FOR UPDATE SKIP LOCKED) and run it. Returns
    whether a job was processed."""
    with Session(worker_engine) as session, session.begin():
        job = session.scalars(
            select(Job)
            .where(Job.status == "queued")
            .order_by(Job.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        ).one_or_none()
        if job is None:
            return False
        job.status = "running"
        job.attempts += 1
        job_id, client_id, document_id, kind = job.id, job.client_id, job.document_id, job.kind

    error: str | None = None
    try:
        if kind == "build_voice_profile":
            build_voice_profile(app_engine, client_id)
        else:
            run_full_pipeline(app_engine, storage, client_id, document_id)
    except Exception as exc:  # recorded, never swallowed silently
        logger.exception("job %s failed", job_id)
        error = f"{type(exc).__name__}: {exc}"[:500]

    with Session(worker_engine) as session, session.begin():
        job = session.get(Job, job_id)
        job.status = "failed" if error else "done"
        job.error = error
    if error and document_id is not None:
        with tenant_session(app_engine, client_id) as session:
            doc = session.get(Document, document_id)
            if doc is not None:
                doc.status = "failed"
    return True


async def worker_loop(worker_engine: Engine, app_engine: Engine, storage: RawStorage,
                      poll_interval: float) -> None:
    while True:
        try:
            processed = await asyncio.to_thread(
                claim_and_run_next, worker_engine, app_engine, storage
            )
        except Exception:  # e.g. DB briefly unavailable — stay alive
            logger.warning("worker poll failed; retrying", exc_info=True)
            processed = False
        if not processed:
            await asyncio.sleep(poll_interval)
