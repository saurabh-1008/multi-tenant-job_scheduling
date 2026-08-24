from fastapi import APIRouter, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

metrics_router = APIRouter()

JOBS_CREATED = Counter("jobs_created_total", "Total number of jobs created", ["tenant_id"])
JOB_DURATION = Histogram("job_duration_seconds", "Time taken to complete a job")


@metrics_router.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)