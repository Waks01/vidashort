from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.schemas.entitlement import CheckRequest, CheckResponse, UnlockRequest, UnlockResponse
from app.services import entitlement as entitlement_service

router = APIRouter()


@router.post("/check", response_model=CheckResponse)
async def check(
    payload: CheckRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await entitlement_service.check(db, user["id"], payload.episode_id)


@router.post("/unlock", response_model=UnlockResponse, responses={403: {"model": dict}})
async def unlock(
    payload: UnlockRequest,
    request: Request,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await rate_limit(user.get("id"), request.client.host if request.client else "0.0.0.0", "entitlement:unlock", limit=10, window_s=60)
    return await entitlement_service.unlock(db, user["id"], payload)