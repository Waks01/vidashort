from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.schemas.ads import AdCapResponse, AdRecordRequest, AdRecordResponse
from app.services import ads as ad_service

router = APIRouter()


@router.get("/cap", response_model=AdCapResponse)
async def cap(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ad_service.cap(db, user["id"])


@router.post("/record", response_model=AdRecordResponse, responses={429: {"model": dict}})
async def record(
    payload: AdRecordRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ad_service.record(db, user["id"], payload)