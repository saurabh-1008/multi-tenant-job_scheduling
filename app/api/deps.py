from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_tenant_id(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> str:
    """
    Decodes the JWT and returns the tenant_id it was issued for.
    Every route that touches tenant data depends on this — it's the
    single source of truth for "who is making this request."
    """
    try:
        payload = decode_token(token)
        tenant_id: str | None = payload.get("tenant_id")
        if tenant_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return tenant_id
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentTenant = Annotated[str, Depends(get_current_tenant_id)]