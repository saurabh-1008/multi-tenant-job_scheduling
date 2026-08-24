from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import Depends
from sqlalchemy import select

from app.api.deps import DbSession
from app.core.security import create_access_token, create_refresh_token
from app.db.models import Tenant

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(
    db: DbSession,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    # Simplified: in a real system, look up a User row, not Tenant directly.
    result = await db.execute(select(Tenant).where(Tenant.name == form_data.username))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(subject=tenant.name, tenant_id=str(tenant.id))
    refresh_token = create_refresh_token(subject=tenant.name, tenant_id=str(tenant.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }