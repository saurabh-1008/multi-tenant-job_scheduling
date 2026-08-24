import uuid
from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import DbSession, CurrentTenant
from app.db.models import Job, JobStatus
from app.workers.tasks import run_workflow_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/workflows/{workflow_id}/run", status_code=202)
async def trigger_job(
    workflow_id: uuid.UUID,
    db: DbSession,
    tenant_id: CurrentTenant,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if idempotency_key:
        existing = await db.execute(select(Job).where(Job.idempotency_key == idempotency_key))
        existing_job = existing.scalar_one_or_none()
        if existing_job:
            # Same request retried — return the original job, don't create a duplicate
            return {"id": str(existing_job.id), "status": existing_job.status}

    job = Job(workflow_id=workflow_id, status=JobStatus.PENDING, idempotency_key=idempotency_key)
    db.add(job)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate idempotency key")
    await db.refresh(job)

    # Hand off to a worker instead of running inline — this is why we need Celery/ARQ
    run_workflow_job.delay(str(job.id))

    return {"id": str(job.id), "status": job.status}


@router.get("/{job_id}")
async def get_job_status(job_id: uuid.UUID, db: DbSession):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"id": str(job.id), "status": job.status}