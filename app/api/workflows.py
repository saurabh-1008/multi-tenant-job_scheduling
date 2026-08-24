import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import select

from app.api.deps import DbSession, CurrentTenant
from app.db.models import Workflow

router = APIRouter(prefix="/workflows", tags=["workflows"])


class TaskDefinition(BaseModel):
    name: str
    depends_on: list[str] = []


class WorkflowCreate(BaseModel):
    name: str
    tasks: list[TaskDefinition]

    @field_validator("tasks")
    @classmethod
    def validate_dag(cls, tasks: list[TaskDefinition]) -> list[TaskDefinition]:
        names = {t.name for t in tasks}
        for task in tasks:
            for dep in task.depends_on:
                if dep not in names:
                    raise ValueError(f"Task '{task.name}' depends on unknown task '{dep}'")
        return tasks


@router.post("/", status_code=201)
async def create_workflow(payload: WorkflowCreate, db: DbSession, tenant_id: CurrentTenant):
    workflow = Workflow(
        tenant_id=uuid.UUID(tenant_id),
        name=payload.name,
        definition=payload.model_dump()["tasks"],
    )
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    return {"id": str(workflow.id), "name": workflow.name}


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: uuid.UUID, db: DbSession, tenant_id: CurrentTenant):
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.tenant_id == uuid.UUID(tenant_id))
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"id": str(workflow.id), "name": workflow.name, "definition": workflow.definition}