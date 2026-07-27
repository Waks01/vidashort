from typing import Annotated, AsyncIterator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_access_token
from app.db.session import get_db, get_redis

# Database dependency
async def get_db_session() -> AsyncIterator[AsyncSession]:
    async for session in get_db():
        yield session


bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return {
            "id": payload["sub"],
            "email": payload.get("email", ""),
            "role": payload.get("role", "viewer"),
            "vip": payload.get("vip", False),
        }
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_creator(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "creator":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Creator access required")
    return user


async def get_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
