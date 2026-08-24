import asyncio

from app.workers.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.db.models import Job, TaskRun, JobStatus
from app.scheduler.dag import topological_order, CycleError
from sqlalchemy import select


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def run_workflow_job(self, job_id: str):
    asyncio.run(_run_workflow_job_async(job_id))


async def _run_workflow_job_async(job_id: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            return

        job.status = JobStatus.RUNNING
        await db.commit()

        workflow = job.workflow
        try:
            order = topological_order(workflow.definition)
        except CycleError:
            job.status = JobStatus.FAILED
            await db.commit()
            return

        for task_name in order:
            task_run = TaskRun(job_id=job.id, task_name=task_name, status=JobStatus.RUNNING)
            db.add(task_run)
            await db.commit()

            success = await _execute_task(task_name)

            task_run.status = JobStatus.DONE if success else JobStatus.FAILED
            await db.commit()

            if not success:
                job.status = JobStatus.FAILED
                await db.commit()
                return

        job.status = JobStatus.DONE
        await db.commit()


async def _execute_task(task_name: str) -> bool:
    # Placeholder — replace with real task execution (calling a script, an API, etc.)
    await asyncio.sleep(1)
    return True